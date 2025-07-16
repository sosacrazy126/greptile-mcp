import httpx
import os
import urllib.parse
import typing
import uuid
import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from typing import Optional, Any, Dict, List

# Import logging after avoiding circular imports
try:
    from src.logging_config import logger
except ImportError:
    # Fallback to basic logging if circular import
    logger = logging.getLogger(__name__)

###############################################################################
# Session Management Utilities
###############################################################################

class SessionManager:
    """
    In-memory session and context manager for conversation message history.
    This can be swapped or extended for persistent storage if needed.
    """
    def __init__(self):
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        async with self._lock:
            return list(self.sessions.get(session_id, []))

    async def append_message(self, session_id: str, message: Dict[str, Any]) -> None:
        async with self._lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = []
            self.sessions[session_id].append(message)

    async def set_history(self, session_id: str, messages: List[Dict[str, Any]]) -> None:
        async with self._lock:
            self.sessions[session_id] = list(messages)

    async def clear_session(self, session_id: str) -> None:
        async with self._lock:
            self.sessions.pop(session_id, None)

def generate_session_id() -> str:
    """
    Generate a new unique session ID in proper UUID format.
    
    Returns:
        str: A properly formatted UUID string (e.g., '12345678-1234-1234-1234-123456789abc')
    """
    session_id = str(uuid.uuid4())
    # Ensure it's in lowercase for consistency
    return session_id.lower()

def normalize_session_id(session_id: Optional[str]) -> Optional[str]:
    """
    Normalize a session ID to ensure consistent format.
    
    Args:
        session_id: The session ID to normalize
        
    Returns:
        str: Normalized session ID in lowercase, or None if input was None
    """
    if session_id is None:
        return None
    return session_id.lower().strip()

###############################################################################
# Greptile API Client
###############################################################################

