/**
 * Cloudflare Workers TypeScript implementation of Greptile MCP Server
 * This provides the same functionality as the Python version but using TypeScript
 */

interface Env {
  GREPTILE_API_KEY: string;
  GITHUB_TOKEN: string;
  GREPTILE_BASE_URL?: string;
}

interface GreptileRepository {
  remote: string;
  repository: string;
  branch: string;
}

interface MCPRequest {
  method: string;
  params: any;
}

interface MCPResponse {
  success: boolean;
  data?: any;
  error?: {
    message: string;
    code?: string;
  };
}

// Simple in-memory session storage
const sessions = new Map<string, any[]>();

function generateSessionId(): string {
  return crypto.randomUUID();
}

function createResponse(data: any, success: boolean = true): MCPResponse {
  return {
    success,
    data: success ? data : undefined,
    error: success ? undefined : { message: String(data) }
  };
}

async function makeGreptileRequest(
  url: string,
  method: string,
  headers: Record<string, string>,
  body?: any
): Promise<any> {
  const response = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }

  return response.json();
}

async function handleIndexRepository(
  params: any,
  env: Env
): Promise<MCPResponse> {
  try {
    const { remote, repository, branch, reload = true, notify = false } = params;
    
    const headers = {
      'Authorization': `Bearer ${env.GREPTILE_API_KEY}`,
      'X-GitHub-Token': env.GITHUB_TOKEN,
      'Content-Type': 'application/json',
    };

    const baseUrl = env.GREPTILE_BASE_URL || 'https://api.greptile.com/v2';
    const url = `${baseUrl}/repositories`;
    
    const payload = {
      remote,
      repository,
      branch,
      reload,
      notify,
    };

    const result = await makeGreptileRequest(url, 'POST', headers, payload);
    return createResponse(result);
  } catch (error) {
    return createResponse(`Error indexing repository: ${error}`, false);
  }
}

async function handleQueryRepository(
  params: any,
  env: Env
): Promise<MCPResponse> {
  try {
    const {
      query,
      repositories,
      session_id,
      stream = false,
      genius = true,
      previous_messages,
    } = params;

    const headers = {
      'Authorization': `Bearer ${env.GREPTILE_API_KEY}`,
      'X-GitHub-Token': env.GITHUB_TOKEN,
      'Content-Type': 'application/json',
    };

    const baseUrl = env.GREPTILE_BASE_URL || 'https://api.greptile.com/v2';
    const url = `${baseUrl}/query`;

    // Session management
    const sid = session_id || generateSessionId();
    
    let messages: any[];
    if (previous_messages) {
      messages = [...previous_messages, { role: 'user', content: query }];
      sessions.set(sid, messages);
    } else {
      const history = sessions.get(sid) || [];
      messages = [...history, { role: 'user', content: query }];
      sessions.set(sid, messages);
    }

    const payload = {
      messages,
      repositories,
      stream: false, // Disable streaming for simplicity
      genius,
      ...(session_id && { sessionId: session_id }),
    };

    const result = await makeGreptileRequest(url, 'POST', headers, payload);
    
    // Update session history
    if (result.messages) {
      sessions.set(sid, result.messages);
    } else if (result.output) {
      const updatedMessages = [...messages, { role: 'assistant', content: result.output }];
      sessions.set(sid, updatedMessages);
    }

    result._session_id = sid;
    return createResponse(result);
  } catch (error) {
    return createResponse(`Error querying repositories: ${error}`, false);
  }
}

async function handleSearchRepository(
  params: any,
  env: Env
): Promise<MCPResponse> {
  try {
    const { query, repositories, session_id, genius = true } = params;

    const headers = {
      'Authorization': `Bearer ${env.GREPTILE_API_KEY}`,
      'X-GitHub-Token': env.GITHUB_TOKEN,
      'Content-Type': 'application/json',
    };

    const baseUrl = env.GREPTILE_BASE_URL || 'https://api.greptile.com/v2';
    const url = `${baseUrl}/search`;

    const messages = [{ role: 'user', content: query }];
    const payload = {
      messages,
      repositories,
      genius,
      ...(session_id && { sessionId: session_id }),
    };

    const result = await makeGreptileRequest(url, 'POST', headers, payload);
    return createResponse(result);
  } catch (error) {
    return createResponse(`Error searching repositories: ${error}`, false);
  }
}

