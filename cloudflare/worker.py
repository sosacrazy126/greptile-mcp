"""
Cloudflare Workers Python entry point for Greptile MCP Server.

This module provides a remote MCP server implementation that runs on Cloudflare Workers,
supporting both HTTP and SSE transports while maintaining compatibility with the
existing local/Docker deployment.
"""

import asyncio
import json
import os
import logging
from collections.abc import AsyncGenerator
from typing import Dict, Any, List, Optional, Union
from urllib.parse import parse_qs, urlparse

# Cloudflare Workers Python imports
from js import Request, Response, Headers, JSON

# Import shared utilities (we'll create a shared module)
from cloudflare.shared_utils import (
    GreptileClient,
    SessionManager,
    generate_session_id,
    get_environment_variable,
    create_error_response,
    create_success_response
)

# Configure logging for Cloudflare Workers
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global session manager for the worker
session_manager = None

class GreptileMCPWorker:
    """Main MCP server implementation for Cloudflare Workers."""
    
    def __init__(self, env=None):
        # Initialize session manager with environment bindings
        if env and hasattr(env, 'SESSION_MANAGER'):
            self.session_manager = SessionManager(env.SESSION_MANAGER)
        else:
            # Fallback to in-memory session manager
            self.session_manager = SessionManager()
        
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
    
    async def handle_mcp_request(self, method: str, params: Dict[str, Any], user_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle MCP tool requests with optional user context."""
        try:
            # Check permissions
            allowed, error_msg = await self.oauth_middleware.check_permissions(user_data, method, params)
            if not allowed:
                return create_error_response(f"Access denied: {error_msg}")
            
            # Add user context to params if authenticated
            if user_data:
                params["_user_context"] = user_data.get("user", {})
            
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
            logger.error(f"Error handling MCP request {method}: {str(e)}")
            return create_error_response(f"Error in {method}: {str(e)}")
    
    async def index_repository(
        self, 
        remote: str, 
        repository: str, 
        branch: str, 
        reload: bool = True, 
        notify: bool = False,
        _user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Index a repository for code search and querying."""
        try:
            # Log user context if available
            if _user_context:
                logger.info(f"User {_user_context.get('login', 'unknown')} indexing repository {repository}")
            
            greptile_client = self.get_greptile_client()
            result = await greptile_client.index_repository(remote, repository, branch, reload, notify)
            await greptile_client.aclose()
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
        previous_messages: Optional[List[Dict[str, Any]]] = None,
        _user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query repositories to get answers with code references."""
        try:
            # Log user context if available
            if _user_context:
                logger.info(f"User {_user_context.get('login', 'unknown')} querying repositories")
            
            greptile_client = self.get_greptile_client()
            
            # Session logic - include user context in session ID if available
            if _user_context and not session_id:
                user_id = _user_context.get('id', _user_context.get('login', 'unknown'))
                sid = f"user_{user_id}_{generate_session_id()}"
            else:
                sid = session_id or generate_session_id()
            
            # Build message history
            if previous_messages is not None:
                messages = previous_messages + [{"role": "user", "content": query}]
                await self.session_manager.set_history(sid, messages)
            else:
                history = await self.session_manager.get_history(sid)
                messages = history + [{"role": "user", "content": query}]
                await self.session_manager.set_history(sid, messages)
            
            # For streaming responses in Workers, we'll need to handle differently
            # For now, we'll disable streaming and return complete responses
            if stream:
                logger.warning("Streaming not yet supported in Cloudflare Workers, using non-streaming response")
                stream = False
            
            # Non-streaming query
            result = await greptile_client.query_repositories(
                messages, repositories, session_id=sid, stream=False, genius=genius, timeout=timeout
            )
            await greptile_client.aclose()
            
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
        genius: bool = True,
        _user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search repositories for relevant files without generating a full answer."""
        try:
            # Log user context if available
            if _user_context:
                logger.info(f"User {_user_context.get('login', 'unknown')} searching repositories")
            
            greptile_client = self.get_greptile_client()
            messages = [{"role": "user", "content": query}]
            result = await greptile_client.search_repositories(messages, repositories, session_id, genius)
            await greptile_client.aclose()
            return create_success_response(result)
        except Exception as e:
            return create_error_response(f"Error searching repositories: {str(e)}")
    
    async def get_repository_info(self, remote: str, repository: str, branch: str, _user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get information about an indexed repository."""
        try:
            # Log user context if available
            if _user_context:
                logger.info(f"User {_user_context.get('login', 'unknown')} getting repository info for {repository}")
            
            greptile_client = self.get_greptile_client()
            repository_id = f"{remote}:{branch}:{repository}"
            result = await greptile_client.get_repository_info(repository_id)
            await greptile_client.aclose()
            return create_success_response(result)
        except Exception as e:
            return create_error_response(f"Error getting repository info: {str(e)}")

# Global worker instance
mcp_worker = GreptileMCPWorker()

async def handle_http_request(request_data: Dict[str, Any], user_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle HTTP-based MCP requests with optional user context."""
    try:
        method = request_data.get("method")
        params = request_data.get("params", {})
        
        if not method:
            return create_error_response("Missing 'method' in request")
        
        result = await mcp_worker.handle_mcp_request(method, params, user_data)
        return result
        
    except Exception as e:
        logger.error(f"Error handling HTTP request: {str(e)}")
        return create_error_response(f"Request processing error: {str(e)}")

async def handle_sse_request(request_data: Dict[str, Any], user_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle SSE-based MCP requests (Server-Sent Events)."""
    # For now, we'll treat SSE requests the same as HTTP requests
    # In a full implementation, this would handle the SSE protocol
    return await handle_http_request(request_data, user_data)

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

async def on_fetch(request, env, ctx):
    """
    Main entry point for Cloudflare Workers.
    
    This function handles all incoming HTTP requests to the worker.
    Args:
        request: The incoming HTTP request
        env: Environment bindings including Durable Objects
        ctx: Execution context
    """
    try:
        # Parse the request
        url = urlparse(request.url)
        method = request.method
        path = url.path
        
        # Handle CORS preflight
        if method == "OPTIONS":
            return Response.new(
                "",
                status=200,
                headers=Headers.new(create_cors_headers())
            )
        
        # Handle OAuth authentication endpoints
        if path.startswith("/auth/"):
            oauth_response = await oauth_middleware.handle_auth_request(request, path)
            if oauth_response:
                return oauth_response
        
        # Handle different endpoints
        if path == "/health" or path == "/":
            # Health check endpoint
            health_data = {
                "status": "healthy",
                "service": "greptile-mcp-server",
                "version": "1.0.0",
                "transport": "http",
                "deployment": "cloudflare-workers"
            }
            return Response.new(
                JSON.stringify(health_data),
                status=200,
                headers=Headers.new(create_cors_headers())
            )
        
        elif path == "/sse" or path.startswith("/mcp"):
            # MCP endpoint - handle both SSE and HTTP requests
            if method == "POST":
                # Parse request body
                try:
                    body_text = await request.text()
                    request_data = json.loads(body_text) if body_text else {}
                except Exception as e:
                    logger.error(f"Error parsing request body: {str(e)}")
                    return Response.new(
                        JSON.stringify(create_error_response("Invalid JSON in request body")),
                        status=400,
                        headers=Headers.new(create_cors_headers())
                    )
                
                # Get user context from OAuth token (if available)
                user_data = await oauth_middleware.get_user_from_request(request)
                
                # Handle the MCP request
                if path == "/sse":
                    result = await handle_sse_request(request_data, user_data)
                else:
                    result = await handle_http_request(request_data, user_data)
                
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
                    "endpoints": {
                        "/": "Health check",
                        "/health": "Health check", 
                        "/sse": "SSE MCP endpoint",
                        "/mcp": "HTTP MCP endpoint",
                        "/auth/login": "OAuth login initiation",
                        "/auth/callback": "OAuth callback handler",
                        "/auth/logout": "OAuth logout",
                        "/auth/user": "Get authenticated user info"
                    },
                    "tools": [
                        "index_repository",
                        "query_repository", 
                        "search_repository",
                        "get_repository_info"
                    ],
                    "oauth": {
                        "enabled": oauth_middleware.enabled,
                        "providers": list(oauth_middleware.providers.keys()) if oauth_middleware.enabled else [],
                        "require_auth": get_environment_variable("OAUTH_REQUIRE_AUTH", "false").lower() == "true"
                    }
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
        logger.error(f"Unhandled error in on_fetch: {str(e)}")
        return Response.new(
            JSON.stringify(create_error_response(f"Internal server error: {str(e)}")),
            status=500,
            headers=Headers.new(create_cors_headers())
        )

# Import the Durable Object class
from cloudflare.session_durable_object import SessionManager as SessionManagerDO

# Export the main handler and Durable Objects for Cloudflare Workers
export = {
    "fetch": on_fetch,
    "SessionManager": SessionManagerDO
}