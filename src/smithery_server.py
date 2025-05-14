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

# Create FastAPI app (without custom lifespan event)
app = FastAPI()

async def parse_config(config_b64: Optional[str]) -> Dict[str, Any]:
    """Parse and apply configuration from base64-encoded query parameter"""
    if not config_b64:
        return {}
    
    try:
        config_json = base64.b64decode(config_b64).decode('utf-8')
        config = json.loads(config_json)
        
        # Apply configuration to environment variables
        for key, value in config.items():
            os.environ[key] = str(value)
        
        return config
    except Exception as e:
        print(f"Error parsing config: {e}")
        return {}

async def list_tools_response():
    """Helper function to construct the tools list response for /mcp and /tools endpoints."""
    # Use the FastMCP's list_tools method which is async
    tool_list = await greptile_mcp.list_tools()
    
    # Convert the Tool objects to the format expected by Smithery
    tools = []
    for tool in tool_list:
        tool_data = {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema
        }
        tools.append(tool_data)
    
    return {
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False
        },
        "tools": tools
    }

@app.get("/mcp")
async def mcp_list_tools(request: Request):
    """
    Handle GET request for MCP endpoint - list available tools.
    This endpoint doesn't require authentication (lazy loading).
    """
    return await list_tools_response()

@app.get("/tools")
async def tools_list_get(request: Request):
    """
    Handle GET request for /tools endpoint - list available tools.
    This endpoint doesn't require authentication (lazy loading).
    """
    return await list_tools_response()

@app.post("/tools")
async def tools_list_post(request: Request):
    """
    Handle POST request for /tools endpoint - list available tools.
    Accepts an empty JSON body or config, compatible with Smithery orchestrator.
    """
    return await list_tools_response()

@app.post("/mcp")
async def mcp_execute_tool(request: Request):
    """Handle POST request for MCP endpoint - execute tools"""
    # Parse config from query parameter
    query_params = parse_qs(str(request.url.query))
    config_b64 = query_params.get('config', [None])[0]
    config = await parse_config(config_b64)

    # Parse request body
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    method = body.get('method')
    request_id = body.get('id')

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

    # Validate tool exists through tool_manager
    tool_manager = greptile_mcp._tool_manager
    if tool_name not in tool_manager._tools:
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

    # Create context for tool execution
    class MockContext:
        def __init__(self, greptile_context):
            self.request_context = type('RequestContext', (), {
                'lifespan_context': greptile_context
            })()

    ctx = MockContext(greptile_context)

    # Execute the tool
    try:
        # Use the MCP server's internal tool manager directly
        tool_manager = greptile_mcp._tool_manager
        tool_info = tool_manager._tools[tool_name]
        
        # Create a mock context that's compatible with FastMCP
        class MockContext:
            def __init__(self, greptile_context):
                self.request_context = type('RequestContext', (), {
                    'lifespan_context': greptile_context
                })()
        
        ctx = MockContext(greptile_context)
        
        # Call the function directly with our context
        tool_func = tool_info.fn
        if tool_info.is_async:
            result = await tool_func(ctx, **tool_args)
        else:
            result = tool_func(ctx, **tool_args)
        
        # Convert result to proper format if needed
        if hasattr(result, '__iter__') and not isinstance(result, str):
            # It's a list of content items
            content_list = list(result)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": content_list
            }
        elif isinstance(result, str):
            # It's a direct string result
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": [{"type": "text", "text": result}]
            }
        else:
            # Return as is
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
    # If you have a global context, clean up here, but now it's per-request
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
    port = int(os.getenv("PORT", "8088"))
    uvicorn.run(app, host="0.0.0.0", port=port)
