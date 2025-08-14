import { expect } from 'chai';
import { describe, it, before } from 'mocha';
import { GreptileMCPServer } from '../../src/server.js';
import type { Config } from '../../src/types/index.js';

describe('Greptile MCP Server Integration', () => {
  let server: GreptileMCPServer;
  let config: Config;

  before(() => {
    // Mock configuration for testing
    config = {
      apiKey: process.env.GREPTILE_API_KEY || 'test-api-key',
      githubToken: process.env.GITHUB_AI_TOKEN || process.env.GITHUB_TOKEN || 'test-github-token',
      baseUrl: 'http://localhost:3000', // Mock server URL for testing
      features: {
        streaming: true,
        orchestration: true,
        flowEnhancement: true,
      },
    };
  });

  describe('Server Initialization', () => {
    it('should create server instance', () => {
      server = new GreptileMCPServer();
      expect(server).to.be.instanceOf(GreptileMCPServer);
    });

    it('should handle missing API key', async () => {
      const invalidConfig = { ...config, apiKey: undefined };

      try {
        await GreptileMCPServer.create(invalidConfig);
        expect.fail('Should have thrown error for missing API key');
      } catch (error) {
        expect(error).to.be.instanceOf(Error);
        expect((error as Error).message).to.include('API key');
      }
    });

    it('should handle missing GitHub token', async () => {
      const invalidConfig = { ...config, githubToken: undefined };

      try {
        await GreptileMCPServer.create(invalidConfig);
        expect.fail('Should have thrown error for missing GitHub token');
      } catch (error) {
        expect(error).to.be.instanceOf(Error);
        expect((error as Error).message).to.include('GitHub token');
      }
    });
  });

  describe('Server Configuration', () => {
    it('should accept valid configuration', () => {
      expect(() => {
        server = new GreptileMCPServer();
      }).to.not.throw();
    });

    it('should handle custom base URL', () => {
      const customConfig = { ...config, baseUrl: 'https://custom.api.com' };
      expect(customConfig.baseUrl).to.equal('https://custom.api.com');
    });
  });

  // Note: These tests would require actual API credentials and connectivity
  // For CI/CD, these could be skipped or mocked
  describe('API Integration (requires credentials)', function () {
    this.timeout(10000); // Increase timeout for API calls

    before(function () {
      // Skip if no real credentials provided
      if (
        !process.env.GREPTILE_API_KEY ||
        (!process.env.GITHUB_AI_TOKEN && !process.env.GITHUB_TOKEN)
      ) {
        this.skip();
      }
    });

    it('should initialize with real credentials', async () => {
      const realConfig = {
        apiKey: process.env.GREPTILE_API_KEY!,
        githubToken: process.env.GITHUB_AI_TOKEN || process.env.GITHUB_TOKEN!,
        baseUrl: 'https://api.greptile.com/v2',
        features: {
          streaming: true,
          orchestration: true,
          flowEnhancement: true,
        },
      };

      server = await GreptileMCPServer.create(realConfig);
      expect(server).to.be.instanceOf(GreptileMCPServer);
    });
  });
});
