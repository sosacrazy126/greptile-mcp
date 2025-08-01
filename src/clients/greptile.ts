import type {
  Repository,
  QueryMessage,
  QueryResponse,
  StreamingChunk,
  GreptileError,
  Config,
} from '../types/index.js';
import { retry, safeJsonParse } from '../utils/index.js';

export class GreptileClient {
  private readonly apiKey: string;
  private readonly githubToken: string;
  private readonly baseUrl: string;
  private readonly defaultTimeout: number;
  private readonly headers: Record<string, string>;

  constructor(config: Config) {
    if (!config.apiKey) {
      throw new Error('API key is required');
    }
    if (!config.githubToken) {
      throw new Error('GitHub token is required');
    }

    this.apiKey = config.apiKey;
    this.githubToken = config.githubToken;
    this.baseUrl = config.baseUrl || 'https://api.greptile.com/v2';
    this.defaultTimeout = 60000; // 60 seconds

    this.headers = {
      'Authorization': `Bearer ${this.apiKey}`,
      'X-GitHub-Token': this.githubToken,
      'Content-Type': 'application/json',
      'User-Agent': 'greptile-mcp-server/3.0.0',
    };
  }

  /**
   * Index a repository for code search and querying
   */
  async indexRepository(
    remote: string,
    repository: string,
    branch: string,
    reload: boolean = true,
    notify: boolean = false,
    timeout?: number
  ): Promise<Record<string, unknown>> {
    const url = `${this.baseUrl}/repositories`;
    const payload = {
      remote,
      repository,
      branch,
      reload,
      notify,
    };

    return this.makeRequest('POST', url, payload, timeout);
  }

  /**
   * Query repositories to get an answer with code references
   */
  async queryRepositories(
    messages: QueryMessage[],
    repositories: Repository[],
    sessionId?: string,
    stream: boolean = false,
    genius: boolean = true,
    timeout?: number
  ): Promise<QueryResponse | AsyncIterable<StreamingChunk>> {
    if (stream) {
      return this.streamQueryRepositories(
        messages,
        repositories,
        sessionId,
        genius,
        timeout
      );
    }

    const url = `${this.baseUrl}/query`;
    const payload: Record<string, unknown> = {
      messages,
      stream: false,
      genius,
    };

    if (repositories.length > 0) {
      payload.repositories = repositories;
    }
    if (sessionId) {
      payload.sessionId = sessionId;
    }

    const response = await this.makeRequest('POST', url, payload, timeout);
    return response as QueryResponse;
  }

  /**
   * Stream query repositories with Server-Sent Events
   */
  async *streamQueryRepositories(
    messages: QueryMessage[],
    repositories: Repository[],
    sessionId?: string,
    genius: boolean = true,
    timeout?: number
  ): AsyncIterable<StreamingChunk> {
    const url = `${this.baseUrl}/query`;
    const payload: Record<string, unknown> = {
      messages,
      stream: true,
      genius,
    };

    if (repositories.length > 0) {
      payload.repositories = repositories;
    }
    if (sessionId) {
      payload.sessionId = sessionId;
    }

    const streamHeaders = {
      ...this.headers,
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache',
    };

    const controller = new AbortController();
    const timeoutId = timeout ? setTimeout(() => controller.abort(), timeout) : null;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: streamHeaders,
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw this.createError(`HTTP ${response.status}: ${response.statusText}`, response.status);
      }

      if (!response.body) {
        throw this.createError('No response body for streaming request');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.trim() && line.startsWith('data: ')) {
              const data = line.slice(6);
              const chunk = safeJsonParse(data, null);

              if (chunk) {
                const processedChunk = this.processStreamChunk(chunk);
                if (processedChunk) {
                  yield processedChunk;
                }
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } finally {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    }
  }


  /**
   * Get information about an indexed repository
   */
  async getRepositoryInfo(
    remote: string,
    repository: string,
    branch: string,
    timeout?: number
  ): Promise<Record<string, unknown>> {
    const repositoryId = `${remote}:${branch}:${repository}`;
    const encodedId = encodeURIComponent(repositoryId);
    const url = `${this.baseUrl}/repositories/${encodedId}`;

    return this.makeRequest('GET', url, undefined, timeout);
  }

  /**
   * Make an HTTP request with retry logic and error handling
   */
  private async makeRequest(
    method: string,
    url: string,
    payload?: unknown,
    timeout?: number
  ): Promise<Record<string, unknown>> {
    const requestTimeout = timeout || this.defaultTimeout;

    const makeRequestAttempt = async (): Promise<Record<string, unknown>> => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), requestTimeout);

      try {
        const requestOptions: RequestInit = {
          method,
          headers: this.headers,
          signal: controller.signal,
        };

        if (payload) {
          requestOptions.body = JSON.stringify(payload);
        }

        const response = await fetch(url, requestOptions);

        if (!response.ok) {
          const errorText = await response.text();
          throw this.createError(
            `HTTP ${response.status}: ${response.statusText}\n${errorText}`,
            response.status,
            errorText
          );
        }

        const result = await response.json();
        return result as Record<string, unknown>;
      } finally {
        clearTimeout(timeoutId);
      }
    };

    try {
      return await retry(makeRequestAttempt, {
        maxAttempts: 3,
        baseDelay: 1000,
        maxDelay: 5000,
      });
    } catch (error) {
      if (error instanceof Error) {
        throw this.createError(error.message);
      }
      throw this.createError('Unknown error occurred');
    }
  }

  /**
   * Process streaming chunks into standardized format
   */
  private processStreamChunk(chunk: unknown): StreamingChunk | null {
    if (!chunk || typeof chunk !== 'object') {
      return null;
    }

    const chunkObj = chunk as Record<string, unknown>;
    const timestamp = Date.now();

    if (chunkObj.type === 'text' && typeof chunkObj.content === 'string') {
      return {
        type: 'text',
        content: chunkObj.content,
        timestamp,
      };
    }

    if (chunkObj.type === 'citation') {
      return {
        type: 'citation',
        file: typeof chunkObj.file === 'string' ? chunkObj.file : undefined,
        lines: typeof chunkObj.lines === 'string' ? chunkObj.lines : undefined,
        timestamp,
      };
    }

    if ('sessionId' in chunkObj && typeof chunkObj.sessionId === 'string') {
      return {
        type: 'session',
        sessionId: chunkObj.sessionId,
        timestamp,
      };
    }

    return {
      type: 'other',
      data: chunk,
      timestamp,
    };
  }

  /**
   * Create a standardized error object
   */
  private createError(message: string, statusCode?: number, response?: unknown): GreptileError {
    const error = new Error(message) as GreptileError;
    error.name = 'GreptileError';
    if (statusCode) {
      error.statusCode = statusCode;
    }
    if (response) {
      error.response = response;
    }
    return error;
  }

  /**
   * Health check for the Greptile API
   */
  async healthCheck(): Promise<boolean> {
    try {
      // Create manual timeout controller for better compatibility
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        headers: this.headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        return false;
      }

      const text = await response.text();
      return text.includes('Healthy');
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }
}