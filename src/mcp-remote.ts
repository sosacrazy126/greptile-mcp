#!/usr/bin/env node

import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import { createHash } from 'crypto';
import os from 'os';
import fs from 'fs';
import path from 'path';
import http from 'http';

interface ParsedHeader {
  key: string;
  value: string;
}

interface IgnoreRule {
  pattern: string;
  regex: RegExp;
}

function toBooleanEnv(name: string): string | undefined {
  const v = process.env[name];
  return v && v.trim() ? v : undefined;
}

function ensureDirExists(dir: string): void {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function sha256Hex(input: string): string {
  return createHash('sha256').update(input).digest('hex');
}

function getConfigDir(): string {
  const base = process.env.MCP_REMOTE_CONFIG_DIR || path.join(os.homedir(), '.mcp-auth');
  ensureDirExists(base);
  return base;
}

function makeDebugLogger(serverUrl: string, enabled: boolean) {
  const dir = getConfigDir();
  const hash = sha256Hex(serverUrl).slice(0, 16);
  const file = path.join(dir, `${hash}_debug.log`);

  const write = (line: string) => {
    const ts = new Date().toISOString();
    fs.appendFileSync(file, `[${ts}] ${line}\n`);
  };

  return {
    file,
    log: (...args: unknown[]) => {
      if (!enabled) return;
      try {
        write(args.map(a => (typeof a === 'string' ? a : JSON.stringify(a))).join(' '));
      } catch {
        // ignore logging errors
      }
    },
  };
}

function parseHeader(h: string): ParsedHeader | null {
  const idx = h.indexOf(':');
  if (idx === -1) return null;
  const key = h.slice(0, idx).trim();
  const value = h.slice(idx + 1).trim();
  if (!key) return null;
  return { key, value };
}

function buildHeaders(headers?: string[]): Record<string, string> {
  const result: Record<string, string> = {};
  if (!headers) return result;
  for (const h of headers) {
    const parsed = parseHeader(h);
    if (parsed) {
      result[parsed.key] = parsed.value;
    }
  }
  return result;
}

function wildcardToRegex(pattern: string): RegExp {
  // Escape regex special chars except '*'
  const escaped = pattern.replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*');
  return new RegExp(`^${escaped}$`);
}

function buildIgnoreRules(patterns?: string[]): IgnoreRule[] {
  return (patterns || []).map(p => ({ pattern: p, regex: wildcardToRegex(p) }));
}

function isHttpsUrl(url: string): boolean {
  try {
    const u = new URL(url);
    return u.protocol === 'https:';
  } catch {
    return false;
  }
}

function isHttpUrl(url: string): boolean {
  try {
    const u = new URL(url);
    return u.protocol === 'http:';
  } catch {
    return false;
  }
}

async function maybeLoadJsonArg(input?: string): Promise<unknown | undefined> {
  if (!input) return undefined;
  const trimmed = input.trim();
  if (!trimmed) return undefined;
  if (trimmed.startsWith('@')) {
    const filePath = trimmed.slice(1);
    const content = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(content);
  }
  return JSON.parse(trimmed);
}

async function startAuthCallbackServer(opts: {
  host: string;
  desiredPort: number;
  timeoutSec: number;
  debugLog: ReturnType<typeof makeDebugLogger>;
}): Promise<{ server: http.Server; port: number; url: string; waitForCode: () => Promise<{ code: string; state?: string } | null> }>
{
  const debug = opts.debugLog;
  const started = Date.now();
  let resolver: (val: { code: string; state?: string } | null) => void = () => {};
  const waitForCode = () => new Promise<{ code: string; state?: string } | null>(resolve => {
    resolver = resolve;
  });

  const server = http.createServer((req, res) => {
    try {
      const url = new URL(req.url || '/', `http://${req.headers.host}`);
      if (url.pathname === '/callback') {
        const code = url.searchParams.get('code') || '';
        const state = url.searchParams.get('state') || undefined;
        debug.log('OAuth callback received: code length', code.length, 'state', state);
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end('<html><body><h1>Authentication Complete</h1><p>You can return to your MCP client.</p></body></html>');
        resolver({ code, state });
        return;
      }
      res.writeHead(404);
      res.end('Not Found');
    } catch (e) {
      try { res.writeHead(500); res.end('Internal Server Error'); } catch {}
      debug.log('Auth callback error', e);
    }
  });

  const listen = (port: number): Promise<number> =>
    new Promise(resolve => {
      server.once('error', (err: any) => {
        if (err && err.code === 'EADDRINUSE') {
          debug.log('Port in use, retrying with random port');
          server.listen(0, opts.host, () => resolve((server.address() as any).port));
        } else {
          debug.log('Server listen error', err);
          // retry random port
          server.listen(0, opts.host, () => resolve((server.address() as any).port));
        }
      });
      server.listen(port, opts.host, () => resolve((server.address() as any).port));
    });

  const actualPort = await listen(opts.desiredPort);
  const url = `http://${opts.host}:${actualPort}/callback`;
  debug.log('Auth callback server started on', url, 'after', Math.round((Date.now() - started) / 1000), 's');

  // Set timeout to auto-resolve
  const timeout = setTimeout(() => {
    debug.log('Auth callback timeout reached');
    try { server.close(); } catch {}
    resolver(null);
  }, Math.max(5, opts.timeoutSec) * 1000);

  server.on('close', () => clearTimeout(timeout));

  return { server, port: actualPort, url, waitForCode };
}

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
    const hp = toBooleanEnv('HTTP_PROXY');
    const hps = toBooleanEnv('HTTPS_PROXY');
    const np = toBooleanEnv('NO_PROXY');
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
