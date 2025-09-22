import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { GreptileClient } from './clients/greptile.js';
import type { QueryMessage } from './types/index.js';
import { generateSessionId, createErrorResponse } from './utils/index.js';

// Configuration schema for Smithery - this will auto-generate the session config UI
export const configSchema = z.object({
  greptileApiKey: z.string().default('').describe('Your Greptile API key from app.greptile.com/settings/api (required for functionality)'),
  githubToken: z.string().default('').describe('GitHub personal access token with repo permissions (required for repository access)'),
  greptileBaseUrl: z
    .string()
    .default('https://api.greptile.com/v2')
    .describe('Base URL for Greptile API'),
  transport: z.string().default('stdio').describe('Transport method for MCP'),
  host: z.string().default('0.0.0.0').describe('Host binding for SSE transport'),
  port: z.number().default(8080).describe('Port for SSE transport'),
});

type Config = z.infer<typeof configSchema>;

// Required: Export default createServer function for Smithery
export default function createServer({ config }: { config: Config }) {
  const server = new McpServer({
    name: 'greptile-mcp-server',
    version: '3.0.4',
    description: 'AI-powered code search and querying with Greptile API',
  });

  // Initialize Greptile client with user-provided configuration
  const greptileClient = new GreptileClient({
    apiKey: config.greptileApiKey,
    githubToken: config.githubToken,
    baseUrl: config.greptileBaseUrl,
  });

  // Register greptile_help tool
  server.registerTool(
    'greptile_help',
    {
      title: 'Greptile Help',
      description: 'Get comprehensive help and usage examples for all Greptile MCP tools',
      inputSchema: {},
    },
    async () => {
      const helpContent = `# 🚀 Greptile MCP Server - Comprehensive Guide

## Overview
The Greptile MCP Server provides AI-powered code search and querying capabilities through the Model Context Protocol (MCP). It integrates with the Greptile API to index repositories and answer natural language questions about codebases.

## Available Tools

### 1. \`greptile_help\`
Get this comprehensive help documentation.

### 2. \`index_repository\`
Index a repository to make it searchable for future queries.

**Parameters:**
- \`remote\`: "github" or "gitlab"
- \`repository\`: Repository in "owner/repo" format
- \`branch\`: Branch to index
- \`reload\`: Force reprocessing (optional, default: true)
- \`notify\`: Email notification (optional, default: false)

### 3. \`query_repository\`
Query repositories using natural language to get detailed answers with code references.

**Parameters:**
- \`query\`: Natural language question
- \`repositories\`: Array of repository objects
- \`session_id\`: For conversation continuity (auto-generated if not provided)
- \`stream\`: Enable streaming response (optional, default: false)
- \`genius\`: Enhanced capabilities (optional, default: true)

### 4. \`get_repository_info\`
Get information about an indexed repository.

**Parameters:**
- \`remote\`: Repository host
- \`repository\`: Repository identifier
- \`branch\`: Branch name

## Best Practices

### Repository Workflow
1. **Index** repositories first using \`index_repository\`
2. **Verify** indexing status with \`get_repository_info\`
3. **Query** using natural language with \`query_repository\`

### Session Management
- Use consistent \`session_id\` across related queries for better context
- Session continuity improves answer quality over multiple interactions

For more information, visit: https://docs.greptile.com`;

      return {
        content: [{ type: 'text', text: helpContent }],
      };
    }
  );

  // Register index_repository tool
  server.registerTool(
    'index_repository',
    {
      title: 'Index Repository',
      description: 'Index a repository to make it searchable for future queries',
      inputSchema: {
        remote: z.enum(['github', 'gitlab']).describe('Repository host (github or gitlab)'),
        repository: z.string().describe('Repository in owner/repo format'),
        branch: z.string().describe('Branch to index'),
        reload: z
          .boolean()
          .default(true)
          .describe('Force reprocessing of previously indexed repository'),
        notify: z
          .boolean()
          .default(false)
          .describe('Send email notification when indexing completes'),
      },
    },
    async ({ remote, repository, branch, reload, notify }) => {
      try {
        const result = await greptileClient.indexRepository(
          remote,
          repository,
          branch,
          reload,
          notify
        );

        return {
          content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        return {
          content: [
            {
              type: 'text',
              text: createErrorResponse(`Failed to index repository: ${errorMessage}`),
            },
          ],
        };
      }
    }
  );

  // Register query_repository tool
  server.registerTool(
    'query_repository',
    {
      title: 'Query Repository',
      description:
        'Query repositories using natural language to get detailed answers with code references',
      inputSchema: {
        query: z.string().describe('Natural language query about the codebase'),
        repositories: z
          .array(
            z.object({
              remote: z.enum(['github', 'gitlab']),
              repository: z.string(),
              branch: z.string(),
            })
          )
          .default([])
          .describe('List of repositories to query'),
        session_id: z
          .string()
          .optional()
          .describe('Session ID for conversation continuity (auto-generated if not provided)'),
        stream: z.boolean().default(false).describe('Enable streaming response'),
        genius: z.boolean().default(true).describe('Use enhanced query capabilities'),
        timeout: z.number().default(60000).describe('Request timeout in milliseconds'),
        previous_messages: z
          .array(
            z.object({
              role: z.enum(['user', 'assistant']),
              content: z.string(),
            })
          )
          .default([])
          .describe('Previous conversation messages for context'),
      },
    },
    async ({ query, repositories, session_id, stream, genius, timeout, previous_messages }) => {
      try {
        // Generate session ID if not provided
        const sessionId = session_id || generateSessionId();

        // Prepare messages array
        const messages: QueryMessage[] = [
          ...previous_messages,
          { role: 'user' as const, content: query },
        ];

        if (stream) {
          // Handle streaming response
          const streamResults: string[] = [];
          const streamingResponse = await greptileClient.queryRepositories(
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
          const result = await greptileClient.queryRepositories(
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
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        return {
          content: [
            {
              type: 'text',
              text: createErrorResponse(`Failed to query repository: ${errorMessage}`),
            },
          ],
        };
      }
    }
  );

  // Register get_repository_info tool
  server.registerTool(
    'get_repository_info',
    {
      title: 'Get Repository Info',
      description: 'Get information about an indexed repository including status and metadata',
      inputSchema: {
        remote: z.enum(['github', 'gitlab']).describe('Repository host'),
        repository: z.string().describe('Repository in owner/repo format'),
        branch: z.string().describe('Branch that was indexed'),
      },
    },
    async ({ remote, repository, branch }) => {
      try {
        const result = await greptileClient.getRepositoryInfo(remote, repository, branch);

        return {
          content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        return {
          content: [
            {
              type: 'text',
              text: createErrorResponse(`Failed to get repository info: ${errorMessage}`),
            },
          ],
        };
      }
    }
  );

  // Register resources
  server.registerResource(
    'greptile-help',
    'greptile://help',
    {
      title: 'Greptile MCP Help',
      description: 'Comprehensive documentation for all Greptile MCP features',
      mimeType: 'text/markdown',
    },
    async uri => {
      const helpContent = `# Greptile MCP Server Resources\n\nThis resource provides comprehensive documentation for all Greptile MCP features.`;
      return {
        contents: [{ uri: uri.href, mimeType: 'text/markdown', text: helpContent }],
      };
    }
  );

  server.registerResource(
    'greptile-config',
    'greptile://config',
    {
      title: 'Current Configuration',
      description: 'Current server configuration and settings',
      mimeType: 'application/json',
    },
    async uri => {
      return {
        contents: [
          {
            uri: uri.href,
            mimeType: 'application/json',
            text: JSON.stringify(config, null, 2),
          },
        ],
      };
    }
  );

  // Register prompts
  server.registerPrompt(
    'codebase_exploration',
    {
      title: 'Codebase Exploration',
      description: 'Start exploring a codebase with guided questions',
      argsSchema: {
        repository: z.string().describe('Repository to explore (owner/repo)'),
        focus_area: z
          .string()
          .optional()
          .describe('Specific area to focus on (architecture, authentication, etc.)'),
      },
    },
    ({ repository, focus_area }) => {
      const basePrompt = `Let's explore the ${repository} codebase systematically.`;

      let promptText = basePrompt;
      if (focus_area) {
        promptText += ` I'm particularly interested in understanding the ${focus_area} aspects.

Please start by indexing the repository, then provide an overview of how ${focus_area} is implemented.`;
      } else {
        promptText += `

Please start by indexing the repository, then provide a comprehensive overview of the codebase architecture.`;
      }

      return {
        description: 'Guided codebase exploration prompt',
        messages: [
          {
            role: 'user' as const,
            content: {
              type: 'text',
              text: promptText,
            },
          },
        ],
      };
    }
  );

  return server.server;
}

// Also export the legacy exports for backward compatibility
export { GreptileMCPServer } from './server.js';
export { GreptileClient } from './clients/greptile.js';
export * from './types/index.js';
export * from './utils/index.js';
