#!/usr/bin/env node

import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import {
  buildHeaders,
  buildIgnoreRules,
  getConfigDir,
  isHttpUrl,
  isHttpsUrl,
  makeDebugLogger,
  maybeLoadJsonArg,
  sha256Hex,
  startAuthCallbackServer,
} from './mcp-remote-lib.js';

async function main() {
  const argv = await yargs(hideBin(process.argv))
    .scriptName('mcp-remote')
    .usage('$0 <server> [port] [options]')
    .positional('server', {
      type: 'string',
      describe: 'Remote MCP server URL (e.g. https://remote.mcp.server/sse)',
      demandOption: true,
    })
    .positional('port', {
      type: 'number',
      describe: 'Local OAuth callback port to try first (default 3334)',
    })
    .option('host', {
      type: 'string',
      describe: 'Host to bind for OAuth callback URL',
      default: 'localhost',
    })
    .option('header', {
      type: 'array',
      string: true,
      describe: 'Custom header to include in all remote requests (repeatable) in the form Key: Value',
    })
    .option('allow-http', {
      type: 'boolean',
      describe: 'Allow HTTP connections (only for trusted private networks)',
      default: false,
    })
    .option('debug', {
      type: 'boolean',
      describe: 'Enable verbose debug logging to ~/.mcp-auth/{server_hash}_debug.log',
      default: false,
    })
    .option('enable-proxy', {
      type: 'boolean',
      describe: 'Enable HTTP(S) proxy support using environment variables (HTTP_PROXY/HTTPS_PROXY/NO_PROXY)',
      default: false,
    })
    .option('ignore-tool', {
      type: 'array',
      string: true,
      describe: 'Patterns of tool names to ignore (supports * wildcards). Can be specified multiple times.',
    })
    .option('auth-timeout', {
      type: 'number',
      describe: 'Timeout in seconds to wait for OAuth callback',
      default: 30,
    })
    .option('transport', {
      type: 'string',
      choices: ['http-first', 'sse-first', 'http-only', 'sse-only'] as const,
      describe: 'Transport strategy when connecting to remote MCP server',
      default: 'http-first',
    })
    .option('static-oauth-client-metadata', {
      type: 'string',
      describe: 'Static OAuth client metadata JSON, or @/path/to/file.json',
    })
    .option('static-oauth-client-info', {
      type: 'string',
      describe: 'Static OAuth client information JSON, or @/path/to/file.json',
    })
    .help()
    .strict()
    .parseAsync();

  const serverUrl = (argv.server as unknown as string).trim();
  const debugLog = makeDebugLogger(serverUrl, !!argv.debug);
  debugLog.log('Starting mcp-remote with args', { ...argv, header: undefined });

  // Validate URL scheme
  const isHttps = isHttpsUrl(serverUrl);
  const isHttp = isHttpUrl(serverUrl);
  if (!isHttps && !isHttp) {
    console.error('Invalid server URL. Expected http(s)://');
    process.exit(2);
  }
  if (isHttp && !argv.allowHttp) {
    console.error('Refusing to connect over HTTP without --allow-http. Use only on trusted networks.');
    process.exit(3);
  }

  // Proxy support (best-effort informational only; Node may not respect these automatically)
  if (argv.enableProxy) {
    const hp = process.env.HTTP_PROXY && process.env.HTTP_PROXY.trim();
    const hps = process.env.HTTPS_PROXY && process.env.HTTPS_PROXY.trim();
    const np = process.env.NO_PROXY && process.env.NO_PROXY.trim();
    debugLog.log('Proxy requested. HTTP_PROXY=', hp, 'HTTPS_PROXY=', hps, 'NO_PROXY=', np);
  }

  // Prepare headers and rules
  const extraHeaders = buildHeaders(argv.header as string[] | undefined);
  const ignoreRules = buildIgnoreRules(argv['ignore-tool'] as string[] | undefined);

  // Load static OAuth inputs if provided (validation only)
  try {
    const staticMeta = await maybeLoadJsonArg(argv['static-oauth-client-metadata'] as string | undefined);
    if (staticMeta) debugLog.log('Loaded static OAuth client metadata');
    const staticInfo = await maybeLoadJsonArg(argv['static-oauth-client-info'] as string | undefined);
    if (staticInfo) debugLog.log('Loaded static OAuth client info');
  } catch (e) {
    console.error('Failed to parse static OAuth inputs:', e instanceof Error ? e.message : String(e));
    process.exit(4);
  }

  // Start OAuth callback server (on-demand for future OAuth exchanges)
  const desiredPort = typeof argv.port === 'number' && !Number.isNaN(argv.port) ? argv.port : 3334;
  const { server: authServer, url: callbackUrl, waitForCode } = await startAuthCallbackServer({
    host: (argv.host as string) || 'localhost',
    desiredPort,
    timeoutSec: (argv['auth-timeout'] as number) ?? 30,
    debugLog,
  });

  // Informational banner
  const serverHash = sha256Hex(serverUrl).slice(0, 8);
  console.log(`mcp-remote: connecting to ${serverUrl} [id ${serverHash}]`);
  console.log(`OAuth callback listening at ${callbackUrl}`);
  if (Object.keys(extraHeaders).length) {
    console.log('Using custom headers:', Object.keys(extraHeaders).join(', '));
  }
  if (ignoreRules.length) {
    console.log('Ignoring tools matching:', ignoreRules.map(r => r.pattern).join(', '));
  }
  console.log(`Transport strategy: ${argv.transport}`);

  console.log('mcp-remote is running in placeholder mode. This build focuses on CLI, flags, and local OAuth callback.');
  console.log('For full proxying behavior, see docs/mcp-remote.md and use the remote server directly where supported.');

  // Keep process alive until interrupted, or until OAuth code is received (for diagnostics)
  waitForCode().then(code => {
    if (code) {
      debugLog.log('Received OAuth code; placeholder build will exit.');
      try { authServer.close(); } catch {}
      console.log('Received OAuth code. Exiting placeholder mcp-remote.');
      process.exit(0);
    }
  }).catch(() => {});

  // Keep the event loop alive
  const keepAlive = setInterval(() => {
    debugLog.log('heartbeat');
  }, 10_000);

  const shutdown = () => {
    clearInterval(keepAlive);
    try { authServer.close(); } catch {}
    debugLog.log('Shutting down');
    process.exit(0);
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

main().catch(err => {
  console.error('Fatal error in mcp-remote:', err instanceof Error ? err.message : String(err));
  process.exit(1);
});
