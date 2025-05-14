# Greptile MCP - Local Usage Guide

## How It Works

Greptile MCP is a Model Context Protocol (MCP) server that provides tools for searching and analyzing code repositories using natural language. It can run in two modes:

### 1. SSE Mode (for Desktop Applications)
When using with Claude Desktop or other MCP-compatible clients, the server runs in SSE (Server-Sent Events) mode. The application directly calls tools without needing a persistent server.

### 2. HTTP Mode (for Web/Smithery Deployment)  
For web deployments like Smithery, it runs as an HTTP server that must stay running to handle tool requests.

## Setup

1. Run the setup script:
   ```bash
   ./setup_local.sh
   ```

2. Configure your API keys in `.env`:
   ```
   GREPTILE_API_KEY=your_greptile_api_key_here
   GITHUB_TOKEN=your_github_token_here
   ```

## Running the Server

### For Desktop Use (SSE Mode)
```bash
source .venv/bin/activate
python -m src.main
```

This mode is used when integrating with Claude Desktop. The server handles tool calls directly without needing to maintain a persistent connection.

### For Web/API Use (HTTP Mode)
```bash
source .venv/bin/activate
python -m src.smithery_server
```

This starts an HTTP server on port 8080 that handles MCP requests via HTTP endpoints.

## Using with Claude Desktop

1. Copy the template configuration:
   ```bash
   cp claude_desktop_config_template.json claude_desktop_config.json
   ```

2. Edit `claude_desktop_config.json` to add your actual API keys

3. Add this configuration to your Claude Desktop config (usually `~/.config/claude/claude.json`):

```json
{
  "mcpServers": {
    "greptile": {
      "command": "/path/to/grep-mcp/.venv/bin/python",
      "args": ["-m", "src.main"],
      "env": {
        "GREPTILE_API_KEY": "your_key",
        "GITHUB_TOKEN": "your_token"
      }
    }
  }
}
```

## Common Issues

1. **Import Error for GreptileClient**: Make sure you've activated the virtual environment and installed dependencies.

2. **API Key Errors**: Ensure your `.env` file has valid API keys.

3. **Server Won't Start**: Check that the port (8050 for SSE, 8080 for HTTP) is not already in use.

## Environment Variables

- `GREPTILE_API_KEY`: Your Greptile API key (required)
- `GITHUB_TOKEN`: GitHub personal access token (required)
- `GREPTILE_BASE_URL`: API base URL (optional, defaults to https://api.greptile.com/v2)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8050 for SSE, 8080 for HTTP)
- `TRANSPORT`: Transport mode - "sse" or "http" (default: sse)
