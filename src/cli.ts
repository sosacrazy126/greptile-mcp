#!/usr/bin/env node

import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import chalk from 'chalk';
import ora from 'ora';
import { config } from 'dotenv';

import { GreptileMCPServer } from './server.js';
import { validateConfig, checkEnvironmentVariables } from './utils/index.js';
import type { Config, Repository } from './types/index.js';

// Load environment variables
config();

/**
 * Get platform-specific environment variable setup instructions
 */
function getPlatformSpecificEnvInstructions(): string {
  const platform = process.platform;
  const isWindows = platform === 'win32';

  if (isWindows) {
    return `
${chalk.gray('Windows PowerShell:')}
${chalk.green('$env:GREPTILE_API_KEY="your_api_key_here"')}
${chalk.green('$env:GITHUB_TOKEN="your_github_token_here"')}

${chalk.gray('Windows Command Prompt:')}
${chalk.green('set GREPTILE_API_KEY=your_api_key_here')}
${chalk.green('set GITHUB_TOKEN=your_github_token_here')}

${chalk.gray('Permanent (Windows):')}
${chalk.green('setx GREPTILE_API_KEY "your_api_key_here"')}
${chalk.green('setx GITHUB_TOKEN "your_github_token_here"')}
${chalk.yellow('Note: Restart terminal after using setx')}`;
  } else {
    // Unix-like systems (Linux, macOS)
    const shell = process.env.SHELL?.split('/').pop() || 'bash';
    const configFile =
      shell === 'zsh' ? '~/.zshrc' : shell === 'fish' ? '~/.config/fish/config.fish' : '~/.bashrc';

    return `
${chalk.gray('Current session (Linux/macOS):')}
${chalk.green('export GREPTILE_API_KEY="your_api_key_here"')}
${chalk.green('export GITHUB_TOKEN="your_github_token_here"')}

${chalk.gray(`Permanent (add to ${configFile}):`)}
${chalk.green('echo \'export GREPTILE_API_KEY="your_api_key_here"\' >> ' + configFile)}
${chalk.green('echo \'export GITHUB_TOKEN="your_github_token_here"\' >> ' + configFile)}
${chalk.green('source ' + configFile)}

${chalk.gray('Or use a one-liner:')}
${chalk.green('GREPTILE_API_KEY="your_key" GITHUB_TOKEN="your_token" npx greptile-mcp-server')}`;
  }
}

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
  console.log(
    chalk.cyan(`
╔══════════════════════════════════════════════════════════╗
║                 🚀 GREPTILE MCP SERVER                   ║
║              TypeScript Edition v3.0.4                  ║
║                                                          ║
║    AI-powered code search and querying via MCP          ║
║         Built with Model Context Protocol SDK           ║
╚══════════════════════════════════════════════════════════╝
`)
  );
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
   • Set as: ${chalk.gray('GITHUB_TOKEN')} environment variable
   • Or use: ${chalk.gray('--github-token')} CLI argument

${chalk.yellow('Quick Start Examples:')}

${chalk.gray('# Start MCP server (stdio mode)')}
${chalk.green('npx greptile-mcp-server')}

${chalk.gray('# With inline credentials')}
${chalk.green('npx greptile-mcp-server --api-key=xxx --github-token=xxx')}

${chalk.gray('# Index and query a repository')}
${chalk.green('npx greptile-mcp-server --repositories=\'[{"remote":"github","repository":"microsoft/vscode","branch":"main"}]\'')}

${chalk.yellow('Environment Setup:')}

${chalk.cyan('Option 1: .env file (Recommended for local development)')}
Create a ${chalk.cyan('.env')} file in your project directory:
${chalk.gray(`GREPTILE_API_KEY=your_api_key_here
GITHUB_TOKEN=your_github_token_here`)}

${chalk.cyan('Option 2: System Environment Variables')}
${getPlatformSpecificEnvInstructions()}

${chalk.yellow('MCP Client Integration:')}

Add to your MCP client configuration:
${chalk.gray(`{
  "mcpServers": {
    "greptile": {
      "command": "npx",
      "args": ["greptile-mcp-server"]
    }
  }
}`)}

${chalk.yellow('Testing Your Setup:')}

After setting up your environment variables, test your configuration:
${chalk.green('npx greptile-mcp-server test')}

${chalk.yellow('Common Issues & Solutions:')}

${chalk.gray('❌ "Environment variables missing"')}
${chalk.white('→ Make sure you restart your terminal after setting permanent env vars')}
${chalk.white('→ Verify with:')} ${chalk.green('echo $GREPTILE_API_KEY')} ${chalk.gray('(Linux/macOS)')}
${chalk.white('→ Verify with:')} ${chalk.green('echo $env:GREPTILE_API_KEY')} ${chalk.gray('(Windows PowerShell)')}

${chalk.gray('❌ "GitHub token validation failed"')}
${chalk.white('→ Ensure your token has "repo" permissions')}
${chalk.white('→ Generate a new token at: https://github.com/settings/tokens')}
${chalk.white('→ Select "Fine-grained personal access tokens" for better security')}