async function handleGetRepositoryInfo(
  params: any,
  env: Env
): Promise<MCPResponse> {
  try {
    const { remote, repository, branch } = params;

    if (!remote || !repository || !branch) {
      return createResponse('Missing required parameters: remote, repository, branch', false);
    }

    const headers = {
      'Authorization': `Bearer ${env.GREPTILE_API_KEY}`,
      'X-GitHub-Token': env.GITHUB_TOKEN,
      'Content-Type': 'application/json',
    };

    const baseUrl = env.GREPTILE_BASE_URL || 'https://api.greptile.com/v2';
    const repositoryId = `${remote}:${branch}:${repository}`;
    const encodedId = encodeURIComponent(repositoryId);
    const url = `${baseUrl}/repositories/${encodedId}`;

    const result = await makeGreptileRequest(url, 'GET', headers);
    return createResponse(result);
  } catch (error) {
    return createResponse(`Error getting repository info: ${error}`, false);
  }
}

async function handleMCPRequest(request: MCPRequest, env: Env): Promise<MCPResponse> {
  const { method, params } = request;

  // Check for required environment variables
  const greptileKey = env.GREPTILE_API_KEY;
  const githubToken = env.GITHUB_TOKEN;
  
  if (!greptileKey || !githubToken) {
    return createResponse(`Missing required environment variables. Greptile key: ${!!greptileKey}, GitHub token: ${!!githubToken}`, false);
  }

  switch (method) {
    case 'index_repository':
      return handleIndexRepository(params, env);
    case 'query_repository':
      return handleQueryRepository(params, env);
    case 'search_repository':
      return handleSearchRepository(params, env);
    case 'get_repository_info':
      return handleGetRepositoryInfo(params, env);
    default:
      return createResponse(`Unknown method: ${method}`, false);
  }
}

function createCORSHeaders(): Record<string, string> {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Max-Age': '86400',
    'Content-Type': 'application/json',
  };
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;

    // Handle CORS preflight
    if (method === 'OPTIONS') {
      return new Response(null, {
        status: 200,
        headers: createCORSHeaders(),
      });
    }

    // Health check endpoint
    if (path === '/' || path === '/health') {
      let status = 'healthy';
      const missingEnv: string[] = [];
      if (!env.GREPTILE_API_KEY) missingEnv.push('GREPTILE_API_KEY');
      if (!env.GITHUB_TOKEN) missingEnv.push('GITHUB_TOKEN');

      if (missingEnv.length > 0) {
        status = 'degraded';
      }

      const healthData = {
        status,
        service: 'greptile-mcp-server',
        version: '1.0.0',
        deployment: 'cloudflare-workers',
        runtime: 'typescript',
        missingEnv: missingEnv.length ? missingEnv : undefined,
        timestamp: new Date().toISOString(),
      };

      return new Response(JSON.stringify(healthData), {
        status: status === 'healthy' ? 200 : 500,
        headers: createCORSHeaders(),
      });
    }

    // Debug endpoint
    if (path === '/debug') {
      const debugData = {
        envKeys: Object.keys(env),
        hasGreptileKey: !!env.GREPTILE_API_KEY,
        hasGithubToken: !!env.GITHUB_TOKEN,
        greptileKeyLength: env.GREPTILE_API_KEY ? env.GREPTILE_API_KEY.length : 0,
        githubTokenLength: env.GITHUB_TOKEN ? env.GITHUB_TOKEN.length : 0,
      };

      return new Response(JSON.stringify(debugData), {
        status: 200,
        headers: createCORSHeaders(),
      });
    }

    // MCP endpoints
    if ((path === '/sse' || path === '/mcp') && method === 'POST') {
      try {
        const requestData: MCPRequest = await request.json();
        const result = await handleMCPRequest(requestData, env);

        return new Response(JSON.stringify(result), {
          status: result.success ? 200 : 400,
          headers: createCORSHeaders(),
        });
      } catch (error) {
        const errorResponse = createResponse(`Invalid request: ${error}`, false);
        return new Response(JSON.stringify(errorResponse), {
          status: 400,
          headers: createCORSHeaders(),
        });
      }
    }

    // Server info for GET requests on MCP endpoints
    if ((path === '/sse' || path === '/mcp') && method === 'GET') {
      const serverInfo = {
        name: 'greptile-mcp-server',
        version: '1.0.0',
        description: 'MCP server for code search and querying with Greptile API',
        transport: ['http', 'sse'],
        deployment: 'cloudflare-workers',
        runtime: 'typescript',
        endpoints: {
          '/': 'Health check',
          '/health': 'Health check',
          '/sse': 'SSE MCP endpoint',
          '/mcp': 'HTTP MCP endpoint',
        },
        tools: [
          'index_repository',
          'query_repository',
          'search_repository',
          'get_repository_info',
        ],
      };

      return new Response(JSON.stringify(serverInfo), {
        status: 200,
        headers: createCORSHeaders(),
      });
    }

    // Unknown endpoint
    const errorResponse = createResponse(`Unknown endpoint: ${path}`, false);
    return new Response(JSON.stringify(errorResponse), {
      status: 404,
      headers: createCORSHeaders(),
    });
  },
};