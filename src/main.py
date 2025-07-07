#!/usr/bin/env python3
"""
Modern Greptile MCP Server using FastMCP 2.0
Provides code search and querying capabilities through the Greptile API.
"""

import os
import asyncio
import uuid
import json
from typing import Optional
from fastmcp import FastMCP
from src.utils import (
    GreptileClient,
    validate_repositories,
    format_messages_for_api,
    query_multiple_repositories,
    compare_repositories,
    search_multiple_repositories,
)
import uuid
import functools
import json

# Session manager is now always present
from src.utils import SessionManager
session_manager = SessionManager()

# Create the modern MCP server
mcp = FastMCP(
    name="Greptile MCP Server",
    instructions="Modern MCP server for code search and querying with Greptile API",
    session_manager=session_manager,
)

# Global client instance (will be initialized on first use)
_greptile_client: Optional[GreptileClient] = None

async def get_greptile_client() -> GreptileClient:
    """Get or create the Greptile client instance."""
    global _greptile_client
    if _greptile_client is None:
        api_key = os.getenv("GREPTILE_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")
        
        if not api_key:
            raise ValueError("GREPTILE_API_KEY environment variable is required")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
            
        _greptile_client = GreptileClient(api_key, github_token)
    
    return _greptile_client

def require_initialized(func):
    """
    Decorator that checks if greptile client is initialized. If not, raises ValueError.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        client = await get_greptile_client()
        if client is None:
            raise ValueError("Greptile client is not initialized")
        return await func(*args, **kwargs)
    return wrapper

@mcp.tool
@require_initialized
async def index_repository(
    remote: str,
    repository: str, 
    branch: str,
    reload: bool = True,
    notify: bool = False
) -> str:
    """
    Index a repository for code search and querying.
    
    Args:
        remote: The repository host ("github" or "gitlab")
        repository: Repository in owner/repo format (e.g., "greptileai/greptile")
        branch: The branch to index (e.g., "main")
        reload: Whether to force reprocessing of a previously indexed repository (default: True)
        notify: Whether to send an email notification when indexing is complete
    
    Returns:
        Dictionary containing indexing status and information
    """
    client = await get_greptile_client()
    
    try:
        result = await client.index_repository(
            remote=remote,
            repository=repository,
            branch=branch,
            reload=reload,
            notify=notify
        )
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})

@mcp.tool
async def query_repository(
    query: str,
    repositories: str,  # JSON string instead of List[Dict[str, str]]
    session_id: Optional[str] = None,
    stream: bool = False,
    genius: bool = True,
    timeout: Optional[float] = None,
    previous_messages: Optional[str] = None  # JSON string instead of List[Dict[str, Any]]
) -> str:  # Simplified return type
    """
    Query repositories to get answers with code references.

    Args:
        query: The natural language query about the codebase
        repositories: JSON string of repositories to query (e.g., '[{"remote":"github","repository":"owner/repo","branch":"main"}]')
        session_id: Optional session ID for conversation continuity
        stream: Whether to stream the response (default: False)
        genius: Whether to use enhanced query capabilities (default: True)
        timeout: Optional timeout for the request in seconds
        previous_messages: Optional JSON string of previous messages for context

    Returns:
        JSON string containing the answer and source code references
    """
    client = await get_greptile_client()

    # Parse JSON parameters
    try:
        repositories_list = json.loads(repositories) if repositories else []
        previous_messages_list = json.loads(previous_messages) if previous_messages else None
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON in parameters: {str(e)}", "type": "JSONDecodeError"})

    # Generate session ID if not provided
    if session_id is None:
        session_id = str(uuid.uuid4())

    try:
        # Convert query to messages format
        messages = [{"role": "user", "content": query}]
        if previous_messages_list:
            messages = previous_messages_list + messages

        if stream:
            # For streaming, collect all chunks and return as complete response
            chunks = []
            async for chunk in client.stream_query_repositories(
                messages=messages,
                repositories=repositories_list,
                session_id=session_id,
                genius=genius,
                timeout=timeout
            ):
                chunks.append(chunk)

            # Combine chunks into final response
            result = {"message": "".join(chunks), "session_id": session_id, "streamed": True}
        else:
            result = await client.query_repositories(
                messages=messages,
                repositories=repositories_list,
                session_id=session_id,
                genius=genius,
                timeout=timeout
            )
            result["session_id"] = session_id

        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__, "session_id": session_id})

@mcp.tool
@require_initialized
async def search_repository(
    query: str,
    repositories: str,  # JSON string instead of List[Dict[str, str]]
    session_id: Optional[str] = None,
    genius: bool = False,
    timeout: Optional[float] = None,
    previous_messages: Optional[str] = None  # JSON string instead of List[Dict[str, Any]]
) -> str:  # Simplified return type
    """
    Search repositories to find relevant files without generating a full answer.

    Args:
        query: The search query about the codebase
        repositories: JSON string of repositories to search (e.g., '[{"remote":"github","repository":"owner/repo","branch":"main"}]')
        session_id: Optional session ID for conversation continuity
        genius: Whether to use enhanced search capabilities (default: False)
        timeout: Optional timeout for the request in seconds
        previous_messages: Optional JSON string of previous messages for context

    Returns:
        JSON string containing relevant files and code references
    """
    client = await get_greptile_client()

    # Parse JSON parameters
    try:
        repositories_list = json.loads(repositories) if repositories else []
        previous_messages_list = json.loads(previous_messages) if previous_messages else None
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON in parameters: {str(e)}", "type": "JSONDecodeError"})

    # Generate session ID if not provided
    if session_id is None:
        session_id = str(uuid.uuid4())

    try:
        # Convert query to messages format
        messages = [{"role": "user", "content": query}]
        if previous_messages_list:
            messages = previous_messages_list + messages

        result = await client.search_repositories(
            messages=messages,
            repositories=repositories_list,
            session_id=session_id,
            genius=genius,
            timeout=timeout
        )
        result["session_id"] = session_id
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__, "session_id": session_id})

@mcp.tool
@require_initialized
async def get_repository_info(
    remote: str,
    repository: str,
    branch: str
) -> str:
    """
    Get information about an indexed repository.

    Args:
        remote: The repository host ("github" or "gitlab")
        repository: Repository in owner/repo format
        branch: The branch that was indexed

    Returns:
        JSON string containing repository information and indexing status
    """
    client = await get_greptile_client()

    try:
        result = await client.get_repository_info(
            remote=remote,
            repository=repository,
            branch=branch
        )
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})

# --- New FastMCP Tools for batch/multi/compare repo support ---

@mcp.tool
@require_initialized
async def query_multiple_repositories(
    messages_or_query: str,
    repositories: str,  # JSON string; can be list-of-list
    session_id: Optional[str] = None,
    stream: bool = False,
    genius: bool = True,
    timeout: Optional[float] = None
) -> str:
    """
    Query multiple repositories (optionally batched) using the Greptile API.

    Args:
        messages_or_query: Either a user query (str) or a JSON-encoded list of message dicts
        repositories: JSON string; may be list-of-list of repo dicts
        session_id: Optional session ID for conversation
        stream: Whether to stream the response
        genius: Use enhanced query mode (default: True)
        timeout: Optional timeout in seconds

    Returns:
        JSON string result
    """
    client = await get_greptile_client()
    try:
        repos = json.loads(repositories) if repositories else []
        validate_repositories(flatten_repositories(repos))
        messages = format_messages_for_api(messages_or_query)
        if session_id is None:
            session_id = str(uuid.uuid4())
        result = await query_multiple_repositories(
            client=client,
            messages=messages,
            repositories=repos,
            session_id=session_id,
            stream=stream,
            genius=genius,
            timeout=timeout
        )
        result["session_id"] = session_id
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})

@mcp.tool
@require_initialized
async def compare_repositories(
    messages_or_query: str,
    repositories_a: str,  # JSON string of list[repo]
    repositories_b: str,  # JSON string of list[repo]
    session_id: Optional[str] = None,
    genius: bool = True,
    timeout: Optional[float] = None
) -> str:
    """
    Compare two sets of repositories using the Greptile API.

    Args:
        messages_or_query: Either a user query (str) or a JSON-encoded list of message dicts
        repositories_a: JSON string of first repo set
        repositories_b: JSON string of second repo set
        session_id: Optional session ID for conversation
        genius: Use enhanced query mode (default: True)
        timeout: Optional timeout in seconds

    Returns:
        JSON string result as { "a": ..., "b": ... }
    """
    client = await get_greptile_client()
    try:
        repos_a = json.loads(repositories_a) if repositories_a else []
        repos_b = json.loads(repositories_b) if repositories_b else []
        validate_repositories(repos_a)
        validate_repositories(repos_b)
        messages = format_messages_for_api(messages_or_query)
        if session_id is None:
            session_id = str(uuid.uuid4())
        result = await compare_repositories(
            client=client,
            messages=messages,
            repositories_a=repos_a,
            repositories_b=repos_b,
            session_id=session_id,
            genius=genius,
            timeout=timeout
        )
        result["session_id"] = session_id
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})

@mcp.tool
@require_initialized
async def search_multiple_repositories(
    messages_or_query: str,
    repositories: str,  # JSON string, may be list-of-list
    session_id: Optional[str] = None,
    genius: bool = True,
    timeout: Optional[float] = None
) -> str:
    """
    Search across multiple repositories (optionally batched) using the Greptile API.

    Args:
        messages_or_query: Either a user query (str) or a JSON-encoded list of message dicts
        repositories: JSON string; may be list-of-list of repo dicts
        session_id: Optional session ID for conversation
        genius: Use enhanced search mode (default: True)
        timeout: Optional timeout in seconds

    Returns:
        JSON string result
    """
    client = await get_greptile_client()
    try:
        repos = json.loads(repositories) if repositories else []
        validate_repositories(flatten_repositories(repos))
        messages = format_messages_for_api(messages_or_query)
        if session_id is None:
            session_id = str(uuid.uuid4())
        result = await search_multiple_repositories(
            client=client,
            messages=messages,
            repositories=repos,
            session_id=session_id,
            genius=genius,
            timeout=timeout
        )
        result["session_id"] = session_id
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})

# Cleanup function for graceful shutdown
async def cleanup():
    """Clean up resources on server shutdown."""
    global _greptile_client
    if _greptile_client:
        await _greptile_client.aclose()
        _greptile_client = None

if __name__ == "__main__":
    # Register cleanup handler
    import atexit
    atexit.register(lambda: asyncio.run(cleanup()))
    
    # Run the server
    mcp.run()
