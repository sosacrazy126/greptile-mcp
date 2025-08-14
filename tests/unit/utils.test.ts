import { expect } from 'chai';
import { describe, it } from 'mocha';
import {
  generateSessionId,
  normalizeSessionId,
  createErrorResponse,
  safeJsonParse,
  formatDuration,
  truncateString,
  parseRepositoryUrl,
  isValidUrl,
} from '../../src/utils/index.js';

describe('Utils', () => {
  describe('generateSessionId', () => {
    it('should generate a valid UUID', () => {
      const sessionId = generateSessionId();
      expect(sessionId).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);
    });

    it('should generate unique IDs', () => {
      const id1 = generateSessionId();
      const id2 = generateSessionId();
      expect(id1).to.not.equal(id2);
    });
  });

  describe('normalizeSessionId', () => {
    it('should normalize valid session ID', () => {
      const sessionId = 'ABC-123-DEF';
      const normalized = normalizeSessionId(sessionId);
      expect(normalized).to.equal('abc-123-def');
    });

    it('should return undefined for null/undefined input', () => {
      expect(normalizeSessionId(undefined)).to.be.undefined;
    });

    it('should handle empty string', () => {
      expect(normalizeSessionId('')).to.be.undefined;
    });

    it('should trim whitespace', () => {
      const normalized = normalizeSessionId('  abc-123  ');
      expect(normalized).to.equal('abc-123');
    });
  });

  describe('createErrorResponse', () => {
    it('should create basic error response', () => {
      const response = createErrorResponse('Test error');
      const parsed = JSON.parse(response);
      expect(parsed).to.deep.equal({
        error: 'Test error',
        type: 'Error',
      });
    });

    it('should include session ID when provided', () => {
      const response = createErrorResponse('Test error', 'ValidationError', 'session-123');
      const parsed = JSON.parse(response);
      expect(parsed).to.deep.equal({
        error: 'Test error',
        type: 'ValidationError',
        session_id: 'session-123',
      });
    });
  });

  describe('safeJsonParse', () => {
    it('should parse valid JSON', () => {
      const result = safeJsonParse('{"key": "value"}', {});
      expect(result).to.deep.equal({ key: 'value' });
    });

    it('should return fallback for invalid JSON', () => {
      const fallback = { default: true };
      const result = safeJsonParse('invalid json', fallback);
      expect(result).to.equal(fallback);
    });
  });

  describe('formatDuration', () => {
    it('should format seconds', () => {
      expect(formatDuration(30)).to.equal('30s');
      expect(formatDuration(45.7)).to.equal('46s');
    });

    it('should format minutes', () => {
      expect(formatDuration(90)).to.equal('2m');
      expect(formatDuration(150)).to.equal('3m');
    });

    it('should format hours and minutes', () => {
      expect(formatDuration(3600)).to.equal('1h 0m');
      expect(formatDuration(3900)).to.equal('1h 5m');
      expect(formatDuration(7380)).to.equal('2h 3m');
    });
  });

  describe('truncateString', () => {
    it('should not truncate short strings', () => {
      const result = truncateString('short', 10);
      expect(result).to.equal('short');
    });

    it('should truncate long strings', () => {
      const result = truncateString('this is a very long string', 10);
      expect(result).to.equal('this is...');
      expect(result).to.have.length(10);
    });

    it('should handle edge cases', () => {
      expect(truncateString('abc', 3)).to.equal('abc');
      expect(truncateString('abcd', 3)).to.equal('...');
    });
  });

  describe('isValidUrl', () => {
    it('should validate correct URLs', () => {
      expect(isValidUrl('https://github.com')).to.be.true;
      expect(isValidUrl('http://example.com')).to.be.true;
      expect(isValidUrl('https://api.greptile.com/v2')).to.be.true;
    });

    it('should reject invalid URLs', () => {
      expect(isValidUrl('not-a-url')).to.be.false;
      expect(isValidUrl('github.com')).to.be.false;
      expect(isValidUrl('')).to.be.false;
    });
  });

  describe('parseRepositoryUrl', () => {
    it('should parse GitHub URLs', () => {
      const result = parseRepositoryUrl('https://github.com/microsoft/vscode');
      expect(result).to.deep.equal({
        remote: 'github',
        repository: 'microsoft/vscode',
      });
    });

    it('should parse GitLab URLs', () => {
      const result = parseRepositoryUrl('https://gitlab.com/gitlab-org/gitlab');
      expect(result).to.deep.equal({
        remote: 'gitlab',
        repository: 'gitlab-org/gitlab',
      });
    });

    it('should handle URLs with additional paths', () => {
      const result = parseRepositoryUrl('https://github.com/microsoft/vscode/tree/main');
      expect(result).to.deep.equal({
        remote: 'github',
        repository: 'microsoft/vscode',
      });
    });

    it('should return null for invalid URLs', () => {
      expect(parseRepositoryUrl('not-a-url')).to.be.null;
      expect(parseRepositoryUrl('https://example.com/repo')).to.be.null;
      expect(parseRepositoryUrl('https://github.com/single')).to.be.null;
    });
  });
});
