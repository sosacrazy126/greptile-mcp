#!/usr/bin/env node

import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

function isValidUrl(u: string): boolean {
  try { new URL(u); return true; } catch { return false; }
}

async function tryFetch(url: string): Promise<{ ok: boolean; status: number; contentType?: string }> {
  try {
    const res = await fetch(url, { method: 'GET' });
    return { ok: res.ok, status: res.status, contentType: res.headers.get('content-type') || undefined };
  } catch {
    return { ok: false, status: 0 };
  }
}

async function main() {
  const argv = await yargs(hideBin(process.argv))
    .scriptName('mcp-remote-client')
    .usage('$0 <server>')
    .positional('server', { type: 'string', describe: 'Remote MCP server URL (HTTP or SSE endpoint)', demandOption: true })
    .help()
    .strict()
    .parseAsync();

  const serverUrl = (argv.server as unknown as string).trim();
  if (!isValidUrl(serverUrl)) {
    console.error('Invalid URL');
    process.exit(2);
  }

  console.log('Testing remote MCP server at', serverUrl);
  const res = await tryFetch(serverUrl);
  if (res.ok) {
    console.log('Success:', res.status, res.contentType ? `content-type=${res.contentType}` : '');
    process.exit(0);
  } else {
    console.error('Request failed:', res.status);
    process.exit(1);
  }
}

main().catch(err => {
  console.error('Fatal:', err instanceof Error ? err.message : String(err));
  process.exit(1);
});
