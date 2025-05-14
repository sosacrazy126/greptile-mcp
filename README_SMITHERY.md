# Greptile MCP Server - Smithery Deployment

This repository contains a Smithery-compatible MCP server for natural language code search and analysis using Greptile.

## Features

- 🔍 Natural language code search across multiple repositories
- 📊 Compare implementations across different codebases
- 🤖 AI-powered code understanding and analysis
- 🚀 Lazy loading for better Smithery integration
- 🔐 Secure API key handling

## Smithery Deployment

This server is designed to be deployed on Smithery with HTTP transport.

### Configuration

The server requires the following configuration:

- `GREPTILE_API_KEY`: Your Greptile API key
- `GITHUB_TOKEN`: GitHub personal access token for repository access

### Endpoints

- `/mcp` - Main MCP protocol endpoint (GET, POST, DELETE)
- `/health` - Health check endpoint
- `/` - Service information

### Features

1. **Lazy Loading**: Tool listing doesn't require API keys, allowing Smithery to display available tools
2. **HTTP Transport**: Native HTTP implementation for better performance
3. **Stateless Design**: Suitable for serverless environments
4. **2-minute Timeout Handling**: Designed for Smithery's connection timeout

## Usage

Once deployed on Smithery, you can:

1. List available tools without authentication
2. Execute tools by providing required API keys in configuration
3. Index repositories for searching
4. Query code using natural language
5. Compare implementations across repositories

## Tools Available

- `greptile_help`: Get comprehensive documentation
- `index_repository`: Index a repository for searching
- `query_repository`: Query repositories with natural language
- `search_repository`: Search for code patterns
- `compare_repositories`: Compare implementations
- `get_repository_info`: Check repository status

## Development

For local development:

```bash
# Install dependencies
pip install -e .

# Run the HTTP server
python -m src.smithery_server
```

## License

MIT
