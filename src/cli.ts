#!/usr/bin/env node

import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import chalk from 'chalk';
import ora from 'ora';
import { config } from 'dotenv';

import { GreptileMCPServer } from './server.js';
import { validateConfig } from './utils/index.js';
import type { Config, Repository } from './types/index.js';

// Load environment variables
config();

interface CliArgs {
  'api-key'?: string;
  'github-token'?: string;
  'base-url'?: string;
  config?: string;
  repositories?: string;
  stream?: boolean;
  'session-id'?: string;
  timeout?: number;
  verbose?: boolean;
  help?: boolean;
  version?: boolean;
}

/**
 * Create CLI configuration from arguments and environment
 */
function createConfig(args: CliArgs): Config {
  // Parse repositories if provided
  let repositories: Repository[] | undefined;
  if (args.repositories) {
    try {
      repositories = JSON.parse(args.repositories) as Repository[];
    } catch (error) {
      console.error(chalk.red('Error: Invalid repositories JSON format'));
      process.exit(1);
    }
  }

  return validateConfig({
    apiKey: args['api-key'],
    githubToken: args['github-token'],
    baseUrl: args['base-url'] || 'https://api.greptile.com/v2',
    repositories,
    features: {
      streaming: args.stream ?? true,
      orchestration: true,
      flowEnhancement: true,
    },
  });
}

/**
 * Display banner and version information
 */
function displayBanner(): void {
  console.log(chalk.cyan(`
╔══════════════════════════════════════════════════════════╗
║                 🚀 GREPTILE MCP SERVER                   ║
║              TypeScript Edition v3.0.0                  ║
║                                                          ║
║    AI-powered code search and querying via MCP          ║
║         Built with Model Context Protocol SDK           ║
╚══════════════════════════════════════════════════════════╝
`));
}

/**
 * Interactive setup wizard
 */
