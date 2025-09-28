import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { GreptileClient } from './clients/greptile.js';
import type { QueryMessage, StreamingChunk } from './types/index.js';
import { generateSessionId, createErrorResponse } from './utils/index.js';

// Enhanced configuration schema for Smithery with validation and user guidance
export const configSchema = z.object({
  // Required API credentials
  greptileApiKey: z
    .string()
    .min(1, 'API key is required')
    .describe(
      'Your Greptile API key from app.greptile.com/settings/api (required for all functionality)'
    ),

  githubToken: z
    .string()
    .min(1, 'GitHub token is required')
    .describe(
      'GitHub personal access token with repo permissions (required for repository access)'
    ),

  // Optional service configuration
  greptileBaseUrl: z
    .string()
    .url('Must be a valid URL')
    .default('https://api.greptile.com/v2')
    .describe('Greptile API base URL (leave default unless using custom instance)'),

  // Transport and networking settings
  transport: z
    .enum(['stdio', 'sse'])
    .default('stdio')
    .describe('MCP transport method (stdio for Claude Desktop, sse for web interfaces)'),

  host: z
    .string()
    .ip({ version: 'v4' })
    .default('0.0.0.0')
    .describe(
      'Host binding for SSE transport (0.0.0.0 for all interfaces, 127.0.0.1 for localhost only)'
    ),

  port: z
    .number()
    .int()
    .min(1024, 'Port must be above 1024')
    .max(65535, 'Port must be below 65536')
    .default(8080)
    .describe('Port for SSE transport (1024-65535, default 8080)'),
});

// Export the config type for external use
export type SmitheryConfig = z.infer<typeof configSchema>;

type Config = z.infer<typeof configSchema>;

export default function ({ config }: { config: Config }) {
  const server = new McpServer({
    name: 'greptile-mcp-server',
    version: '3.0.4',
    description: 'AI-powered code search and querying with Greptile API',
  });

  // Initialize Greptile client
  const greptileClient = new GreptileClient({
    apiKey: config.greptileApiKey,
    githubToken: config.githubToken,
    baseUrl: config.greptileBaseUrl,
  });

  // Add greptile_help tool
  server.tool(
    'greptile_help',
    'Get comprehensive help and usage examples for all Greptile MCP tools',
    {},
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

  // Add index_repository tool
  server.tool(
    'index_repository',
    'Index a repository to make it searchable for future queries',
    {
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

  // Add query_repository tool
  server.tool(
    'query_repository',
    'Query repositories using natural language to get detailed answers with code references',
    {
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

          for await (const chunk of streamingResponse as AsyncIterable<StreamingChunk>) {
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

  // Add get_repository_info tool
  server.tool(
    'get_repository_info',
    'Get information about an indexed repository including status and metadata',
    {
      remote: z.enum(['github', 'gitlab']).describe('Repository host'),
      repository: z.string().describe('Repository in owner/repo format'),
      branch: z.string().describe('Branch that was indexed'),
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

  // Add resources
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
      return { contents: [{ uri: uri.href, mimeType: 'text/markdown', text: helpContent }] };
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
          { uri: uri.href, mimeType: 'application/json', text: JSON.stringify(config, null, 2) },
        ],
      };
    }
  );

  // Add prompts
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
