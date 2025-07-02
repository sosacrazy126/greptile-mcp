"""
Cloudflare Workers Python entry point for Greptile MCP Server (Standard Library Only).

This module provides a remote MCP server implementation that runs on Cloudflare Workers
using only Python standard library modules, compatible with Workers Python runtime.
"""

import json
import os
import uuid
import urllib.parse
import urllib.request
from typing import Dict, Any, List, Optional

# Cloudflare Workers Python imports
from js import Request, Response, Headers, JSON, fetch, URL

# Simple session manager using only standard library
class SimpleSessionManager:
    """Simple in-memory session manager using only standard library."""
    
    def __init__(self):
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}
    
    async def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        return list(self.sessions.get(session_id, []))
    
    async def append_message(self, session_id: str, message: Dict[str, Any]) -> None:
        """Append a message to session history."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append(message)
    
    async def set_history(self, session_id: str, messages: List[Dict[str, Any]]) -> None:
        """Set the complete message history for a session."""
        self.sessions[session_id] = list(messages)
    
    async def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session."""
        self.sessions.pop(session_id, None)

def generate_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())

def get_environment_variable(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable that works in Cloudflare Workers."""
    try:
        from js import env
        if hasattr(env, key):
            return getattr(env, key)
    except:
        pass
    return os.getenv(key, default)

def create_success_response(data: Any) -> Dict[str, Any]:
    """Create a standardized success response."""
    return {
        "success": True,
        "data": data,
        "error": None
    }

def create_error_response(error_message: str, error_code: Optional[str] = None) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "success": False,
        "data": None,
        "error": {
            "message": error_message,
            "code": error_code or "UNKNOWN_ERROR"
        }
    }

class GreptileClient:
    """Simplified Greptile API client using standard library and fetch API."""
    
    def __init__(self, api_key: str, github_token: str, base_url: str = "https://api.greptile.com/v2"):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "X-GitHub-Token": github_token,
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, url: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request using Cloudflare Workers fetch API."""
        # Convert headers to JS Headers object
        js_headers = Headers.new()
        for key, value in self.headers.items():
            js_headers.set(key, value)
        
        # Prepare request options
        request_options = {
            "method": method,
            "headers": js_headers
        }
        
        if data:
            request_options["body"] = JSON.stringify(data)
        
        # Make the request
        response = await fetch(url, request_options)
        
        if not response.ok:
            error_text = await response.text()
            raise Exception(f"HTTP {response.status}: {error_text}")
        
        # Parse JSON response
        response_text = await response.text()
        return json.loads(response_text)
    
    async def index_repository(
        self, 
        remote: str, 
        repository: str, 
        branch: str, 
        reload: bool = True, 
        notify: bool = False
    ) -> Dict[str, Any]:
        """Index a repository for code search and querying."""
        url = f"{self.base_url}/repositories"
        payload = {
            "remote": remote,
            "repository": repository,
            "branch": branch,
            "reload": reload,
            "notify": notify
        }
        return await self._make_request("POST", url, payload)
    
    async def query_repositories(
        self,
        messages: List[Dict[str, Any]],
        repositories: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        stream: bool = False,
        genius: bool = True,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Query repositories to get answers with code references."""
        url = f"{self.base_url}/query"
        payload = {
            "messages": messages,
            "repositories": repositories,
            "stream": False,  # Streaming not supported in this simplified version
            "genius": genius
        }
        if session_id:
            payload["sessionId"] = session_id
        
        return await self._make_request("POST", url, payload)
    
    async def search_repositories(
        self,
        messages: List[Dict[str, Any]],
        repositories: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        genius: bool = True
    ) -> Dict[str, Any]:
        """Search repositories for relevant files."""
        url = f"{self.base_url}/search"
        payload = {
            "messages": messages,
            "repositories": repositories,
            "genius": genius
        }
        
        if session_id:
            payload["sessionId"] = session_id
        
        return await self._make_request("POST", url, payload)
    
    async def get_repository_info(self, repository_id: str) -> Dict[str, Any]:
        """Get information about an indexed repository."""
        encoded_id = urllib.parse.quote_plus(repository_id, safe='')
        url = f"{self.base_url}/repositories/{encoded_id}"
        return await self._make_request("GET", url)

class GreptileMCPWorker:
    """Main MCP server implementation for Cloudflare Workers."""
    
    def __init__(self):
        self.session_manager = SimpleSessionManager()
        
    def get_greptile_client(self) -> GreptileClient:
        """Create Greptile client using environment variables."""
        api_key = get_environment_variable("GREPTILE_API_KEY")
        github_token = get_environment_variable("GITHUB_TOKEN")
        base_url = get_environment_variable("GREPTILE_BASE_URL", "https://api.greptile.com/v2")
        
        if not api_key:
            raise ValueError("GREPTILE_API_KEY environment variable is required")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
            
        return GreptileClient(api_key, github_token, base_url)
    
    async def handle_mcp_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool requests."""
        try:
            if method == "index_repository":
                return await self.index_repository(**params)
            elif method == "query_repository":
                return await self.query_repository(**params)
            elif method == "search_repository":
                return await self.search_repository(**params)
            elif method == "get_repository_info":
                return await self.get_repository_info(**params)
            else:
                return create_error_response(f"Unknown method: {method}")
        except Exception as e:
            return create_error_response(f"Error in {method}: {str(e)}")
    
    async def index_repository(
        self, 
        remote: str, 
        repository: str, 
        branch: str, 
        reload: bool = True, 
        notify: bool = False
    ) -> Dict[str, Any]:
        """Index a repository for code search and querying."""
        try:
            greptile_client = self.get_greptile_client()
            result = await greptile_client.index_repository(remote, repository, branch, reload, notify)
            return create_success_response(result)
        except Exception as e:
            return create_error_response(f"Error indexing repository: {str(e)}")
    
    async def query_repository(
        self,
        query: str,
        repositories: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        stream: bool = False,
        genius: bool = True,
        timeout: Optional[float] = None,
        previous_messages: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Query repositories to get answers with code references."""
        try:
            greptile_client = self.get_greptile_client()
            
            # Session logic
            sid = session_id or generate_session_id()
            
            # Build message history
            if previous_messages is not None:
                messages = previous_messages + [{"role": "user", "content": query}]
                await self.session_manager.set_history(sid, messages)
            else:
                history = await self.session_manager.get_history(sid)
                messages = history + [{"role": "user", "content": query}]
                await self.session_manager.set_history(sid, messages)
            
            # Make the query
            result = await greptile_client.query_repositories(
                messages, repositories, session_id=sid, stream=False, genius=genius, timeout=timeout
            )
            
            # Persist session history
            if "messages" in result:
                await self.session_manager.set_history(sid, result["messages"])
            elif "output" in result:
                await self.session_manager.append_message(sid, {"role": "assistant", "content": result["output"]})
            
            result["_session_id"] = sid
            return create_success_response(result)
            
        except Exception as e:
            return create_error_response(f"Error querying repositories: {str(e)}")
    
    async def search_repository(
        self, 
        query: str, 
        repositories: List[Dict[str, Any]], 
        session_id: Optional[str] = None, 
        genius: bool = True
    ) -> Dict[str, Any]:
        """Search repositories for relevant files without generating a full answer."""
        try:
            greptile_client = self.get_greptile_client()
            messages = [{"role": "user", "content": query}]
            result = await greptile_client.search_repositories(messages, repositories, session_id, genius)
            return create_success_response(result)
        except Exception as e:
            return create_error_response(f"Error searching repositories: {str(e)}")
    
    async def get_repository_info(self, remote: str, repository: str, branch: str) -> Dict[str, Any]:
        """Get information about an indexed repository."""
        try:
            greptile_client = self.get_greptile_client()
            repository_id = f"{remote}:{branch}:{repository}"
            result = await greptile_client.get_repository_info(repository_id)
            return create_success_response(result)
        except Exception as e:
            return create_error_response(f"Error getting repository info: {str(e)}")

# Global worker instance
mcp_worker = GreptileMCPWorker()

def create_cors_headers() -> Dict[str, str]:
    """Create CORS headers for cross-origin requests."""
    cors_origin = get_environment_variable("CORS_ORIGIN", "*")
    return {
        "Access-Control-Allow-Origin": cors_origin,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
        "Content-Type": "application/json"
    }

async def handle_mcp_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP requests."""
    try:
        method = request_data.get("method")
        params = request_data.get("params", {})
        
        if not method:
            return create_error_response("Missing 'method' in request")
        
        result = await mcp_worker.handle_mcp_request(method, params)
        return result
        
    except Exception as e:
        return create_error_response(f"Request processing error: {str(e)}")

async def on_fetch(request):
    """
    Main entry point for Cloudflare Workers.
    
    This function handles all incoming HTTP requests to the worker.
    """
    try:
        # Parse the request
        url_obj = URL.new(request.url)
        method = request.method
        path = url_obj.pathname
        
        # Handle CORS preflight
        if method == "OPTIONS":
            return Response.new(
                "",
                status=200,
                headers=Headers.new(create_cors_headers())
            )
        
        # Handle different endpoints
        if path == "/health" or path == "/":
            # Health check endpoint
            health_data = {
                "status": "healthy",
                "service": "greptile-mcp-server",
                "version": "1.0.0",
                "transport": "http",
                "deployment": "cloudflare-workers",
                "runtime": "python-stdlib"
            }
            return Response.new(
                JSON.stringify(health_data),
                status=200,
                headers=Headers.new(create_cors_headers())
            )
        
        elif path == "/sse" or path.startswith("/mcp"):
            # MCP endpoint
            if method == "POST":
                # Parse request body
                try:
                    body_text = await request.text()
                    request_data = json.loads(body_text) if body_text else {}
                except Exception as e:
                    return Response.new(
                        JSON.stringify(create_error_response("Invalid JSON in request body")),
                        status=400,
                        headers=Headers.new(create_cors_headers())
                    )
                
                # Handle the MCP request
                result = await handle_mcp_request(request_data)
                
                # Return response
                status_code = 200 if result.get("success", True) else 400
                return Response.new(
                    JSON.stringify(result),
                    status=status_code,
                    headers=Headers.new(create_cors_headers())
                )
            
            elif method == "GET":
                # For GET requests, return server information
                server_info = {
                    "name": "greptile-mcp-server",
                    "version": "1.0.0",
                    "description": "MCP server for code search and querying with Greptile API",
                    "transport": ["http", "sse"],
                    "deployment": "cloudflare-workers",
                    "runtime": "python-stdlib",
                    "endpoints": {
                        "/": "Health check",
                        "/health": "Health check", 
                        "/sse": "SSE MCP endpoint",
                        "/mcp": "HTTP MCP endpoint"
                    },
                    "tools": [
                        "index_repository",
                        "query_repository", 
                        "search_repository",
                        "get_repository_info"
                    ]
                }
                return Response.new(
                    JSON.stringify(server_info),
                    status=200,
                    headers=Headers.new(create_cors_headers())
                )
        
        else:
            # Unknown endpoint
            return Response.new(
                JSON.stringify(create_error_response(f"Unknown endpoint: {path}")),
                status=404,
                headers=Headers.new(create_cors_headers())
            )
    
    except Exception as e:
        return Response.new(
            JSON.stringify(create_error_response(f"Internal server error: {str(e)}")),
            status=500,
            headers=Headers.new(create_cors_headers())
        )

# Export the main handler for Cloudflare Workers
export = {"fetch": on_fetch}