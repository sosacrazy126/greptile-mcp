"""
Shared utilities for both local and Cloudflare Workers deployments.

This module provides common functionality that works in both environments,
with appropriate abstractions for differences between local Python and 
Cloudflare Workers Python runtime.
"""

import json
import os
import uuid
import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Dict, Any, List, Optional, Union

# Try to detect if we're running in Cloudflare Workers
try:
    from js import fetch, Headers as JSHeaders
    CLOUDFLARE_ENVIRONMENT = True
except ImportError:
    CLOUDFLARE_ENVIRONMENT = False

# Use appropriate HTTP client based on environment
if CLOUDFLARE_ENVIRONMENT:
    # For Cloudflare Workers, we'll use the fetch API
    HTTP_CLIENT = None
else:
    # For local environment, use httpx
    try:
        import httpx
        HTTP_CLIENT = "httpx"
    except ImportError:
        HTTP_CLIENT = None

# Configure logging
logger = logging.getLogger(__name__)

###############################################################################
# Environment Variable Utilities
###############################################################################

def get_environment_variable(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get environment variable that works in both local and Cloudflare Workers.
    
    In Cloudflare Workers, environment variables are available via the global env object
    or through process.env (depending on configuration).
    """
    if CLOUDFLARE_ENVIRONMENT:
        # In Cloudflare Workers, try to get from various sources
        try:
            # Try process.env first (if available)
            from js import process
            if hasattr(process, 'env') and hasattr(process.env, key):
                return getattr(process.env, key)
        except:
            pass
        
        try:
            # Try global env object (Cloudflare Workers binding)
            from js import env
            if hasattr(env, key):
                return getattr(env, key)
        except:
            pass
    
    # Fallback to standard os.getenv
    return os.getenv(key, default)

###############################################################################
# Response Utilities
###############################################################################

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

###############################################################################
# Session Management (adapted for Cloudflare Workers)
###############################################################################

class DurableSessionManager:
    """
    Durable Objects-based session manager for persistent session storage.
    
    This class provides persistent session management using Cloudflare Durable Objects,
    ensuring conversation history persists across worker invocations with robust error
    handling and fallback mechanisms.
    """
    
    def __init__(self, session_manager_binding=None):
        """
        Initialize the durable session manager.
        
        Args:
            session_manager_binding: The Durable Objects binding from env
        """
        self.session_manager_binding = session_manager_binding
        self._durable_objects = {}  # Cache for durable object stubs
        self._fallback_sessions = {}  # In-memory fallback for critical failures
        self._max_retries = 3
        self._retry_delay = 0.1  # seconds
    
    def _get_durable_object_stub(self, session_id: str):
        """Get or create a durable object stub for the given session."""
        if session_id not in self._durable_objects:
            if not self.session_manager_binding:
                raise RuntimeError("SESSION_MANAGER binding not available")
            
            # Create a durable object ID for this session
            do_id = self.session_manager_binding.idFromName(session_id)
            self._durable_objects[session_id] = self.session_manager_binding.get(do_id)
        
        return self._durable_objects[session_id]
    
    async def _retry_with_fallback(self, operation_name: str, session_id: str, operation_func, fallback_func=None):
        """Execute an operation with retry logic and fallback to in-memory storage."""
        last_exception = None
        
        for attempt in range(self._max_retries):
            try:
                return await operation_func()
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed for {operation_name} on session {session_id}: {str(e)}")
                
                if attempt < self._max_retries - 1:
                    # Wait before retrying
                    import time
                    time.sleep(self._retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    # Last attempt failed, use fallback
                    logger.error(f"All {self._max_retries} attempts failed for {operation_name} on session {session_id}: {str(last_exception)}")
                    if fallback_func:
                        logger.info(f"Using fallback mechanism for {operation_name} on session {session_id}")
                        return await fallback_func()
                    else:
                        # Return safe default
                        if operation_name == "get_history":
                            return []
                        else:
                            return None
        
        # Should never reach here, but just in case
        return None

    async def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session from durable storage with fallback."""
        async def do_operation():
            stub = self._get_durable_object_stub(session_id)
            
            # Make request to durable object
            from js import Request, Headers
            request = Request.new(f"https://durable-object/history", {
                "method": "GET",
                "headers": Headers.new({"Content-Type": "application/json"})
            })
            
            response = await stub.fetch(request)
            
            if response.ok:
                response_text = await response.text()
                response_data = json.loads(response_text)
                
                if response_data.get("success"):
                    return response_data.get("data", [])
                else:
                    raise Exception(f"Durable Object returned error: {response_data.get('error')}")
            else:
                raise Exception(f"HTTP {response.status} getting history")
        
        async def fallback():
            # Return in-memory fallback data
            return list(self._fallback_sessions.get(session_id, []))
        
        return await self._retry_with_fallback("get_history", session_id, do_operation, fallback)
    
    async def append_message(self, session_id: str, message: Dict[str, Any]) -> None:
        """Append a message to session history in durable storage with fallback."""
        async def do_operation():
            stub = self._get_durable_object_stub(session_id)
            
            # Prepare request body
            body_data = {
                "operation": "append_message",
                "message": message
            }
            
            # Make request to durable object
            from js import Request, Headers, JSON
            request = Request.new(f"https://durable-object/update", {
                "method": "POST",
                "headers": Headers.new({"Content-Type": "application/json"}),
                "body": JSON.stringify(body_data)
            })
            
            response = await stub.fetch(request)
            
            if response.ok:
                return True
            else:
                response_text = await response.text()
                raise Exception(f"HTTP {response.status}: {response_text}")
        
        async def fallback():
            # Append to in-memory fallback
            if session_id not in self._fallback_sessions:
                self._fallback_sessions[session_id] = []
            self._fallback_sessions[session_id].append(message)
            return True
        
        await self._retry_with_fallback("append_message", session_id, do_operation, fallback)
    
    async def set_history(self, session_id: str, messages: List[Dict[str, Any]]) -> None:
        """Set the complete message history for a session in durable storage with fallback."""
        async def do_operation():
            stub = self._get_durable_object_stub(session_id)
            
            # Prepare request body
            body_data = {
                "operation": "set_history",
                "messages": messages
            }
            
            # Make request to durable object
            from js import Request, Headers, JSON
            request = Request.new(f"https://durable-object/update", {
                "method": "POST",
                "headers": Headers.new({"Content-Type": "application/json"}),
                "body": JSON.stringify(body_data)
            })
            
            response = await stub.fetch(request)
            
            if response.ok:
                return True
            else:
                response_text = await response.text()
                raise Exception(f"HTTP {response.status}: {response_text}")
        
        async def fallback():
            # Set in-memory fallback
            self._fallback_sessions[session_id] = list(messages)
            return True
        
        await self._retry_with_fallback("set_history", session_id, do_operation, fallback)
    
    async def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session from durable storage with fallback."""
        async def do_operation():
            stub = self._get_durable_object_stub(session_id)
            
            # Make request to durable object
            from js import Request, Headers
            request = Request.new(f"https://durable-object/clear", {
                "method": "DELETE",
                "headers": Headers.new({"Content-Type": "application/json"})
            })
            
            response = await stub.fetch(request)
            
            if response.ok:
                return True
            else:
                response_text = await response.text()
                raise Exception(f"HTTP {response.status}: {response_text}")
        
        async def fallback():
            # Clear in-memory fallback
            self._fallback_sessions.pop(session_id, None)
            return True
        
        await self._retry_with_fallback("clear_session", session_id, do_operation, fallback)


class SessionManager:
    """
    Session manager that works in both local and Cloudflare Workers environments.
    
    In Cloudflare Workers, this uses Durable Objects for persistent storage.
    In local environment, this uses in-memory storage with asyncio locks.
    """
    
    def __init__(self, session_manager_binding=None):
        if CLOUDFLARE_ENVIRONMENT and session_manager_binding:
            # Use Durable Objects for persistent storage in Cloudflare Workers
            self._manager = DurableSessionManager(session_manager_binding)
        else:
            # Use in-memory storage for local development
            self._manager = InMemorySessionManager()
    
    async def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        return await self._manager.get_history(session_id)
    
    async def append_message(self, session_id: str, message: Dict[str, Any]) -> None:
        """Append a message to session history."""
        await self._manager.append_message(session_id, message)
    
    async def set_history(self, session_id: str, messages: List[Dict[str, Any]]) -> None:
        """Set the complete message history for a session."""
        await self._manager.set_history(session_id, messages)
    
    async def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session."""
        await self._manager.clear_session(session_id)


class InMemorySessionManager:
    """
    In-memory session manager for local development.
    
    This implementation uses in-memory storage with asyncio locks for thread safety.
    It's suitable for local development but not for production use in Cloudflare Workers.
    """
    
    def __init__(self):
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()
    
    async def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        async with self._lock:
            return list(self.sessions.get(session_id, []))
    
    async def append_message(self, session_id: str, message: Dict[str, Any]) -> None:
        """Append a message to session history."""
        async with self._lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = []
            self.sessions[session_id].append(message)
    
    async def set_history(self, session_id: str, messages: List[Dict[str, Any]]) -> None:
        """Set the complete message history for a session."""
        async with self._lock:
            self.sessions[session_id] = list(messages)
    
    async def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session."""
        async with self._lock:
            self.sessions.pop(session_id, None)

def generate_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())

###############################################################################
# HTTP Client Abstraction
###############################################################################

class HTTPClient:
    """HTTP client that works in both local and Cloudflare Workers environments."""
    
    def __init__(self, timeout: float = 60.0):
        self.timeout = timeout
        if not CLOUDFLARE_ENVIRONMENT and HTTP_CLIENT == "httpx":
            self.client = httpx.AsyncClient(timeout=timeout)
        else:
            self.client = None
    
    async def aclose(self):
        """Close the HTTP client if needed."""
        if self.client and hasattr(self.client, 'aclose'):
            await self.client.aclose()
    
    async def post(self, url: str, json_data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Make a POST request."""
        if CLOUDFLARE_ENVIRONMENT:
            return await self._fetch_post(url, json_data, headers)
        elif self.client:
            return await self._httpx_post(url, json_data, headers)
        else:
            raise RuntimeError("No HTTP client available")
    
    async def get(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Make a GET request."""
        if CLOUDFLARE_ENVIRONMENT:
            return await self._fetch_get(url, headers)
        elif self.client:
            return await self._httpx_get(url, headers)
        else:
            raise RuntimeError("No HTTP client available")
    
    async def _fetch_post(self, url: str, json_data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """POST request using Cloudflare Workers fetch API."""
        from js import fetch, JSON
        
        # Convert headers to JS Headers object
        js_headers = JSHeaders.new()
        for key, value in headers.items():
            js_headers.set(key, value)
        
        # Make the request
        response = await fetch(url, {
            "method": "POST",
            "headers": js_headers,
            "body": JSON.stringify(json_data)
        })
        
        if not response.ok:
            raise Exception(f"HTTP {response.status}: {response.statusText}")
        
        # Parse JSON response
        response_text = await response.text()
        return json.loads(response_text)
    
    async def _fetch_get(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """GET request using Cloudflare Workers fetch API."""
        from js import fetch
        
        # Convert headers to JS Headers object
        js_headers = JSHeaders.new()
        for key, value in headers.items():
            js_headers.set(key, value)
        
        # Make the request
        response = await fetch(url, {
            "method": "GET",
            "headers": js_headers
        })
        
        if not response.ok:
            raise Exception(f"HTTP {response.status}: {response.statusText}")
        
        # Parse JSON response
        response_text = await response.text()
        return json.loads(response_text)
    
    async def _httpx_post(self, url: str, json_data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """POST request using httpx (local environment)."""
        response = await self.client.post(url, json=json_data, headers=headers)
        response.raise_for_status()
        return response.json()
    
    async def _httpx_get(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """GET request using httpx (local environment)."""
        response = await self.client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

###############################################################################
# Greptile API Client (adapted for cross-environment use)
###############################################################################

class GreptileClient:
    """Greptile API client that works in both local and Cloudflare Workers environments."""
    
    def __init__(self, api_key: str, github_token: str, base_url: str = "https://api.greptile.com/v2"):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "X-GitHub-Token": github_token,
            "Content-Type": "application/json"
        }
        self.default_timeout = 60.0
        self.client = HTTPClient(self.default_timeout)
    
    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()
    
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
        
        return await self.client.post(url, payload, self.headers)
    
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
            "stream": False,  # Streaming not yet supported in Workers
            "genius": genius
        }
        if session_id:
            payload["sessionId"] = session_id
        
        return await self.client.post(url, payload, self.headers)
    
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
        
        return await self.client.post(url, payload, self.headers)
    
    async def get_repository_info(self, repository_id: str) -> Dict[str, Any]:
        """Get information about an indexed repository."""
        import urllib.parse
        encoded_id = urllib.parse.quote_plus(repository_id, safe='')
        url = f"{self.base_url}/repositories/{encoded_id}"
        
        return await self.client.get(url, self.headers)

###############################################################################
# Utility Functions
###############################################################################

def safe_json_loads(text: str) -> Any:
    """Safely parse JSON, returning None on failure."""
    try:
        return json.loads(text)
    except Exception:
        return None

def format_repository_list(repositories: List[str]) -> List[Dict[str, Any]]:
    """
    Convert repository strings to the format expected by Greptile API.
    
    Supports formats like:
    - "github/owner/repo"
    - "github:owner/repo:branch"
    - {"remote": "github", "repository": "owner/repo", "branch": "main"}
    """
    formatted = []
    for repo in repositories:
        if isinstance(repo, dict):
            # Already in correct format
            formatted.append(repo)
        elif isinstance(repo, str):
            # Parse string format
            if repo.count(':') == 2:
                # Format: "github:owner/repo:branch"
                remote, repository, branch = repo.split(':', 2)
            elif repo.count('/') >= 2:
                # Format: "github/owner/repo" or "owner/repo"
                parts = repo.split('/')
                if len(parts) == 3:
                    remote, repository = parts[0], f"{parts[1]}/{parts[2]}"
                    branch = "main"
                else:
                    remote = "github"
                    repository = f"{parts[0]}/{parts[1]}"
                    branch = "main"
            else:
                raise ValueError(f"Invalid repository format: {repo}")
            
            formatted.append({
                "remote": remote,
                "repository": repository,
                "branch": branch
            })
    
    return formatted