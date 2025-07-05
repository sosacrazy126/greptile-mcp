#!/usr/bin/env python3
"""
Modern Greptile MCP Server using FastMCP 2.0
Provides code search and querying capabilities through the Greptile API.
"""

import os
import asyncio
import uuid
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP
from .utils import GreptileClient

# Create the modern MCP server
mcp = FastMCP(
    name="Greptile MCP Server",
    instructions="Modern MCP server for code search and querying with Greptile API"
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

@mcp.tool
async def index_repository(
    remote: str,
    repository: str, 
    branch: str,
    reload: bool = False,
    notify: bool = False
) -> Dict[str, Any]:
    """
    Index a repository for code search and querying.
    
    Args:
        remote: The repository host ("github" or "gitlab")
        repository: Repository in owner/repo format (e.g., "greptileai/greptile")
        branch: The branch to index (e.g., "main")
        reload: Whether to force reprocessing of a previously indexed repository
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
        return result
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

@mcp.tool
async def query_repository(
    query: str,
    repositories: List[Dict[str, str]],
    session_id: Optional[str] = None,
    stream: bool = False,
    genius: bool = True,
    timeout: Optional[float] = None,
    previous_messages: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Query repositories to get answers with code references.
    
    Args:
        query: The natural language query about the codebase
        repositories: List of repositories to query, each with remote, repository, and branch
        session_id: Optional session ID for conversation continuity
        stream: Whether to stream the response (default: False)
        genius: Whether to use enhanced query capabilities (default: True)
        timeout: Optional timeout for the request in seconds
        previous_messages: Optional list of previous messages for context
    
    Returns:
        Dictionary containing the answer and source code references
    """
    client = await get_greptile_client()
    
    # Generate session ID if not provided
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    try:
        if stream:
            # For streaming, collect all chunks and return as complete response
            chunks = []
            async for chunk in client.stream_query_repositories(
                query=query,
                repositories=repositories,
                session_id=session_id,
                genius=genius,
                timeout=timeout,
                previous_messages=previous_messages
            ):
                chunks.append(chunk)
            
            # Combine chunks into final response
            result = {"message": "".join(chunks), "session_id": session_id, "streamed": True}
        else:
            result = await client.query_repositories(
                query=query,
                repositories=repositories,
                session_id=session_id,
                genius=genius,
                timeout=timeout,
                previous_messages=previous_messages
            )
            result["session_id"] = session_id
            
        return result
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__, "session_id": session_id}

@mcp.tool
async def search_repository(
    query: str,
    repositories: List[Dict[str, str]],
    session_id: Optional[str] = None,
    genius: bool = True,
    timeout: Optional[float] = None,
    previous_messages: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Search repositories to find relevant files without generating a full answer.
    
    Args:
        query: The search query about the codebase
        repositories: List of repositories to search
        session_id: Optional session ID for conversation continuity
        genius: Whether to use enhanced search capabilities (default: True)
        timeout: Optional timeout for the request in seconds
        previous_messages: Optional list of previous messages for context
    
    Returns:
        Dictionary containing relevant files and code references
    """
    client = await get_greptile_client()
    
    # Generate session ID if not provided
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    try:
        result = await client.search_repositories(
            query=query,
            repositories=repositories,
            session_id=session_id,
            genius=genius,
            timeout=timeout,
            previous_messages=previous_messages
        )
        result["session_id"] = session_id
        return result
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__, "session_id": session_id}

@mcp.tool
async def get_repository_info(
    remote: str,
    repository: str,
    branch: str
) -> Dict[str, Any]:
    """
    Get information about an indexed repository.
    
    Args:
        remote: The repository host ("github" or "gitlab")
        repository: Repository in owner/repo format
        branch: The branch that was indexed
    
    Returns:
        Dictionary containing repository information and indexing status
    """
    client = await get_greptile_client()
    
    try:
        result = await client.get_repository_info(
            remote=remote,
            repository=repository,
            branch=branch
        )
        return result
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

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
