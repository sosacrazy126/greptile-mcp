import { expect } from 'chai';
import { describe, it } from 'mocha';
import {
  parseHeader,
  buildHeaders,
  wildcardToRegex,
  buildIgnoreRules,
  isHttpsUrl,
  isHttpUrl,
  maybeLoadJsonArg,
  startAuthCallbackServer,
  makeDebugLogger,
  getConfigDir,
  sha256Hex,
} from '../../src/mcp-remote-lib.js';
import fs from 'fs';
import os from 'os';
import path from 'path';

describe('mcp-remote-lib', () => {
  it('parseHeader should parse key/value pairs and handle malformed', () => {
    expect(parseHeader('Authorization: Bearer token')).to.deep.equal({ key: 'Authorization', value: 'Bearer token' });
    expect(parseHeader('X-Foo:Bar')).to.deep.equal({ key: 'X-Foo', value: 'Bar' });
    expect(parseHeader('NoColonHere')).to.equal(null);
    expect(parseHeader(': onlyvalue')).to.equal(null);
  });

  it('buildHeaders should convert arrays to a header object', () => {
    const headers = buildHeaders([
      'Authorization: Bearer abc',
      'X-Test: 123',
    ]);
    expect(headers).to.have.property('Authorization', 'Bearer abc');
    expect(headers).to.have.property('X-Test', '123');
  });

  it('wildcardToRegex should support * patterns', () => {
    const rx1 = wildcardToRegex('delete*');
    expect(rx1.test('deleteTask')).to.be.true;
    expect(rx1.test('TaskDelete')).to.be.false;

    const rx2 = wildcardToRegex('*account');
    expect(rx2.test('getaccount')).to.be.true;
    expect(rx2.test('accounting')).to.be.false;

    const rx3 = wildcardToRegex('exactTool');
    expect(rx3.test('exactTool')).to.be.true;
    expect(rx3.test('exactToolX')).to.be.false;
  });

  it('buildIgnoreRules should compile patterns', () => {
    const rules = buildIgnoreRules(['delete*', '*account']);
    expect(rules).to.have.length(2);
    expect(rules[0].regex.test('deleteSomething')).to.be.true;
    expect(rules[1].regex.test('useraccount')).to.be.true;
  });

  it('URL helpers should validate http/https', () => {
    expect(isHttpsUrl('https://example.com')).to.be.true;
    expect(isHttpsUrl('http://example.com')).to.be.false;
    expect(isHttpUrl('http://example.com')).to.be.true;
    expect(isHttpUrl('https://example.com')).to.be.false;
    expect(isHttpUrl('notaurl')).to.be.false;
  });

  it('maybeLoadJsonArg should parse JSON or @file', async () => {
    const obj = (await maybeLoadJsonArg('{"a":1}')) as any;
    expect(obj).to.deep.equal({ a: 1 });

    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'mcp-remote-test-'));
    const file = path.join(tmpDir, 'meta.json');
    fs.writeFileSync(file, '{"x": "y"}', 'utf8');
    const fromFile = (await maybeLoadJsonArg(`@${file}`)) as any;
    expect(fromFile).to.deep.equal({ x: 'y' });
  });

  it('startAuthCallbackServer should capture code via /callback and resolve', async () => {
    const dbg = makeDebugLogger('https://example.com/sse', false);
    const { server, port, url, waitForCode } = await startAuthCallbackServer({
      host: '127.0.0.1',
      desiredPort: 0,
      timeoutSec: 10,
      debugLog: dbg,
    });

    // simulate browser redirect
    const callbackUrl = `http://127.0.0.1:${port}/callback?code=abc123&state=xyz`;
    const res = await fetch(callbackUrl);
    expect(res.status).to.equal(200);

    const data = await waitForCode();
    expect(data).to.deep.equal({ code: 'abc123', state: 'xyz' });
    server.close();
  });

  it('makeDebugLogger should create a log file in config dir', () => {
    const dbg = makeDebugLogger('https://logtest.example', true);
    const msg = `test-${Date.now()}`;
    dbg.log(msg);
    const dir = getConfigDir();
    const files = fs.readdirSync(dir).filter(f => f.endsWith('_debug.log'));
    expect(files.length).to.be.greaterThan(0);
  });

  it('sha256Hex should produce stable hash', () => {
    const a = sha256Hex('hello');
    const b = sha256Hex('hello');
    expect(a).to.equal(b);
    expect(a).to.match(/^[a-f0-9]{64}$/);
  });
});