class GreptileClient:
    """Client for interacting with the Greptile API."""

    def __init__(self, api_key: str, github_token: str, base_url: str = "https://api.greptile.com/v2"):
        """
        Initialize the Greptile API client.

        Args:
            api_key: Greptile API key
            github_token: GitHub/GitLab personal access token
            base_url: Base URL for the Greptile API
            default_timeout: Default timeout for API calls in seconds
        """
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "X-GitHub-Token": github_token,
            "Content-Type": "application/json"
        }
        self.default_timeout = 60.0  # Default timeout for long operations
        self.client = httpx.AsyncClient(timeout=self.default_timeout)

    async def aclose(self) -> None:
        """Close the underlying HTTPX client."""
        await self.client.aclose()

    async def index_repository(
        self, 
        remote: str, 
        repository: str, 
        branch: str, 
        reload: bool = True, 
        notify: bool = False
    ) -> Dict[str, Any]:
        """
        Index a repository for code search and querying.

        Args:
            remote: The repository host, either "github" or "gitlab"
            repository: The repository in owner/repo format
            branch: The branch to index
            reload: Whether to force reprocessing (default: True).
                   When False, won't reprocess if previously indexed successfully.
            notify: Whether to send an email notification (default: False)

        Returns:
            The API response as a dictionary
        """
        url = f"{self.base_url}/repositories"
        payload = {
            "remote": remote,
            "repository": repository,
            "branch": branch,
            "reload": reload,
            "notify": notify
        }

        try:
            logger.debug(f"Making API call to {url}", payload=payload)
            response = await self.client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            logger.debug("API call successful", status_code=response.status_code)
            return result
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error during repository indexing",
                status_code=e.response.status_code,
                response_text=e.response.text,
                url=url
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error during repository indexing", error=str(e), url=url)
            raise
        except Exception as e:
            logger.error("Unexpected error during repository indexing", error=str(e), url=url)
            raise

    async def query_repositories(
        self,
        messages: List[Dict[str, Any]],
        repositories: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        stream: bool = False,
        genius: bool = True,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Query repositories to get an answer with code references.

        Args:
            messages: List of message objects with role and content
            repositories: List of repository objects
            session_id: Optional session ID for continuing a conversation
            stream: Whether to stream the response (returns final output, not streaming generator)
            genius: Whether to use enhanced query capabilities
            timeout: Optional request timeout in seconds

        Returns:
            The API response as a dictionary if stream=False,
            or an AsyncGenerator yielding chunks if stream=True
        """
        if stream:
            # Return streaming response
            return self.stream_query_repositories(
                messages, repositories, session_id, genius, timeout
            )
            
        url = f"{self.base_url}/query"
        payload = {
            "messages": messages,
            "repositories": repositories,
            "stream": False,
            "genius": genius
        }
        if session_id:
            payload["sessionId"] = session_id

        client_timeout = timeout if timeout is not None else self.default_timeout
        async with httpx.AsyncClient(timeout=client_timeout) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def stream_query_repositories(
        self,
        messages: List[Dict[str, Any]],
        repositories: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        genius: bool = True,
        timeout: Optional[float] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams the Greptile /query endpoint using Server-Sent Events (SSE).

        Args:
            messages: List of message objects with role and content
            repositories: List of repository objects
            session_id: Optional session ID for continuing a conversation
            genius: Whether to use enhanced query capabilities
            timeout: Optional request timeout in seconds

        Yields:
            Structured chunk data including text content, citations, and metadata.
        """
        url = f"{self.base_url}/query"
        payload = {
            "messages": messages,
            "repositories": repositories,
            "stream": True,
            "genius": genius
        }
        if session_id:
            payload["sessionId"] = session_id

        # Use streaming-specific headers
        headers = {
            **self.headers,
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache"
        }

        req_timeout = timeout if timeout is not None else self.default_timeout
        async with httpx.AsyncClient(timeout=req_timeout) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                
                # Process Server-Sent Events
                async for line in response.aiter_lines():
                    if line and line.strip():
                        try:
                            # Parse SSE format: "data: {json}"
                            if line.startswith("data: "):
                                raw = line[6:]  # Remove "data: " prefix
                                chunk = __safe_json_loads(raw)
                                
                                # Yield structured chunk data
                                if chunk:
                                    chunk_type = chunk.get("type")
                                    if chunk_type == "text":
                                        yield {
                                            "type": "text",
                                            "content": chunk.get("content", ""),
                                            "timestamp": time.time()
                                        }
                                    elif chunk_type == "citation":
                                        yield {
                                            "type": "citation",
                                            "file": chunk.get("file"),
                                            "lines": chunk.get("lines"),
                                            "timestamp": time.time()
                                        }
                                    elif "sessionId" in chunk:
                                        yield {
                                            "type": "session",
                                            "sessionId": chunk["sessionId"],
                                            "timestamp": time.time()
                                        }
                                    else:
                                        # Forward other chunk types as-is
                                        yield {
                                            "type": "other",
                                            "data": chunk,
                                            "timestamp": time.time()
                                        }
                                        
                        except Exception:
                            # Skip malformed chunks but continue streaming
                            continue

    async def search_repositories(
        self,
        messages: List[Dict[str, Any]],
        repositories: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        genius: bool = True,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Search repositories for relevant files without generating a full answer.

        Args:
            messages: List of message objects with role and content
            repositories: List of repository objects
            session_id: Optional session ID for continuing a conversation
            genius: Whether to use enhanced search capabilities
            timeout: Optional request timeout in seconds

        Returns:
            The API response as a dictionary
        """
        url = f"{self.base_url}/search"
        payload = {
            "messages": messages,
            "repositories": repositories,
            "genius": genius
        }

        if session_id:
            payload["sessionId"] = session_id

        client_timeout = timeout if timeout is not None else self.default_timeout
        async with httpx.AsyncClient(timeout=client_timeout) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_repository_info(self, remote: str, repository: str, branch: str) -> Dict[str, Any]:
        """
        Get information about an indexed repository.

        Args:
            remote: The repository host ("github" or "gitlab")
            repository: Repository in owner/repo format
            branch: The branch that was indexed

        Returns:
            The API response as a dictionary
        """
        repository_id = f"{remote}:{branch}:{repository}"
        encoded_id = urllib.parse.quote_plus(repository_id, safe='')
        url = f"{self.base_url}/repositories/{encoded_id}"

        response = await self.client.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

###############################################################################
# Helper utilities
###############################################################################

def __safe_json_loads(text: str) -> Any:
    """
    Attempt to decode a JSON string; returns None on failure.
    Used for robustly parsing streaming response lines.
    """
    import json
    try:
        return json.loads(text)
    except Exception:
        return None

def get_greptile_client() -> GreptileClient:
    """
    Create and configure a Greptile API client based on environment variables.

    Returns:
        GreptileClient: Configured Greptile API client
        
    Raises:
        ValueError: If required environment variables are missing
    """
    api_key = os.getenv("GREPTILE_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    base_url = os.getenv("GREPTILE_BASE_URL", "https://api.greptile.com/v2")

    if not api_key:
        raise ValueError("GREPTILE_API_KEY environment variable is required")

    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")

    return GreptileClient(api_key, github_token, base_url)
