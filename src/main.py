#!/usr/bin/env python3
"""
Greptile MCP Server - Fast Tool Discovery Version
Optimized for Smithery compatibility with lazy loading
"""

import os
import json
import uuid
from typing import Optional, List, Dict, Any
from fastmcp import FastMCP
from mcp.server.fastmcp import Context  # type: ignore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global client instance (lazy loaded)
_greptile_client_global: Optional[Any] = None

async def _get_greptile_client_from_env():
    """Fallback Greptile client when not provided via FastMCP context."""
    global _greptile_client_global
    if _greptile_client_global is None:
        from src.utils import GreptileClient
        
        api_key = os.getenv("GREPTILE_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")
        
        if not api_key:
            raise ValueError("GREPTILE_API_KEY environment variable is required")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
            
        _greptile_client_global = GreptileClient(api_key, github_token)
    
    return _greptile_client_global

# Initialize FastMCP server with minimal configuration for fast tool discovery
_mcp = FastMCP(
    name="Greptile MCP Server",
    instructions="AI-powered code analysis and search using Greptile API"
)

def _extract_client(ctx: Context):
    """Return the GreptileClient either from FastMCP context or env."""
    # The tests store the client at ctx.request_context.lifespan_context.greptile_client
    try:
        return ctx.request_context.lifespan_context.greptile_client  # type: ignore
    except Exception:
        # Fallback to env-based client
        return None

# Public (testable) tool implementations – plain async functions
async def index_repository(
    ctx: Context,
    remote: str,
    repository: str,
    branch: str,
    reload: bool = True,
    notify: bool = False,
) -> str:
    """Index a repository for code search and querying (JSON string)."""

    client = _extract_client(ctx)
    if client is None:
        client = await _get_greptile_client_from_env()

    try:
        result = await client.index_repository(remote, repository, branch, reload, notify)
        return json.dumps(result)
    except Exception as e:
        return f"Error indexing repository: {str(e)}"

async def query_repository(
    ctx: Context,
    query: str,
    repositories: List[Dict[str, Any]],
    session_id: Optional[str] = None,
    stream: bool = False,
    genius: bool = True,
    timeout: Optional[float] = None,
    previous_messages: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Query repositories and return answer / refs as JSON string."""

    client = _extract_client(ctx)
    if client is None:
        client = await _get_greptile_client_from_env()

    # Build session & messages as expected by utils
    sid = session_id or str(uuid.uuid4())
    # Build messages with an explicit id for deterministic testing
    messages = (previous_messages or []) + [{"id": "msg_0", "role": "user", "content": query}]

    try:
        if stream:
            chunks = []
            async for chunk in client.stream_query_repositories(
                messages=messages,
                repositories=repositories,
                session_id=sid,
                genius=genius,
                timeout=timeout,
            ):
                chunks.append(chunk)

            result: Dict[str, Any] = {
                "streamed": True,
                "session_id": sid,
                "chunks": chunks,
            }
        else:
            result = await client.query_repositories(
                messages,
                repositories,
                session_id=sid,
                genius=genius,
                timeout=timeout,
            )
            result["session_id"] = sid

        return json.dumps(result)
    except Exception as e:
        return f"Error querying repositories: {str(e)}"

async def search_repository(
    ctx: Context,
    query: str,
    repositories: List[Dict[str, Any]],
    session_id: Optional[str] = None,
    genius: bool = True,
    timeout: Optional[float] = None,
    previous_messages: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Search repositories and return matching files as JSON string."""

    client = _extract_client(ctx)
    if client is None:
        client = await _get_greptile_client_from_env()

    sid = session_id or str(uuid.uuid4())
    # Build messages with an explicit id for deterministic testing
    messages = (previous_messages or []) + [{"id": "msg_0", "role": "user", "content": query}]

    try:
        result = await client.search_repositories(
            messages,
            repositories,
            session_id=sid,
            genius=genius,
        )
        result["session_id"] = sid
        return json.dumps(result)
    except Exception as e:
        return f"Error searching repositories: {str(e)}"

async def get_repository_info(
    ctx: Context,
    remote: str,
    repository: str,
    branch: str,
) -> str:
    """Return repository indexing info as JSON string."""

    client = _extract_client(ctx)
    if client is None:
        client = await _get_greptile_client_from_env()

    repository_id = f"{remote}:{branch}:{repository}"

    try:
        result = await client.get_repository_info(repository_id)
        return json.dumps(result)
    except Exception as e:
        return f"Error getting repository info: {str(e)}"

# Register tools with FastMCP – but keep callable functions for tests
_mcp.tool()(index_repository)
_mcp.tool()(query_repository)
_mcp.tool()(search_repository)
_mcp.tool()(get_repository_info)

# For running as a script
if __name__ == "__main__":
    _mcp.run()
