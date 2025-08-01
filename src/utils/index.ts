import { randomUUID } from 'crypto';
import type { Config } from '../types/index.js';

/**
 * Generate a new unique session ID in proper UUID format
 */
export function generateSessionId(): string {
  return randomUUID().toLowerCase();
}

/**
 * Normalize a session ID to ensure consistent format
 */
export function normalizeSessionId(sessionId?: string): string | undefined {
  if (!sessionId) return undefined;
  return sessionId.toLowerCase().trim();
}

/**
 * Create an error response in JSON format
 */
export function createErrorResponse(
  message: string,
  type: string = 'Error',
  sessionId?: string
): string {
  const error = {
    error: message,
    type,
    ...(sessionId && { session_id: sessionId }),
  };
  return JSON.stringify(error, null, 2);
}

/**
 * Safe JSON parsing with fallback
 */
export function safeJsonParse<T>(text: string, fallback: T): T {
  try {
    return JSON.parse(text) as T;
  } catch {
    return fallback;
  }
}

/**
 * Validate environment variables and create config
 */
export function validateConfig(overrides: Partial<Config> = {}): Config {
  // Check for GitHub token with fallback priority:
  // 1. Override from arguments
  // 2. GITHUB_AI_TOKEN (preferred)
  // 3. GITHUB_TOKEN (fallback)
  const githubToken = overrides.githubToken || 
                     process.env.GITHUB_AI_TOKEN || 
                     process.env.GITHUB_TOKEN;

  const config: Config = {
    apiKey: process.env.GREPTILE_API_KEY || overrides.apiKey,
    githubToken,
    baseUrl: process.env.GREPTILE_BASE_URL || overrides.baseUrl || 'https://api.greptile.com/v2',
    repositories: overrides.repositories,
    features: {
      streaming: true,
      orchestration: true,
      flowEnhancement: true,
      ...overrides.features,
    },
    plugins: overrides.plugins || [],
  };

  // Validation
  if (!config.apiKey) {
    throw new Error('GREPTILE_API_KEY environment variable or --api-key argument is required');
  }

  if (!config.githubToken) {
    throw new Error('GITHUB_AI_TOKEN or GITHUB_TOKEN environment variable or --github-token argument is required');
  }

  return config;
}

/**
 * Format duration in human-readable format
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  } else if (seconds < 3600) {
    return `${Math.round(seconds / 60)}m`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.round((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
}

/**
 * Truncate string to specified length with ellipsis
 */
export function truncateString(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength - 3) + '...';
}

/**
 * Delay execution for specified milliseconds
 */
export async function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry function with exponential backoff
 */
export async function retry<T>(
  fn: () => Promise<T>,
  options: {
    maxAttempts?: number;
    baseDelay?: number;
    maxDelay?: number;
    backoffFactor?: number;
  } = {}
): Promise<T> {
  const {
    maxAttempts = 3,
    baseDelay = 1000,
    maxDelay = 10000,
    backoffFactor = 2,
  } = options;

  let lastError: Error;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      if (attempt === maxAttempts) {
        throw lastError;
      }

      const delayMs = Math.min(
        baseDelay * Math.pow(backoffFactor, attempt - 1),
        maxDelay
      );
      
      await delay(delayMs);
    }
  }

  throw lastError!;
}

/**
 * Create a timeout promise that rejects after specified milliseconds
 */
export function withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
  const timeoutPromise = new Promise<never>((_, reject) => {
    setTimeout(() => reject(new Error(`Operation timed out after ${timeoutMs}ms`)), timeoutMs);
  });

  return Promise.race([promise, timeoutPromise]);
}

/**
 * Check if a string is a valid URL
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Extract repository info from various URL formats
 */
export function parseRepositoryUrl(url: string): { remote: string; repository: string } | null {
  try {
    const parsedUrl = new URL(url);
    
    // GitHub URLs
    if (parsedUrl.hostname === 'github.com') {
      const pathParts = parsedUrl.pathname.split('/').filter(Boolean);
      if (pathParts.length >= 2) {
        return {
          remote: 'github',
          repository: `${pathParts[0]}/${pathParts[1]}`,
        };
      }
    }
    
    // GitLab URLs
    if (parsedUrl.hostname === 'gitlab.com') {
      const pathParts = parsedUrl.pathname.split('/').filter(Boolean);
      if (pathParts.length >= 2) {
        return {
          remote: 'gitlab',
          repository: `${pathParts[0]}/${pathParts[1]}`,
        };
      }
    }
    
    return null;
  } catch {
    return null;
  }
}