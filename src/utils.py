import httpx
import os
import urllib.parse
import typing
import uuid
import asyncio
import logging
import json
from collections.abc import AsyncGenerator
from typing import Optional, Any, Dict, List, Union

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
    """Generate a new unique session ID."""
    return str(uuid.uuid4())

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
        reload: bool = False, 
        notify: bool = False
    ) -> Dict[str, Any]:
        """
        Index a repository for code search and querying.

        Args:
            remote: The repository host, either "github" or "gitlab"
            repository: The repository in owner/repo format
            branch: The branch to index
            reload: Whether to force reprocessing
            notify: Whether to send an email notification

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

        response = await self.client.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

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
        Streams the Greptile /query endpoint using chunked responses.

        Args:
            messages: List of message objects with role and content
            repositories: List of repository objects
            session_id: Optional session ID for continuing a conversation
            genius: Whether to use enhanced query capabilities
            timeout: Optional request timeout in seconds

        Yields:
            Parsed chunked message objects as dictionaries.
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

        req_timeout = timeout if timeout is not None else self.default_timeout
        async with httpx.AsyncClient(timeout=req_timeout) as client:
            async with client.stream("POST", url, json=payload, headers=self.headers) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            # Some APIs may prefix with data:, etc.; strip it if needed
                            raw = line
                            if raw.startswith("data: "):
                                raw = raw[6:]
                            chunk = typing.cast(Dict[str, Any], __safe_json_loads(raw))
                            yield chunk
                        except Exception:
                            # Optionally log/handle parse errors per chunk here
                            continue

    async def search_repositories(
        self,
        messages: List[Dict[str, Any]],
        repositories: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        genius: bool = True
    ) -> Dict[str, Any]:
        """
        Search repositories for relevant files without generating a full answer.

        Args:
            messages: List of message objects with role and content
            repositories: List of repository objects
            session_id: Optional session ID for continuing a conversation
            genius: Whether to use enhanced search capabilities

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

        response = await self.client.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    async def get_repository_info(self, repository_id: str) -> Dict[str, Any]:
        """
        Get information about an indexed repository.

        Args:
            repository_id: Repository ID in the format "remote:branch:owner/repository"

        Returns:
            The API response as a dictionary
        """
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

###############################################################################
# Additional Helpers and Client Wrappers (PR #146 integration)
###############################################################################

def validate_repositories(repos: List[Dict[str, str]]) -> None:
    """
    Raises ValueError if any repo entry is missing 'remote', 'repository', or 'branch' keys.
    """
    required_keys = {"remote", "repository", "branch"}
    for idx, repo in enumerate(repos):
        if not all(k in repo for k in required_keys):
            raise ValueError(f"Repository entry at index {idx} missing required key(s): {required_keys - set(repo.keys())}")

def format_messages_for_api(messages_or_query: Union[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    If a raw str is passed, wrap as single {'role':'user','content':...} entry.
    If already list-of-dict, return as-is.
    """
    if isinstance(messages_or_query, str):
        return [{"role": "user", "content": messages_or_query}]
    if isinstance(messages_or_query, list):
        return messages_or_query
    raise ValueError("Invalid type for messages_or_query: expected str or list of dict")

def flatten_repositories(repositories: List[Union[Dict[str, str], List[Dict[str, str]]]]) -> List[Dict[str, str]]:
    """
    Flattens a list of repositories or list-of-lists thereof into a single list.
    """
    flattened = []
    for entry in repositories:
        if isinstance(entry, list):
            flattened.extend(entry)
        else:
            flattened.append(entry)
    return flattened

def ensure_async(func):
    """
    Decorator: ensures function is async, wraps sync as async if needed.
    """
    if asyncio.iscoroutinefunction(func):
        return func
    async def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def _aggregate_list_of_lists(list_of_lists):
    agg = []
    for e in list_of_lists:
        if isinstance(e, list):
            agg.extend(e)
        else:
            agg.append(e)
    return agg

def _as_jsonable(obj):
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)

# ---- Async wrappers for GreptileClient ----
@ensure_async
async def query_multiple_repositories(
    client: GreptileClient,
    messages: Union[str, List[Dict[str, Any]]],
    repositories: List[Union[Dict[str, str], List[Dict[str, str]]]],
    session_id: Optional[str] = None,
    stream: bool = False,
    genius: bool = True,
    timeout: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Same signature as query_repositories but allows repositories to be list-of-list.
    (For now, calls straight through to query_repositories using aggregated list.)
    """
    agg_repos = flatten_repositories(repositories)
    return await client.query_repositories(
        messages=format_messages_for_api(messages),
        repositories=agg_repos,
        session_id=session_id,
        stream=stream,
        genius=genius,
        timeout=timeout,
    )

@ensure_async
async def compare_repositories(
    client: GreptileClient,
    messages: Union[str, List[Dict[str, Any]]],
    repositories_a: List[Dict[str, str]],
    repositories_b: List[Dict[str, str]],
    session_id: Optional[str] = None,
    genius: bool = True,
    timeout: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calls query_repositories twice (once per repo set) and returns combined dict {'a':..., 'b':...}.
    """
    result_a = await client.query_repositories(
        messages=format_messages_for_api(messages),
        repositories=repositories_a,
        session_id=session_id,
        genius=genius,
        timeout=timeout,
    )
    result_b = await client.query_repositories(
        messages=format_messages_for_api(messages),
        repositories=repositories_b,
        session_id=session_id,
        genius=genius,
        timeout=timeout,
    )
    return {"a": result_a, "b": result_b}

@ensure_async
async def search_multiple_repositories(
    client: GreptileClient,
    messages: Union[str, List[Dict[str, Any]]],
    repositories: List[Union[Dict[str, str], List[Dict[str, str]]]],
    session_id: Optional[str] = None,
    genius: bool = True,
    timeout: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Same as search_repositories but with flattened repo list.
    """
    agg_repos = flatten_repositories(repositories)
    return await client.search_repositories(
        messages=format_messages_for_api(messages),
        repositories=agg_repos,
        session_id=session_id,
        genius=genius,
    )
