#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ListPromptsRequestSchema,
  ReadResourceRequestSchema,
  GetPromptRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

import { GreptileClient } from './clients/greptile.js';
import {
  validateConfig,
  generateSessionId,
  createErrorResponse,
  checkEnvironmentVariables,
} from './utils/index.js';
import type { Config, EnvironmentStatus } from './types/index.js';

class GreptileMCPServer {
  private server: Server;
  private greptileClient: GreptileClient | null = null;
  private config: Config | null = null;
  private envStatus: EnvironmentStatus;

  constructor() {
    // Check environment variables first
    this.envStatus = checkEnvironmentVariables();

    this.server = new Server(
      {
        name: 'greptile-mcp-server',
        version: '3.0.3',
        description: 'AI-powered code search and querying with Greptile API',
      },
      {
        capabilities: {
          tools: {},
          resources: {},
          prompts: {},
        },
      }
    );

    this.setupHandlers();
  }

  /**
   * Initialize the server with configuration
   */
  async initialize(config: Config): Promise<void> {
    this.config = config;

    // Only initialize Greptile client if environment is fully configured
    if (this.envStatus.isFullyConfigured) {
      try {
        this.greptileClient = new GreptileClient(config);

        // Test API connectivity
        const isHealthy = await this.greptileClient.healthCheck();
        if (!isHealthy) {
          console.warn('Greptile API health check failed - tools may not work correctly');
        }
      } catch (error) {
        console.error('Failed to initialize Greptile client:', error);
        // Don't throw - let server start anyway for diagnostic purposes
        this.greptileClient = null;
      }
    } else {
      console.warn('Greptile MCP server started with incomplete configuration');
      console.warn('Missing environment variables:', this.envStatus.missingVars.join(', '));
      console.warn('Use greptile_env_check tool for setup guidance');
    }
  }

