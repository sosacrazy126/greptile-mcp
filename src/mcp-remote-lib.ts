import { createHash } from 'crypto';
import os from 'os';
import fs from 'fs';
import path from 'path';
import http from 'http';

export interface ParsedHeader {
  key: string;
  value: string;
}

export interface IgnoreRule {
  pattern: string;
  regex: RegExp;
}

export function ensureDirExists(dir: string): void {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

export function sha256Hex(input: string): string {
  return createHash('sha256').update(input).digest('hex');
}

export function getConfigDir(): string {
  const base = process.env.MCP_REMOTE_CONFIG_DIR || path.join(os.homedir(), '.mcp-auth');
  ensureDirExists(base);
  return base;
}

export function makeDebugLogger(serverUrl: string, enabled: boolean) {
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

export function parseHeader(h: string): ParsedHeader | null {
  const idx = h.indexOf(':');
  if (idx === -1) return null;
  const key = h.slice(0, idx).trim();
  const value = h.slice(idx + 1).trim();
  if (!key) return null;
  return { key, value };
}

export function buildHeaders(headers?: string[]): Record<string, string> {
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

export function wildcardToRegex(pattern: string): RegExp {
  const escaped = pattern.replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*');
  return new RegExp(`^${escaped}$`);
}

export function buildIgnoreRules(patterns?: string[]): IgnoreRule[] {
  return (patterns || []).map(p => ({ pattern: p, regex: wildcardToRegex(p) }));
}

export function isHttpsUrl(url: string): boolean {
  try {
    const u = new URL(url);
    return u.protocol === 'https:';
  } catch {
    return false;
  }
}

export function isHttpUrl(url: string): boolean {
  try {
    const u = new URL(url);
    return u.protocol === 'http:';
  } catch {
    return false;
  }
}

export async function maybeLoadJsonArg(input?: string): Promise<unknown | undefined> {
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

export async function startAuthCallbackServer(opts: {
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
          server.listen(0, opts.host, () => resolve((server.address() as any).port));
        }
      });
      server.listen(port, opts.host, () => resolve((server.address() as any).port));
    });

  const actualPort = await listen(opts.desiredPort);
  const url = `http://${opts.host}:${actualPort}/callback`;
  debug.log('Auth callback server started on', url, 'after', Math.round((Date.now() - started) / 1000), 's');

  const timeout = setTimeout(() => {
    debug.log('Auth callback timeout reached');
    try { server.close(); } catch {}
    resolver(null);
  }, Math.max(5, opts.timeoutSec) * 1000);

  server.on('close', () => clearTimeout(timeout));

  return { server, port: actualPort, url, waitForCode };
}
