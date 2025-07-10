# Smithery Integration Analysis & Fix

## Issue Summary

Your Greptile MCP server is successfully deploying to Smithery, but when Smithery tries to scan for tools, it gets a timeout error:

```
Deployment successful.
Scanning for tools...
Failed to scan tools list from server: McpError: MCP error -32001: Request timed out

Please ensure your server performs lazy loading of configurations: https://smithery.ai/docs/build/deployments#tool-lists
```

## Root Cause

The issue is in `src/smithery_server.py` in the tool listing endpoints (`/mcp` GET and `/tools` GET/POST). These endpoints are currently trying to initialize the Greptile client and context during tool listing, which:

1. **Requires API keys** - but Smithery needs to list tools before authentication
2. **Takes too long** - causing the timeout error
3. **Violates lazy loading principle** - Smithery expects tool listing to work without authentication

## Current Problematic Code

In `src/smithery_server.py`, the `list_tools_response()` function calls:

```python
async def list_tools_response():
    # This line is problematic - it tries to initialize everything
    tool_list = await greptile_mcp.list_tools()  
    # ... rest of function
```

The `greptile_mcp.list_tools()` call triggers full initialization, including Greptile client setup, which requires API keys and can timeout.

## Solution

The fix is to implement **lazy loading** by separating tool metadata (which should be available immediately) from tool execution (which requires authentication).

## Fixed Implementation

Here's the corrected `smithery_server.py`:

