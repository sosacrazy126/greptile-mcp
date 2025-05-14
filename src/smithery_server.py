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

from src.main import mcp as greptile_mcp, greptile_lifespan, GreptileContext
from src.utils import get_greptile_client

# Create FastAPI app
app = FastAPI()

# Global state
mcp_context: Optional[GreptileContext] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of the Greptile MCP server"""
    global mcp_context
    
    # Initialize the Greptile context
    async with greptile_lifespan(greptile_mcp) as context:
        mcp_context = context
        yield
        mcp_context = None

# Update app with lifespan
app = FastAPI(lifespan=lifespan)

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

def list_tools_response():
    """Helper function to construct the tools list response for /mcp and /tools endpoints."""
    # Get tool information from the MCP server
    tools = []
    for tool_name, tool_func in greptile_mcp.tools.items():
        # Extract tool metadata
        tool_info = {
            "name": tool_name,
            "description": tool_func.__doc__.strip() if tool_func.__doc__ else "",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        # Extract parameters from function signature
        import inspect
        sig = inspect.signature(tool_func)
        for param_name, param in sig.parameters.items():
            if param_name == 'ctx':  # Skip context parameter
                continue
            # Add parameter to schema
            param_type = "string"  # Default type
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == list:
                    param_type = "array"
                elif param.annotation == dict:
                    param_type = "object"
            tool_info["inputSchema"]["properties"][param_name] = {
                "type": param_type,
                "description": ""  # Would need to extract from docstring
            }
            # Mark required parameters
            if param.default == inspect.Parameter.empty:
                tool_info["inputSchema"]["required"].append(param_name)
        tools.append(tool_info)
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
    # Parse config but don't require it for listing tools
    # (Kept for compatibility, but config is not used in listing)
    return list_tools_response()

@app.get("/tools")
async def tools_list_get(request: Request):
    """
    Handle GET request for /tools endpoint - list available tools.
    This endpoint doesn't require authentication (lazy loading).
    """
    # Support the same as /mcp for compatibility
    return list_tools_response()

@app.post("/tools")
async def tools_list_post(request: Request):
    """
    Handle POST request for /tools endpoint - list available tools.
    Accepts an empty JSON body or config, compatible with Smithery orchestrator.
    """
    return list_tools_response()

@app.post("/mcp")
async def mcp_execute_tool(request: Request):
    """Handle POST request for MCP endpoint - execute tools"""
    global mcp_context
    
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
    
    if method != 'tools/call':
        return JSONResponse(
            content={"error": f"Unsupported method: {method}"},
            status_code=400
        )
    
    # Extract tool call parameters
    params = body.get('params', {})
    tool_name = params.get('name')
    tool_args = params.get('arguments', {})
    
    # Validate tool exists
    if tool_name not in greptile_mcp.tools:
        return JSONResponse(
            content={"error": f"Tool '{tool_name}' not found"},
            status_code=404
        )
    
    # Check for required API keys only when executing tools
    if not os.getenv('GREPTILE_API_KEY') or not os.getenv('GITHUB_TOKEN'):
        return JSONResponse(
            content={
                "error": "API keys required for tool execution",
                "detail": "Please provide GREPTILE_API_KEY and GITHUB_TOKEN in configuration"
            },
            status_code=401
        )
    
    # Initialize Greptile client if not already done
    if not mcp_context or not mcp_context.initialized:
        try:
            greptile_client = get_greptile_client()
            mcp_context = GreptileContext(
                greptile_client=greptile_client,
                initialized=True
            )
        except Exception as e:
            return JSONResponse(
                content={"error": f"Failed to initialize Greptile client: {str(e)}"},
                status_code=500
            )
    
    # Create context for tool execution
    class MockContext:
        def __init__(self, greptile_context):
            self.request_context = type('RequestContext', (), {
                'lifespan_context': greptile_context
            })()
    
    ctx = MockContext(mcp_context)
    
    # Execute the tool
    try:
        tool_func = greptile_mcp.tools[tool_name]
        result = await tool_func(ctx, **tool_args)
        
        # Format response
        return {
            "id": body.get('id'),
            "result": result
        }
    except Exception as e:
        return JSONResponse(
            content={
                "error": f"Tool execution failed: {str(e)}",
                "tool": tool_name,
                "args": tool_args
            },
            status_code=500
        )

@app.delete("/mcp")
async def mcp_cleanup(request: Request):
    """Handle DELETE request for MCP endpoint - cleanup resources"""
    global mcp_context
    
    if mcp_context and hasattr(mcp_context, 'greptile_client'):
        try:
            await mcp_context.greptile_client.aclose()
        except Exception:
            pass
    
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
