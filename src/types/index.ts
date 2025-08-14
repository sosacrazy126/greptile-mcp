import { z } from 'zod';

// Core Greptile API Types
export const RepositorySchema = z.object({
  remote: z.enum(['github', 'gitlab']),
  repository: z.string(),
  branch: z.string(),
});

export const QueryMessageSchema = z.object({
  role: z.enum(['user', 'assistant']),
  content: z.string(),
});

export const SourceSchema = z.object({
  repository: z.string(),
  remote: z.string(),
  branch: z.string(),
  filepath: z.string(),
  linestart: z.number(),
  lineend: z.number(),
  summary: z.string().optional(),
});

export const QueryResponseSchema = z.object({
  message: z.string(),
  sources: z.array(SourceSchema).optional(),
  session_id: z.string().optional(),
  streamed: z.boolean().optional(),
  streaming_metadata: z.record(z.unknown()).optional(),
});

// Session Management Types
export const SessionContextSchema = z.object({
  session_id: z.string(),
  query_count: z.number(),
  exploration_domains: z.array(z.string()),
  depth_achieved: z.number(),
  patterns_discovered: z.array(z.string()),
  connections_made: z.array(z.string()),
  created_at: z.number(),
  last_active: z.number(),
});

// CLI Configuration Types
export const ConfigSchema = z.object({
  apiKey: z.string().optional(),
  githubToken: z.string().optional(),
  baseUrl: z.string().default('https://api.greptile.com/v2'),
  repositories: z.array(RepositorySchema).optional(),
  features: z
    .object({
      streaming: z.boolean().default(true),
      orchestration: z.boolean().default(true),
      flowEnhancement: z.boolean().default(true),
    })
    .optional(),
  plugins: z.array(z.string()).optional(),
});

// Exported types
export type Repository = z.infer<typeof RepositorySchema>;
export type QueryMessage = z.infer<typeof QueryMessageSchema>;
export type Source = z.infer<typeof SourceSchema>;
export type QueryResponse = z.infer<typeof QueryResponseSchema>;
export type SessionContext = z.infer<typeof SessionContextSchema>;
export type Config = z.infer<typeof ConfigSchema>;

// MCP Tool Input/Output Types
export interface IndexRepositoryInput {
  remote: string;
  repository: string;
  branch: string;
  reload?: boolean;
  notify?: boolean;
}

export interface QueryRepositoryInput {
  query: string;
  repositories?: Repository[];
  session_id?: string;
  stream?: boolean;
  genius?: boolean;
  timeout?: number;
  previous_messages?: QueryMessage[];
}

export interface SearchRepositoryInput {
  query: string;
  repositories?: Repository[];
  session_id?: string;
  genius?: boolean;
  timeout?: number;
  previous_messages?: QueryMessage[];
}

export interface GetRepositoryInfoInput {
  remote: string;
  repository: string;
  branch: string;
}

// Streaming Types
export interface StreamingChunk {
  type: 'text' | 'citation' | 'session' | 'other';
  content?: string;
  file?: string | undefined;
  lines?: string | undefined;
  sessionId?: string;
  data?: unknown;
  timestamp: number;
}

// Error Types
export interface GreptileError extends Error {
  code?: string;
  statusCode?: number;
  response?: unknown;
}

// Environment Checking Types
export interface EnvironmentStatus {
  hasGreptileApiKey: boolean;
  hasGithubToken: boolean;
  isFullyConfigured: boolean;
  missingVars: string[];
  suggestions: string[];
  configErrors?: string[];
}

// Plugin System Types
export interface GreptilePlugin {
  name: string;
  version: string;
  description: string;
  tools?: string[];
  resources?: string[];
  prompts?: string[];
  middleware?: string[];
  initialize?: () => Promise<void>;
  cleanup?: () => Promise<void>;
}