async function runSetupWizard(): Promise<void> {
  displayBanner();
  
  console.log(chalk.yellow('\n📋 Interactive Setup Wizard\n'));
  
  console.log(`To use Greptile MCP Server, you need:

${chalk.cyan('1. Greptile API Key')}
   • Get it from: ${chalk.underline('https://app.greptile.com/settings/api')}
   • Set as: ${chalk.gray('GREPTILE_API_KEY')} environment variable
   • Or use: ${chalk.gray('--api-key')} CLI argument

${chalk.cyan('2. GitHub Token')}  
   • Generate at: ${chalk.underline('https://github.com/settings/tokens')}
   • Needs: ${chalk.gray('repo')} permissions for repositories you want to index
   • Set as: ${chalk.gray('GITHUB_AI_TOKEN')} or ${chalk.gray('GITHUB_TOKEN')} environment variable
   • Or use: ${chalk.gray('--github-token')} CLI argument

${chalk.yellow('Quick Start Examples:')}

${chalk.gray('# Start MCP server (stdio mode)')}
${chalk.green('npx @greptile/mcp-server')}

${chalk.gray('# With inline credentials')}
${chalk.green('npx @greptile/mcp-server --api-key=xxx --github-token=xxx')}

${chalk.gray('# Index and query a repository')}
${chalk.green('npx @greptile/mcp-server --repositories=\'[{"remote":"github","repository":"microsoft/vscode","branch":"main"}]\'')}

${chalk.yellow('Environment Setup:')}

Create a ${chalk.cyan('.env')} file:
${chalk.gray(`GREPTILE_API_KEY=your_api_key_here
GITHUB_AI_TOKEN=your_github_token_here
# Or fallback to:
# GITHUB_TOKEN=your_github_token_here`)}

${chalk.yellow('MCP Client Integration:')}

Add to your MCP client configuration:
${chalk.gray(`{
  "mcpServers": {
    "greptile": {
      "command": "npx",
      "args": ["@greptile/mcp-server"]
    }
  }
}`)}
`);
}

/**
 * Test API connectivity
 */
async function testConnection(config: Config): Promise<void> {
  const spinner = ora('Testing Greptile API connectivity...').start();
  
  try {
    const server = new GreptileMCPServer();
    await server.initialize(config);
    
    spinner.succeed(chalk.green('✅ API connectivity verified'));
    console.log(chalk.cyan('Server is ready to accept MCP connections'));
  } catch (error) {
    spinner.fail(chalk.red('❌ API connectivity failed'));
    console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
    
    console.log(chalk.yellow('\n🔧 Troubleshooting:'));
    console.log('• Verify your API key is correct');
    console.log('• Check your GitHub token has proper permissions');
    console.log('• Ensure you have internet connectivity');
    console.log('• Try running with --verbose for more details');
    
    process.exit(1);
  }
}

/**
 * Start the MCP server
 */
async function startServer(args: CliArgs): Promise<void> {
  try {
    const config = createConfig(args);
    
    if (args.verbose) {
      displayBanner();
      console.log(chalk.gray('Configuration:'));
      console.log(chalk.gray(`• Base URL: ${config.baseUrl}`));
      console.log(chalk.gray(`• Streaming: ${config.features?.streaming ? 'enabled' : 'disabled'}`));
      console.log(chalk.gray(`• Repositories: ${config.repositories?.length || 0} configured`));
      console.log('');
    }

    const spinner = ora('Initializing Greptile MCP Server...').start();
    
    const server = await GreptileMCPServer.create(config);
    
    spinner.succeed(chalk.green('✅ Server initialized successfully'));
    
    if (args.verbose) {
      console.log(chalk.cyan('🚀 Starting MCP server on stdio transport...'));
      console.log(chalk.gray('Server is now ready to accept MCP requests'));
      console.log(chalk.gray('Use Ctrl+C to stop the server'));
      console.log('');
    }

    // Start the server
    await server.start();
    
  } catch (error) {
    console.error(chalk.red('Failed to start server:'));
    console.error(chalk.red(error instanceof Error ? error.message : String(error)));
    
    if (error instanceof Error && error.message.includes('API key')) {
      console.log(chalk.yellow('\n💡 Run "npx @greptile/mcp-server init" for setup help'));
    }
    
    process.exit(1);
  }
}

/**
 * Main CLI handler
 */
async function main(): Promise<void> {
  const argv = await yargs(hideBin(process.argv))
    .scriptName('greptile-mcp')
    .usage('$0 [options]')
    .example('$0', 'Start MCP server with environment variables')
    .example('$0 --api-key xxx --github-token yyy', 'Start with inline credentials')
    .example('$0 init', 'Run interactive setup wizard')
    .example('$0 test', 'Test API connectivity')
    
    .command('init', 'Run interactive setup wizard', {}, async () => {
      await runSetupWizard();
    })
    
    .command('test', 'Test API connectivity', {}, async (args: any) => {
      try {
        const config = createConfig(args);
        await testConnection(config);
      } catch (error) {
        console.error(chalk.red('Configuration error:'));
        console.error(chalk.red(error instanceof Error ? error.message : String(error)));
        console.log(chalk.yellow('\n💡 Run "npx @greptile/mcp-server init" for setup help'));
        process.exit(1);
      }
    })
    
    .option('api-key', {
      type: 'string',
      description: 'Greptile API key (or set GREPTILE_API_KEY env var)',
    })
    
    .option('github-token', {
      type: 'string', 
      description: 'GitHub personal access token (or set GITHUB_AI_TOKEN/GITHUB_TOKEN env var)',
    })
    
    .option('base-url', {
      type: 'string',
      description: 'Greptile API base URL',
      default: 'https://api.greptile.com/v2',
    })
    
    .option('config', {
      type: 'string',
      description: 'Path to configuration file',
    })
    
    .option('repositories', {
      type: 'string',
      description: 'JSON array of repositories to configure',
    })
    
    .option('stream', {
      type: 'boolean',
      description: 'Enable streaming responses by default',
      default: true,
    })
    
    .option('session-id', {
      type: 'string',
      description: 'Default session ID for queries',
    })
    
    .option('timeout', {
      type: 'number',
      description: 'Default request timeout in milliseconds',
      default: 60000,
    })
    
    .option('verbose', {
      alias: 'v',
      type: 'boolean',
      description: 'Enable verbose output',
      default: false,
    })
    
    .help('help')
    .alias('help', 'h')
    .version('3.0.0')
    .alias('version', 'V')
    
    .strict()
    .parseAsync();

  // Handle default command (start server)
  if (argv._.length === 0) {
    await startServer(argv as CliArgs);
  }
}

// Handle unhandled rejections and exceptions
process.on('unhandledRejection', (reason, promise) => {
  console.error(chalk.red('Unhandled Rejection at:'), promise, chalk.red('reason:'), reason);
  process.exit(1);
});

process.on('uncaughtException', (error) => {
  console.error(chalk.red('Uncaught Exception:'), error);
  process.exit(1);
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log(chalk.yellow('\n🛑 Shutting down server gracefully...'));
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log(chalk.yellow('\n🛑 Received SIGTERM, shutting down...'));
  process.exit(0);
});

// Start the CLI
main().catch((error) => {
  console.error(chalk.red('CLI Error:'), error);
  process.exit(1);
});