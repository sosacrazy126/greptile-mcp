"""
Fixed Cloudflare Workers Python entry point for Greptile MCP Server.
"""

import json
import os
from typing import Dict, Any, List, Optional

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable."""
    return os.getenv(key, default)

def create_response(data: Any, success: bool = True) -> Dict[str, Any]:
    """Create standardized response."""
    return {
        "success": success,
        "data": data if success else None,
        "error": None if success else {"message": str(data)}
    }

async def make_api_request(url: str, method: str = "GET", headers: Dict[str, str] = None, data: Dict[str, Any] = None):
    """Make HTTP request using fetch API."""
    from js import fetch, Headers, JSON
    
    # Setup headers
    js_headers = Headers.new()
    if headers:
        for key, value in headers.items():
            js_headers.set(key, value)
    
    # Setup request options
    options = {
        "method": method,
        "headers": js_headers
    }
    
    if data and method in ["POST", "PUT", "PATCH"]:
        options["body"] = JSON.stringify(data)
    
    # Make request
    response = await fetch(url, options)
    
    if not response.ok:
        raise Exception(f"HTTP {response.status}")
    
    response_text = await response.text()
    return json.loads(response_text)

async def handle_mcp_tools(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tool requests."""
    api_key = get_env_var("GREPTILE_API_KEY")
    github_token = get_env_var("GITHUB_TOKEN")
    base_url = get_env_var("GREPTILE_BASE_URL", "https://api.greptile.com/v2")
    
    if not api_key or not github_token:
        return create_response("Missing API credentials", False)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-GitHub-Token": github_token,
        "Content-Type": "application/json"
    }
    
    try:
        if method == "index_repository":
            url = f"{base_url}/repositories"
            result = await make_api_request(url, "POST", headers, params)
            return create_response(result)
            
        elif method == "query_repository":
            url = f"{base_url}/query"
            query = params.get("query", "")
            repositories = params.get("repositories", [])
            messages = [{"role": "user", "content": query}]
            
            payload = {
                "messages": messages,
                "repositories": repositories,
                "stream": False,
                "genius": params.get("genius", True)
            }
            
            result = await make_api_request(url, "POST", headers, payload)
            return create_response(result)
            
        elif method == "search_repository":
            url = f"{base_url}/search"
            query = params.get("query", "")
            repositories = params.get("repositories", [])
            messages = [{"role": "user", "content": query}]
            
            payload = {
                "messages": messages,
                "repositories": repositories,
                "genius": params.get("genius", True)
            }
            
            result = await make_api_request(url, "POST", headers, payload)
            return create_response(result)
            
        elif method == "get_repository_info":
            remote = params.get("remote")
            repository = params.get("repository")
            branch = params.get("branch")
            
            if not all([remote, repository, branch]):
                return create_response("Missing required parameters", False)
            
            import urllib.parse
            repo_id = f"{remote}:{branch}:{repository}"
            encoded_id = urllib.parse.quote_plus(repo_id, safe='')
            url = f"{base_url}/repositories/{encoded_id}"
            
            result = await make_api_request(url, "GET", headers)
            return create_response(result)
            
        else:
            return create_response(f"Unknown method: {method}", False)
            
    except Exception as e:
        return create_response(f"Error: {str(e)}", False)

async def on_fetch(request):
    """Main entry point for Cloudflare Workers."""
    from js import Response, Headers, JSON
    
    try:
        # Parse request URL
        url = request.url
        method = request.method
        
        # Simple path extraction
        if "/health" in url or url.endswith("/"):
            # Health check
            health_data = {
                "status": "healthy",
                "service": "greptile-mcp-server",
                "version": "1.0.0",
                "deployment": "cloudflare-workers"
            }
            
            headers = Headers.new()
            headers.set("Content-Type", "application/json")
            headers.set("Access-Control-Allow-Origin", "*")
            
            return Response.new(
                JSON.stringify(health_data),
                status=200,
                headers=headers
            )
        
        # Handle OPTIONS (CORS preflight)
        if method == "OPTIONS":
            headers = Headers.new()
            headers.set("Access-Control-Allow-Origin", "*")
            headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization")
            
            return Response.new("", status=200, headers=headers)
        
        # MCP endpoints
        if ("/sse" in url or "/mcp" in url):
            if method == "POST":
                # Handle MCP tool requests
                body_text = await request.text()
                request_data = json.loads(body_text) if body_text else {}
                
                tool_method = request_data.get("method")
                params = request_data.get("params", {})
                
                if not tool_method:
                    result = create_response("Missing 'method' in request", False)
                else:
                    result = await handle_mcp_tools(tool_method, params)
                
                headers = Headers.new()
                headers.set("Content-Type", "application/json")
                headers.set("Access-Control-Allow-Origin", "*")
                
                status = 200 if result.get("success") else 400
                return Response.new(JSON.stringify(result), status=status, headers=headers)
            
            elif method == "GET":
                # Server info
                server_info = {
                    "name": "greptile-mcp-server",
                    "version": "1.0.0",
                    "tools": ["index_repository", "query_repository", "search_repository", "get_repository_info"],
                    "endpoints": {
                        "/health": "Health check", 
                        "/sse": "MCP endpoint", 
                        "/mcp": "MCP endpoint"
                    }
                }
                
                headers = Headers.new()
                headers.set("Content-Type", "application/json")
                headers.set("Access-Control-Allow-Origin", "*")
                
                return Response.new(JSON.stringify(server_info), status=200, headers=headers)
        
        # Unknown endpoint
        headers = Headers.new()
        headers.set("Content-Type", "application/json")
        headers.set("Access-Control-Allow-Origin", "*")
        
        error_response = create_response("Unknown endpoint", False)
        return Response.new(JSON.stringify(error_response), status=404, headers=headers)
        
    except Exception as e:
        # Error handling
        headers = Headers.new()
        headers.set("Content-Type", "application/json")
        headers.set("Access-Control-Allow-Origin", "*")
        
        error_response = create_response(f"Internal error: {str(e)}", False)
        return Response.new(JSON.stringify(error_response), status=500, headers=headers)

# Export for Cloudflare Workers
export = {"fetch": on_fetch}