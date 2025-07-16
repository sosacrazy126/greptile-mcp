"""
Smithery-compatible HTTP server for Greptile MCP
"""
import base64
import json
import os
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

# Import only the tool definitions/metadata, not the context or lifespan
from src.main import mcp as greptile_mcp
from src.utils import GreptileClient
from dataclasses import dataclass

# Simple context class for compatibility
@dataclass
class GreptileContext:
    """Simple context for the Greptile MCP server."""
    greptile_client: GreptileClient
    initialized: bool = False

# Create FastAPI app (without custom lifespan event)
app = FastAPI()

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
    """Helper function to construct the tools list response for /mcp and /tools endpoints."""
    print(f"[DEBUG] Starting tool discovery phase")
    
    try:
        # Use a timeout to ensure tool discovery doesn't hang
        import asyncio
        
        async def get_tools_with_timeout():
            return await greptile_mcp.get_tools()
        
        print(f"[DEBUG] Calling greptile_mcp.get_tools() with timeout")
        tools_dict = await asyncio.wait_for(get_tools_with_timeout(), timeout=10.0)
        print(f"[DEBUG] Retrieved {len(tools_dict)} tools")

        # Convert the Tool objects to the format expected by Smithery
        tools = []
        for tool_name, tool in tools_dict.items():
            print(f"[DEBUG] Processing tool: {tool_name}")
            tool_data = {
                "name": tool_name,
                "description": tool.description,
                "inputSchema": tool.parameters
            }
            tools.append(tool_data)
            print(f"[DEBUG] Added tool: {tool_name}")

        response = {
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": False
            },
            "tools": tools
        }
        
        print(f"[DEBUG] Tool discovery completed successfully with {len(tools)} tools")
        return response
        
    except asyncio.TimeoutError:
        print(f"[ERROR] Tool discovery timed out after 10 seconds")
        return await get_fallback_tools_response()
        
    except Exception as e:
        print(f"[ERROR] Tool discovery failed: {e}")
        import traceback
        traceback.print_exc()
        
        return await get_fallback_tools_response()

async def get_fallback_tools_response():
    """Fallback response when tool discovery fails."""
    print(f"[DEBUG] Using fallback tool definitions")
    
    # Define static tool definitions that don't require client initialization
    fallback_tools = [
        {
            "name": "index_repository",
            "description": "Index a repository for code search and querying",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "remote": {"type": "string", "description": "Repository host (github or gitlab)"},
                    "repository": {"type": "string", "description": "Repository in owner/repo format"},
                    "branch": {"type": "string", "description": "Branch to index"},
                    "reload": {"type": "boolean", "description": "Force reprocessing", "default": False},
                    "notify": {"type": "boolean", "description": "Send email notification", "default": False}
                },
                "required": ["remote", "repository", "branch"]
            }
        },
        {
            "name": "query_repository",
            "description": "Query repositories using natural language",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language query"},
                    "repositories": {"type": "string", "description": "JSON string of repositories"},
                    "session_id": {"type": "string", "description": "Session ID for continuity"},
                    "stream": {"type": "boolean", "description": "Enable streaming", "default": False},
                    "genius": {"type": "boolean", "description": "Use enhanced query", "default": True}
                },
                "required": ["query", "repositories"]
            }
        },
        {
            "name": "search_repository",
            "description": "Search repositories for relevant files",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "repositories": {"type": "string", "description": "JSON string of repositories"},
                    "session_id": {"type": "string", "description": "Session ID for continuity"},
                    "genius": {"type": "boolean", "description": "Use enhanced search", "default": True}
                },
                "required": ["query", "repositories"]
            }
        },
        {
            "name": "get_repository_info",
            "description": "Get information about an indexed repository",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "remote": {"type": "string", "description": "Repository host (github or gitlab)"},
                    "repository": {"type": "string", "description": "Repository in owner/repo format"},
                    "branch": {"type": "string", "description": "Branch that was indexed"}
                },
                "required": ["remote", "repository", "branch"]
            }
        },
        {
            "name": "greptile_help",
            "description": "Get comprehensive help and usage guidance",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "learning_level": {"type": "string", "description": "Learning level (beginner, intermediate, advanced)", "default": "beginner"},
                    "context_type": {"type": "string", "description": "Context type (discovery, patterns, workflows, integration)", "default": "discovery"},
                    "focus_area": {"type": "string", "description": "Focus area (general, architectural, consultation, session_management)", "default": "general"}
                }
            }
        }
    ]
    
    return {
        "capabilities": {
            "tools": True,
            "resources": True,
            "prompts": False
        },
        "tools": fallback_tools
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
        api_key = os.getenv("GREPTILE_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")
        
        if not api_key or not github_token:
            raise ValueError("Missing required environment variables: GREPTILE_API_KEY and GITHUB_TOKEN")
        
        greptile_client = GreptileClient(api_key, github_token)
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
        tool_manager = greptile_mcp._tool_manager
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
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
