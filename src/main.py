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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global client instance (lazy loaded)
_greptile_client: Optional[Any] = None

async def get_greptile_client():
    """Lazy load the Greptile client only when needed."""
    global _greptile_client
    if _greptile_client is None:
        from src.utils import GreptileClient
        
        api_key = os.getenv("GREPTILE_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")
        
        if not api_key:
            raise ValueError("GREPTILE_API_KEY environment variable is required")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
            
        _greptile_client = GreptileClient(api_key, github_token)
    
    return _greptile_client

# Initialize FastMCP server with minimal configuration for fast tool discovery
mcp = FastMCP(
    name="Greptile MCP Server",
    instructions="AI-powered code analysis and search using Greptile API"
)

@mcp.tool
async def index_repository(
    remote: str,
    repository: str,
    branch: str,
    reload: bool = False,
    notify: bool = False
) -> str:
    """
    Index a repository for code search and querying.
    
    Args:
        remote: The repository host ("github" or "gitlab")
        repository: Repository in owner/repo format
        branch: The branch to index
        reload: Whether to force reprocessing
        notify: Whether to send email notification
    
    Returns:
        JSON string with indexing status
    """
    try:
        client = await get_greptile_client()
        result = await client.index_repository(remote, repository, branch, reload, notify)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})

@mcp.tool
async def query_repository(
    query: str,
    repositories: str,
    session_id: Optional[str] = None,
    stream: bool = False,
    genius: bool = True,
    timeout: Optional[float] = None,
    previous_messages: Optional[str] = None
) -> str:
    """
    Query repositories to get answers with code references.
    
    Args:
        query: The natural language query about the codebase
        repositories: JSON string of repositories to query
        session_id: Optional session ID for conversation continuity
        stream: Whether to stream the response
        genius: Whether to use enhanced query capabilities
        timeout: Optional timeout for the request in seconds
        previous_messages: Optional JSON string of previous messages for context
    
    Returns:
        JSON string containing the answer and source code references
    """
    try:
        client = await get_greptile_client()
        
        # Parse JSON parameters
        repositories_list = json.loads(repositories) if repositories else []
        previous_messages_list = json.loads(previous_messages) if previous_messages else None
        
        # Generate session ID if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())
        
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
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON in parameters: {str(e)}", "type": "JSONDecodeError"})
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__, "session_id": session_id})

@mcp.tool
async def search_repository(
    query: str,
    repositories: str,
    session_id: Optional[str] = None,
    genius: bool = True,
    timeout: Optional[float] = None,
    previous_messages: Optional[str] = None
) -> str:
    """
    Search repositories to find relevant files without generating a full answer.
    
    Args:
        query: The search query about the codebase
        repositories: JSON string of repositories to search
        session_id: Optional session ID for conversation continuity
        genius: Whether to use enhanced search capabilities
        timeout: Optional timeout for the request in seconds
        previous_messages: Optional JSON string of previous messages for context
    
    Returns:
        JSON string containing relevant files and code references
    """
    try:
        client = await get_greptile_client()
        
        # Parse JSON parameters
        repositories_list = json.loads(repositories) if repositories else []
        previous_messages_list = json.loads(previous_messages) if previous_messages else None
        
        # Generate session ID if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())
        
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
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON in parameters: {str(e)}", "type": "JSONDecodeError"})
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__, "session_id": session_id})

@mcp.tool
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
    try:
        client = await get_greptile_client()
        result = await client.get_repository_info(remote, repository, branch)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})

if __name__ == "__main__":
    mcp.run()