```python
"""
Smithery-compatible HTTP server for Greptile MCP
"""
import base64
import json
import os
from typing import Optional, Dict, Any
from urllib.parse import parse_qs

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
from contextlib import asynccontextmanager
import asyncio

# Import only the tool definitions/metadata, not the context or lifespan
from src.main import mcp as greptile_mcp, GreptileContext
from src.utils import get_greptile_client

# Create FastAPI app
app = FastAPI()

# Static tool definitions for lazy loading (no authentication required)
STATIC_TOOLS = [
    {
        "name": "greptile_help",
        "description": "Get comprehensive documentation on using Greptile MCP",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "index_repository",
        "description": "Index a repository to make it searchable",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository URL or identifier (e.g., owner/repo)"
                },
                "branch": {
                    "type": "string",
                    "description": "Branch to index (optional, defaults to main/master)"
                },
                "force_reindex": {
                    "type": "boolean",
                    "description": "Force re-indexing if already indexed (optional)"
                }
            },
            "required": ["repository"]
        }
    },
    {
        "name": "query_repository",
        "description": "Query repositories with natural language",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query to search for"
                },
                "repositories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of repository identifiers to search in"
                },
                "file_types": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "File extensions to filter by (optional)"
                }
            },
            "required": ["query", "repositories"]
        }
    },
    {
        "name": "search_repository",
        "description": "Search for code patterns across repositories",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Code pattern or regex to search for"
                },
                "repositories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of repository identifiers to search in"
                },
                "file_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File extensions to filter by (optional)"
                }
            },
            "required": ["pattern", "repositories"]
        }
    },
    {
        "name": "compare_repositories",
        "description": "Compare implementations across repositories",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repositories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of repository identifiers to compare"
                },
                "feature": {
                    "type": "string",
                    "description": "Feature or functionality to compare"
                }
            },
            "required": ["repositories", "feature"]
        }
    },
    {
        "name": "get_repository_info",
        "description": "Check repository indexing status",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository identifier to check"
                }
            },
            "required": ["repository"]
        }
    }
]

async def parse_base64_config(config_b64: Optional[str]) -> Dict[str, Any]:
    """Parse and apply configuration from base64-encoded query parameter"""
    if not config_b64:
        return {}
    try:
        config_json = base64.b64decode(config_b64).decode('utf-8')
        config = json.loads(config_json)
        for key, value in config.items():
            os.environ[key] = str(value)
        return config
    except Exception as e:
        print(f"Error parsing config: {e}")
        return {}

def parse_dot_params(params: Dict[str, str]) -> Dict[str, Any]:
    """
    Convert dot-notation query params into dict.
    For now, just flatten key/values (no nesting).
    """
    return dict(params)

def merge_config_from_request(request: Request) -> Dict[str, Any]:
    """
    Merge config from query params and base64 config param. 
    Sets resulting values into os.environ (as string).
    """
    params = dict(request.query_params)
    config = {}

    # 1. Parse dot-notation query params
    config.update(parse_dot_params(params))

    # 2. Look for base64 config for backwards compatibility
    config_b64 = params.get("config")
    if config_b64:
        try:
            parsed = base64.b64decode(config_b64).decode('utf-8')
            config_dict = json.loads(parsed)
            config.update(config_dict)
        except Exception as e:
            print(f"Failed to parse base64 config: {e}")

    # 3. Set values in os.environ
    for k, v in config.items():
        os.environ[k] = str(v)
    return config

async def list_tools_response():
    """
    Helper function to construct the tools list response for /mcp and /tools endpoints.
    Uses static tool definitions for lazy loading - NO authentication required.
    """
    return {
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False
        },
        "tools": STATIC_TOOLS
    }

@app.get("/mcp")
async def mcp_list_tools(request: Request):
    """
    Handle GET request for MCP endpoint - list available tools.
    This endpoint doesn't require authentication (lazy loading).
    """
    merge_config_from_request(request)
    tools_response = await list_tools_response()
    query_params = dict(request.query_params)
    if 'id' in query_params:
        return {
            "jsonrpc": "2.0",
            "id": query_params.get('id'),
            "result": tools_response
        }
    return {
        "jsonrpc": "2.0",
        "result": tools_response
    }

@app.get("/tools")
async def tools_list_get(request: Request):
    """
    Handle GET request for /tools endpoint - list available tools.
    This endpoint doesn't require authentication (lazy loading).
    """
    merge_config_from_request(request)
    return await list_tools_response()

@app.post("/tools")
async def tools_list_post(request: Request):
    """
    Handle POST request for /tools endpoint - list available tools.
    Accepts an empty JSON body or config, compatible with Smithery orchestrator.
    """
    merge_config_from_request(request)
    return await list_tools_response()

@app.post("/mcp")
async def mcp_execute_tool(request: Request):
    """Handle POST request for MCP endpoint - execute tools"""
    merge_config_from_request(request)

    # Parse request body
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    method = body.get('method')
    request_id = body.get('id')

    # If no method provided, default to tools/list
    if not method:
        tools = await list_tools_response()
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": tools
        }

    # Handle initialize method
    if method == 'initialize':
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "0.1.0",
                "capabilities": {
                    "tools": True,
                    "resources": False
                },
                "serverInfo": {
                    "name": "greptile-mcp",
                    "version": "1.0.0"
                }
            }
        }

    # Handle tool listing method
    if method == 'tools/list':
        tools = await list_tools_response()
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": tools
        }

    if method != 'tools/call':
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Unsupported method: {method}"
                }
            },
            status_code=200  # JSON-RPC errors still return 200
        )

    # Extract tool call parameters
    params = body.get('params', {})
    tool_name = params.get('name')
    tool_args = params.get('arguments', {})
    request_id = body.get('id')

    # Validate tool exists in static tools list
    if tool_name not in [tool["name"] for tool in STATIC_TOOLS]:
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Tool '{tool_name}' not found"
                }
            },
            status_code=200  # JSON-RPC errors still return 200
        )

    # Check for required API keys only when executing tools
    if not os.getenv('GREPTILE_API_KEY') or not os.getenv('GITHUB_TOKEN'):
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": "API keys required for tool execution",
                    "data": {
                        "detail": "Please provide GREPTILE_API_KEY and GITHUB_TOKEN in configuration"
                    }
                }
            },
            status_code=200  # JSON-RPC errors still return 200
        )

    # Initialize Greptile client/context only now (lazy)
    try:
        greptile_client = get_greptile_client()
        greptile_context = GreptileContext(
            greptile_client=greptile_client,
            initialized=True
        )
    except Exception as e:
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Failed to initialize Greptile client: {str(e)}"
                }
            },
            status_code=200  # JSON-RPC errors still return 200
        )

    # Get the actual tool manager and execute the tool
    try:
        tool_manager = greptile_mcp._tool_manager
        if tool_name not in tool_manager._tools:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": f"Tool '{tool_name}' not found in tool manager"
                    }
                },
                status_code=200
            )

        # Create context for tool execution
        class MockContext:
            def __init__(self, greptile_context):
                self.request_context = type('RequestContext', (), {
                    'lifespan_context': greptile_context
                })()

        ctx = MockContext(greptile_context)

        # Execute the tool
        tool_info = tool_manager._tools[tool_name]
        tool_func = tool_info.fn
        if tool_info.is_async:
            result = await tool_func(ctx, **tool_args)
        else:
            result = tool_func(ctx, **tool_args)
        
        if hasattr(result, '__iter__') and not isinstance(result, str):
            content_list = list(result)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": content_list
            }
        elif isinstance(result, str):
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": [{"type": "text", "text": result}]
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
    except Exception as e:
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution failed: {str(e)}",
                    "data": {
                        "tool": tool_name,
                        "args": tool_args
                    }
                }
            },
            status_code=200  # JSON-RPC errors still return 200
        )

@app.delete("/mcp")
async def mcp_cleanup(request: Request):
    """Handle DELETE request for MCP endpoint - cleanup resources"""
    return {"status": "cleanup complete"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "greptile-mcp",
        "transport": "http"
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Greptile MCP Server",
        "version": "1.0.0",
        "description": "Natural language code search and analysis",
        "endpoints": {
            "/mcp": "MCP protocol endpoint",
            "/health": "Health check",
            "/": "Service information"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

## Key Changes Made

1. **Static Tool Definitions**: Added `STATIC_TOOLS` array with tool metadata that doesn't require authentication
2. **Lazy Loading**: Tool listing endpoints now use static definitions instead of calling `greptile_mcp.list_tools()`
3. **Authentication Only on Execution**: API keys are only checked when actually executing tools, not when listing them
4. **Fast Response**: Tool listing is now immediate since it doesn't initialize any external services

## Testing the Fix

1. **Deploy the Updated Code**: Replace your current `src/smithery_server.py` with the fixed version
2. **Redeploy to Smithery**: Push your changes and redeploy
3. **Verify Tool Scanning**: Smithery should now successfully scan and list your tools without timeout

## Benefits

- ✅ **Fast Tool Listing**: No authentication or initialization delays
- ✅ **Lazy Loading Compliance**: Follows Smithery's requirements
- ✅ **Secure Execution**: API keys still required for actual tool usage
- ✅ **Timeout Prevention**: Tool scanning completes quickly

This fix should resolve your timeout issue while maintaining the security and functionality of your MCP server.