${chalk.gray('❌ "Greptile API authentication failed"')}
${chalk.white('→ Get your API key from: https://app.greptile.com/settings/api')}
${chalk.white('→ Check if your API key has expired')}
${chalk.white('→ Verify the key is correctly copied (no extra spaces)')}

${chalk.yellow('Need Help?')}
${chalk.white('Run')} ${chalk.green('npx greptile-mcp-server test')} ${chalk.white('for detailed diagnostics')}
`);
}

/**
 * Test API connectivity
 */
async function testConnection(config: Config): Promise<void> {
  console.log(chalk.cyan('🔍 Testing Greptile MCP Server Configuration...\n'));

  // Test 1: Environment Variables
  const spinner1 = ora('Checking environment variables...').start();
  const envStatus = checkEnvironmentVariables();

  if (!envStatus.isFullyConfigured) {
    spinner1.fail(chalk.red('❌ Environment variables missing'));
    console.log(chalk.yellow('Missing variables:'), envStatus.missingVars.join(', '));
    console.log(chalk.yellow('\n💡 Run "npx greptile-mcp-server init" for setup help'));
    process.exit(1);
  }
  spinner1.succeed(chalk.green('✅ Environment variables configured'));

  // Test 2: Greptile API Authentication
  const spinner2 = ora('Testing Greptile API authentication...').start();
  try {
    const { GreptileClient } = await import('./clients/greptile.js');
    const client = new GreptileClient(config);

    // Make an actual authenticated API call to validate credentials
    const isHealthy = await client.healthCheck();
    if (!isHealthy) {
      throw new Error(
        'Greptile API health check failed - service may be down or credentials invalid'
      );
    }

    spinner2.succeed(chalk.green('✅ Greptile API connection verified'));
  } catch (error) {
    spinner2.fail(chalk.red('❌ Greptile API authentication failed'));
    console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));

    console.log(chalk.yellow('\n🔧 Troubleshooting:'));
    console.log('• Verify your GREPTILE_API_KEY is correct');
    console.log('• Get your API key from: https://app.greptile.com/settings/api');
    console.log('• Check that your API key has not expired');

    process.exit(1);
  }

  // Test 3: GitHub Token Validation
  const spinner3 = ora('Testing GitHub token permissions...').start();
  try {
    const githubResponse = await fetch('https://api.github.com/user', {
      headers: {
        Authorization: `Bearer ${config.githubToken}`,
        'User-Agent': 'greptile-mcp-server/3.0.0',
      },
    });

    if (!githubResponse.ok) {
      throw new Error(`GitHub API returned ${githubResponse.status}: ${githubResponse.statusText}`);
    }

    const userData = (await githubResponse.json()) as { login: string };
    spinner3.succeed(chalk.green(`✅ GitHub token verified (user: ${userData.login})`));
  } catch (error) {
    spinner3.fail(chalk.red('❌ GitHub token validation failed'));
    console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));

    console.log(chalk.yellow('\n🔧 Troubleshooting:'));
    console.log('• Verify your GITHUB_TOKEN is correct');
    console.log('• Generate a new token at: https://github.com/settings/tokens');
    console.log('• Ensure token has "repo" permissions for repositories you want to index');

    process.exit(1);
  }

  console.log(chalk.green('\n🎉 All tests passed! Your Greptile MCP Server is ready.'));
  console.log(chalk.cyan('Server is ready to accept MCP connections'));
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
      console.log(
        chalk.gray(`• Streaming: ${config.features?.streaming ? 'enabled' : 'disabled'}`)
      );
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

    if (error instanceof Error) {
      if (error.message.includes('API key') || error.message.includes('GITHUB_TOKEN')) {
        console.log(chalk.yellow('\n🔧 Quick Setup:'));
        console.log(
          chalk.yellow('• Run'),
          chalk.green('npx greptile-mcp-server init'),
          chalk.yellow('for interactive setup')
        );
        console.log(
          chalk.yellow('• Run'),
          chalk.green('npx greptile-mcp-server test'),
          chalk.yellow('to validate your configuration')
        );
      }
    }

    process.exit(1);
  }
}

/**
 * Main CLI handler
 */
async function main(): Promise<void> {
  const argv = await yargs(hideBin(process.argv))
    .scriptName('greptile-mcp-server')
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
        console.log(chalk.yellow('\n💡 Run "npx greptile-mcp-server init" for setup help'));
        process.exit(1);
      }
    })

    .option('api-key', {
      type: 'string',
      description: 'Greptile API key (or set GREPTILE_API_KEY env var)',
    })

    .option('github-token', {
      type: 'string',
      description: 'GitHub personal access token (or set GITHUB_TOKEN env var)',
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

process.on('uncaughtException', error => {
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
main().catch(error => {
  console.error(chalk.red('CLI Error:'), error);
  process.exit(1);
});