  /**
   * Set up MCP request handlers
   */
  private setupHandlers(): void {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'greptile_help',
          description: 'Get comprehensive help and usage examples for all Greptile MCP tools',
          inputSchema: {
            type: 'object',
            properties: {},
          },
        },
        {
          name: 'greptile_env_check',
          description: 'Check environment variable configuration and setup status',
          inputSchema: {
            type: 'object',
            properties: {},
          },
        },
        {
          name: 'index_repository',
          description: 'Index a repository to make it searchable for future queries',
          inputSchema: {
            type: 'object',
            properties: {
              remote: {
                type: 'string',
                enum: ['github', 'gitlab'],
                description: 'Repository host (github or gitlab)',
              },
              repository: {
                type: 'string',
                description: 'Repository in owner/repo format',
              },
              branch: {
                type: 'string',
                description: 'Branch to index',
              },
              reload: {
                type: 'boolean',
                description: 'Force reprocessing of previously indexed repository',
                default: true,
              },
              notify: {
                type: 'boolean',
                description: 'Send email notification when indexing completes',
                default: false,
              },
            },
            required: ['remote', 'repository', 'branch'],
          },
        },
        {
          name: 'query_repository',
          description:
            'Query repositories using natural language to get detailed answers with code references',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Natural language query about the codebase',
              },
              repositories: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    remote: { type: 'string', enum: ['github', 'gitlab'] },
                    repository: { type: 'string' },
                    branch: { type: 'string' },
                  },
                  required: ['remote', 'repository', 'branch'],
                },
                description: 'List of repositories to query',
              },
              session_id: {
                type: 'string',
                description:
                  'Session ID for conversation continuity (auto-generated if not provided)',
              },
              stream: {
                type: 'boolean',
                description: 'Enable streaming response',
                default: false,
              },
              genius: {
                type: 'boolean',
                description: 'Use enhanced query capabilities',
                default: true,
              },
              timeout: {
                type: 'number',
                description: 'Request timeout in milliseconds',
                default: 60000,
              },
              previous_messages: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    role: { type: 'string', enum: ['user', 'assistant'] },
                    content: { type: 'string' },
                  },
                  required: ['role', 'content'],
                },
                description: 'Previous conversation messages for context',
              },
            },
            required: ['query'],
          },
        },
        {
          name: 'get_repository_info',
          description: 'Get information about an indexed repository including status and metadata',
          inputSchema: {
            type: 'object',
            properties: {
              remote: {
                type: 'string',
                enum: ['github', 'gitlab'],
                description: 'Repository host',
              },
              repository: {
                type: 'string',
                description: 'Repository in owner/repo format',
              },
              branch: {
                type: 'string',
                description: 'Branch that was indexed',
              },
            },
            required: ['remote', 'repository', 'branch'],
          },
        },
      ],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async request => {
      try {
        switch (request.params.name) {
          case 'greptile_help':
            return await this.handleGreptileHelp();

          case 'greptile_env_check':
            return await this.handleEnvironmentCheck();

          case 'index_repository':
            return await this.handleIndexRepository(request.params.arguments);

          case 'query_repository':
            return await this.handleQueryRepository(request.params.arguments);

          case 'get_repository_info':
            return await this.handleGetRepositoryInfo(request.params.arguments);

          default:
            return {
              content: [
                {
                  type: 'text',
                  text: createErrorResponse(`Unknown tool: ${request.params.name}`),
                },
              ],
            };
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        return {
          content: [
            {
              type: 'text',
              text: createErrorResponse(`Tool execution failed: ${errorMessage}`),
            },
          ],
        };
      }
    });

    // List available resources
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => ({
      resources: [
        {
          uri: 'greptile://help',
          mimeType: 'text/markdown',
          name: 'Greptile MCP Help',
          description: 'Comprehensive documentation for all Greptile MCP features',
        },
        {
          uri: 'greptile://config',
          mimeType: 'application/json',
          name: 'Current Configuration',
          description: 'Current server configuration and settings',
        },
      ],
    }));

    // Handle resource reads
    this.server.setRequestHandler(ReadResourceRequestSchema, async request => {
      const { uri } = request.params;

      if (uri === 'greptile://help') {
        return {
          contents: [
            {
              uri,
              mimeType: 'text/markdown',
              text: await this.getHelpContent(),
            },
          ],
        };
      }

      if (uri === 'greptile://config') {
        return {
          contents: [
            {
              uri,
              mimeType: 'application/json',
              text: JSON.stringify(this.config, null, 2),
            },
          ],
        };
      }

      throw new Error(`Unknown resource: ${uri}`);
    });

    // List available prompts
    this.server.setRequestHandler(ListPromptsRequestSchema, async () => ({
      prompts: [
        {
          name: 'codebase_exploration',
          description: 'Start exploring a codebase with guided questions',
          arguments: [
            {
              name: 'repository',
              description: 'Repository to explore (owner/repo)',
              required: true,
            },
            {
              name: 'focus_area',
              description: 'Specific area to focus on (architecture, authentication, etc.)',
              required: false,
            },
          ],
        },
      ],
    }));

    // Handle prompt requests
    this.server.setRequestHandler(GetPromptRequestSchema, async request => {
      if (request.params.name === 'codebase_exploration') {
        const repository = request.params.arguments?.repository as string;
        const focusArea = request.params.arguments?.focus_area as string;

        return {
          description: 'Guided codebase exploration prompt',
          messages: [
            {
              role: 'user',
              content: {
                type: 'text',
                text: this.generateExplorationPrompt(repository, focusArea),
              },
            },
          ],
        };
      }

      throw new Error(`Unknown prompt: ${request.params.name}`);
    });
  }

  /**
   * Handle greptile_help tool
   */
  private async handleGreptileHelp(): Promise<{ content: Array<{ type: string; text: string }> }> {
    return {
      content: [
        {
          type: 'text',
          text: await this.getHelpContent(),
        },
      ],
    };
  }

  /**
   * Handle greptile_env_check tool
   */
  private async handleEnvironmentCheck(): Promise<{
    content: Array<{ type: string; text: string }>;
  }> {
    const status = this.envStatus;

    const report = {
      status: status.isFullyConfigured ? 'CONFIGURED' : 'INCOMPLETE',
      environment_variables: {
        GREPTILE_API_KEY: status.hasGreptileApiKey ? 'SET' : 'MISSING',
        GITHUB_TOKEN: status.hasGithubToken ? 'SET' : 'MISSING',
      },
      api_connectivity: null as string | null,
      missing_variables: status.missingVars,
      setup_instructions: status.suggestions,
    };

    if (this.greptileClient) {
      try {
        const healthCheck = await this.greptileClient.healthCheck();
        report.api_connectivity = healthCheck ? 'CONNECTED' : 'FAILED';
      } catch (error) {
        report.api_connectivity = 'ERROR: ' + (error as Error).message;
      }
    } else {
      report.api_connectivity = 'NOT_INITIALIZED';
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(report, null, 2),
        },
      ],
    };
  }

  /**
   * Handle index_repository tool
   */
  private async handleIndexRepository(
    args: unknown
  ): Promise<{ content: Array<{ type: string; text: string }> }> {
    if (!this.greptileClient) {
      return {
        content: [
          {
            type: 'text',
            text: createErrorResponse(
              'Cannot index repository: Missing environment variables. Use greptile_env_check for setup guidance.',
              'Configuration Error',
              undefined
            ),
          },
        ],
      };
    }

    const { remote, repository, branch, reload = true, notify = false } = args as any;

    const result = await this.greptileClient.indexRepository(
      remote,
      repository,
      branch,
      reload,
      notify
    );

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  /**
   * Handle query_repository tool
   */
  private async handleQueryRepository(
    args: unknown
  ): Promise<{ content: Array<{ type: string; text: string }> }> {
    if (!this.greptileClient) {
      return {
        content: [
          {
            type: 'text',
            text: createErrorResponse(
              'Cannot query repository: Missing environment variables. Use greptile_env_check for setup guidance.',
              'Configuration Error',
              undefined
            ),
          },
        ],
      };
    }

    const {
      query,
      repositories = [],
      session_id,
      stream = false,
      genius = true,
      timeout,
      previous_messages = [],
    } = args as any;

    // Generate session ID if not provided
    const sessionId = session_id || generateSessionId();

    // Prepare messages array
    const messages = [...previous_messages, { role: 'user' as const, content: query }];

    if (stream) {
      // Handle streaming response
      const streamResults: string[] = [];
      const streamingResponse = await this.greptileClient.queryRepositories(
        messages,
        repositories,
        sessionId,
        true,
        genius,
        timeout
      );

      for await (const chunk of streamingResponse as AsyncIterable<any>) {
        if (chunk.type === 'text' && chunk.content) {
          streamResults.push(chunk.content);
        }
      }

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              {
                message: streamResults.join(''),
                session_id: sessionId,
                streamed: true,
              },
              null,
              2
            ),
          },
        ],
      };
    } else {
      // Handle regular response
      const result = await this.greptileClient.queryRepositories(
        messages,
        repositories,
        sessionId,
        false,
        genius,
        timeout
      );

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({ ...result, session_id: sessionId }, null, 2),
          },
        ],
      };
    }
  }

  /**
   * Handle get_repository_info tool
   */
  private async handleGetRepositoryInfo(
    args: unknown
  ): Promise<{ content: Array<{ type: string; text: string }> }> {
    if (!this.greptileClient) {
      return {
        content: [
          {
            type: 'text',
            text: createErrorResponse(
              'Cannot get repository info: Missing environment variables. Use greptile_env_check for setup guidance.',
              'Configuration Error',
              undefined
            ),
          },
        ],
      };
    }

    const { remote, repository, branch } = args as any;

    const result = await this.greptileClient.getRepositoryInfo(remote, repository, branch);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  /**
   * Get comprehensive help content
   */
  private async getHelpContent(): Promise<string> {
    return `# 🚀 Greptile MCP Server - Comprehensive Guide

## Overview
The Greptile MCP Server provides AI-powered code search and querying capabilities through the Model Context Protocol (MCP). It integrates with the Greptile API to index repositories and answer natural language questions about codebases.

## Available Tools

### 1. \`greptile_help\`
Get this comprehensive help documentation.

**Usage:** No parameters required

### 2. \`index_repository\`
Index a repository to make it searchable for future queries.

**Parameters:**
- \`remote\`: "github" or "gitlab"
- \`repository\`: Repository in "owner/repo" format
- \`branch\`: Branch to index
- \`reload\`: Force reprocessing (optional, default: true)
- \`notify\`: Email notification (optional, default: false)

**Example:**
\`\`\`json
{
  "remote": "github",
  "repository": "microsoft/vscode",
  "branch": "main",
  "reload": true
}
\`\`\`

### 3. \`query_repository\`
Query repositories using natural language to get detailed answers with code references.

**Parameters:**
- \`query\`: Natural language question
- \`repositories\`: Array of repository objects (optional if session exists)
- \`session_id\`: For conversation continuity (auto-generated if not provided)
- \`stream\`: Enable streaming response (optional, default: false)
- \`genius\`: Enhanced capabilities (optional, default: true)
- \`previous_messages\`: Conversation history (optional)

**Example:**
\`\`\`json
{
  "query": "How is authentication implemented in this codebase?",
  "repositories": [
    {
      "remote": "github",
      "repository": "microsoft/vscode",
      "branch": "main"
    }
  ],
  "stream": false
}
\`\`\`

### 4. \`get_repository_info\`
Get information about an indexed repository.

**Parameters:**
- \`remote\`: Repository host
- \`repository\`: Repository identifier
- \`branch\`: Branch name

## Best Practices

### Session Management
- Use consistent \`session_id\` across related queries for better context
- Auto-generated session IDs are provided if not specified
- Session continuity improves answer quality over multiple interactions

### Repository Workflow
1. **Index** repositories first using \`index_repository\`
2. **Verify** indexing status with \`get_repository_info\`
3. **Query** using natural language with \`query_repository\`

### Query Optimization
- Be specific in your questions for better results
- Use technical terms relevant to the codebase
- Reference specific features, patterns, or components
- Build on previous queries using session continuity

## Example Workflows

### Getting Started with a New Codebase
\`\`\`
1. Index the repository
2. Ask: "What is the overall architecture of this codebase?"
3. Follow up: "How are the main components organized?"
4. Dive deeper: "How does the authentication system work?"
\`\`\`

### Debugging a Specific Issue
\`\`\`
1. Ask: "How is error handling implemented?"
2. Query: "What are the common error patterns in this codebase?"
3. Follow up: "Show me specific examples of error handling code"
\`\`\`

### Understanding Design Patterns
\`\`\`
1. Query: "What design patterns are used in this codebase?"
2. Follow up: "How is the observer pattern implemented?"
3. Query: "Show me specific implementations of this pattern"
\`\`\`

## Configuration

Required environment variables:
- \`GREPTILE_API_KEY\`: Your Greptile API key
- \`GITHUB_TOKEN\`: GitHub personal access token

Optional:
- \`GREPTILE_BASE_URL\`: Custom API base URL (default: https://api.greptile.com/v2)

## Resources

- **greptile://help**: This documentation
- **greptile://config**: Current server configuration

## Prompts

- **codebase_exploration**: Guided codebase exploration with focus areas

---

🔗 **More Information:** Visit the [Greptile documentation](https://docs.greptile.com) for detailed API reference and advanced usage patterns.`;
  }

  /**
   * Generate exploration prompt for codebase analysis
   */
  private generateExplorationPrompt(repository: string, focusArea?: string): string {
    const basePrompt = `Let's explore the ${repository} codebase systematically.`;

    if (focusArea) {
      return `${basePrompt} I'm particularly interested in understanding the ${focusArea} aspects. 

Please start by indexing the repository, then provide an overview of how ${focusArea} is implemented, including:
1. Key files and components involved
2. Design patterns and architectural decisions
3. Dependencies and interactions with other parts of the system
4. Any notable implementation details or best practices

Use the query_repository tool with session continuity to build a comprehensive understanding.`;
    }

    return `${basePrompt}

Please start by indexing the repository, then provide a comprehensive overview including:
1. Overall architecture and design philosophy  
2. Main components and their responsibilities
3. Key directories and their purposes
4. Notable patterns, frameworks, and technologies used
5. Entry points and data flow

Use the query_repository tool with session continuity to build understanding progressively.`;
  }

  /**
   * Start the MCP server
   */
  async start(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
  }

  /**
   * Create and start server with configuration
   */
  static async create(config: Config): Promise<GreptileMCPServer> {
    const server = new GreptileMCPServer();
    await server.initialize(config);
    return server;
  }
}

// Export for use as a module
export { GreptileMCPServer };

// CLI entry point
if (import.meta.url === `file://${process.argv[1]}`) {
  (async () => {
    // Check environment status first
    const envStatus = checkEnvironmentVariables();

    let config: Config;
    if (envStatus.isFullyConfigured) {
      config = validateConfig();
    } else {
      // Create minimal config for diagnostic mode
      config = {
        apiKey: process.env.GREPTILE_API_KEY,
        githubToken: process.env.GITHUB_TOKEN,
        baseUrl: process.env.GREPTILE_BASE_URL || 'https://api.greptile.com/v2',
        features: {
          streaming: true,
          orchestration: true,
          flowEnhancement: true,
        },
      };
    }

    const server = await GreptileMCPServer.create(config);
    await server.start();
  })().catch(error => {
    console.error('Failed to start server:', error);
    process.exit(1);
  });
}
