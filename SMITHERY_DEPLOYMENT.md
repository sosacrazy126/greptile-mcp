# 🚀 Smithery Deployment Guide

## Overview

This guide explains how to deploy the Greptile MCP server on Smithery for streamable HTTP hosting.

## Current Status

The Greptile MCP server currently supports:
- ✅ SSE transport 
- ✅ STDIO transport
- ❌ Streamable HTTP (needed for optimal Smithery deployment)

## Deployment Steps

### 1. Add HTTP Transport Support

To deploy on Smithery, we need to implement streamable HTTP transport:

```python
# Add to src/main.py
from mcp.server.http import create_http_handler

async def run_http():
    """Run the MCP server with HTTP transport for Smithery"""
    handler = create_http_handler(mcp)
    
    # Smithery passes config as base64 query param
    @handler.route("/mcp")
    async def mcp_endpoint(request):
        config = request.query_params.get("config")
        if config:
            # Decode base64 config
            import base64
            config_json = base64.b64decode(config).decode('utf-8')
            # Apply configuration
        
        return await handler.handle_request(request)
    
    # Start HTTP server
    import uvicorn
    await uvicorn.run(handler, host="0.0.0.0", port=8080)
```

### 2. Update Configuration

```python
# Update main() in src/main.py
async def main():
    transport = os.getenv("TRANSPORT", "http")  # Default to HTTP
    
    if transport == 'http':
        await run_http()
    elif transport == 'sse':
        await mcp.run_sse_async()
    else:
        await mcp.run_stdio_async()
```

### 3. Handle Lazy Authentication

For Smithery tool listing, implement lazy loading:

```python
# Update src/utils.py
class GreptileClient:
    def __init__(self, api_key: str = None, github_token: str = None):
        # Delay authentication until needed
        self.api_key = api_key
        self.github_token = github_token
        self._client = None
    
    async def _ensure_authenticated(self):
        """Lazy load authentication"""
        if not self._client and self.api_key:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "X-GitHub-Token": self.github_token
                }
            )
```

### 4. Deploy Configuration

Create `smithery.json`:

```json
{
  "name": "greptile-mcp",
  "description": "Natural language code search and analysis",
  "transport": "http",
  "endpoint": "/mcp",
  "tools": {
    "public": ["greptile_help", "get_repository_info"],
    "authenticated": ["index_repository", "query_repository", "search_repository"]
  },
  "config": {
    "required": {
      "GREPTILE_API_KEY": {
        "type": "string",
        "description": "Your Greptile API key"
      },
      "GITHUB_TOKEN": {
        "type": "string", 
        "description": "GitHub personal access token"
      }
    }
  }
}
```

### 5. Deploy to Smithery

1. Add/claim server on Smithery
2. Go to Deployments tab  
3. Click Deploy
4. Server will be built and hosted

## Environment Variables

For Smithery deployment:

```env
TRANSPORT=http
HOST=0.0.0.0
PORT=8080
```

## Serverless Considerations

Since Smithery uses serverless hosting:

1. **Connection Timeout**: Handle reconnection after 2 min inactivity
2. **Ephemeral Storage**: Don't store state locally
3. **External Database**: Use for persistent data

## Client Configuration

Users connect via:

```json
{
  "mcpServers": {
    "greptile": {
      "url": "https://your-server.smithery.com/mcp",
      "transport": "http",
      "config": {
        "GREPTILE_API_KEY": "your-key",
        "GITHUB_TOKEN": "your-token"
      }
    }
  }
}
```

## Benefits of Smithery Deployment

- ✅ No infrastructure to manage
- ✅ Automatic scaling
- ✅ Global availability
- ✅ Built-in authentication
- ✅ Tool discovery

## Next Steps

1. Implement HTTP transport
2. Add lazy authentication
3. Test locally with HTTP
4. Deploy to Smithery
5. Update documentation
