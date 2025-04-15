from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dotenv import load_dotenv
import asyncio
import json
import os

from src.utils import get_greptile_client

load_dotenv()

# Create a dataclass for our application context
@dataclass
class GreptileContext:
    """Context for the Greptile MCP server."""
    greptile_client: object  # The Greptile API client

@asynccontextmanager
async def greptile_lifespan(server: FastMCP) -> AsyncIterator[GreptileContext]:
    """
    Manages the Greptile client lifecycle.
    
    Args:
        server: The FastMCP server instance
        
    Yields:
        GreptileContext: The context containing the Greptile client
    """
    # Create and return the Greptile client with the helper function in utils.py
    greptile_client = get_greptile_client()
    
    try:
        yield GreptileContext(greptile_client=greptile_client)
    finally:
        # No explicit cleanup needed for the Greptile client
        pass

# Initialize FastMCP server with the Greptile client as context
mcp = FastMCP(
    "mcp-greptile",
    description="MCP server for code search and querying with Greptile API",
    lifespan=greptile_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=os.getenv("PORT", "8050")
)        

@mcp.tool()
async def index_repository(ctx: Context, remote: str, repository: str, branch: str, reload: bool = False, notify: bool = False) -> str:
    """Index a repository for code search and querying.
    
    This tool initiates the processing of a repository, making it available for future queries.
    A repository must be indexed before it can be queried or searched.
    
    Args:
        ctx: The MCP server provided context which includes the Greptile client
        remote: The repository host, either "github" or "gitlab"
        repository: The repository in owner/repo format (e.g., "coleam00/mcp-mem0")
        branch: The branch to index (e.g., "main")
        reload: Whether to force reprocessing of the repository (default: False)
        notify: Whether to send an email notification when indexing is complete (default: False)
    """
    try:
        greptile_client = ctx.request_context.lifespan_context.greptile_client
        result = greptile_client.index_repository(remote, repository, branch, reload, notify)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error indexing repository: {str(e)}"

@mcp.tool()
async def query_repository(ctx: Context, query: str, repositories: list, session_id: str = None, stream: bool = False, genius: bool = True) -> str:
    """Query repositories to get an answer with code references.
    
    This tool submits a natural language query to get an answer with relevant code references
    from the specified repositories. The repositories must have been indexed first.
    
    Args:
        ctx: The MCP server provided context which includes the Greptile client
        query: The natural language query about the codebase
        repositories: List of repositories to query, each with format {"remote": "github", "repository": "owner/repo", "branch": "main"}
        session_id: Optional session ID for continuing a conversation
        stream: Whether to stream the response (default: False)
        genius: Whether to use the enhanced query capabilities (default: True)
    """
    try:
        greptile_client = ctx.request_context.lifespan_context.greptile_client
        messages = [{"role": "user", "content": query}]
        result = greptile_client.query_repositories(messages, repositories, session_id, stream, genius)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error querying repositories: {str(e)}"

@mcp.tool()
async def search_repository(ctx: Context, query: str, repositories: list, session_id: str = None, genius: bool = True) -> str:
    """Search repositories for relevant files without generating a full answer.
    
    This tool returns a list of relevant files based on a query without generating
    a complete answer. The repositories must have been indexed first.
    
    Args:
        ctx: The MCP server provided context which includes the Greptile client
        query: The natural language query about the codebase
        repositories: List of repositories to search, each with format {"remote": "github", "repository": "owner/repo", "branch": "main"}
        session_id: Optional session ID for continuing a conversation
        genius: Whether to use the enhanced search capabilities (default: True)
    """
    try:
        greptile_client = ctx.request_context.lifespan_context.greptile_client
        messages = [{"role": "user", "content": query}]
        result = greptile_client.search_repositories(messages, repositories, session_id, genius)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error searching repositories: {str(e)}"

@mcp.tool()
async def get_repository_info(ctx: Context, remote: str, repository: str, branch: str) -> str:
    """Get information about an indexed repository.
    
    This tool retrieves information about a specific repository that has been indexed,
    including its status and other metadata.
    
    Args:
        ctx: The MCP server provided context which includes the Greptile client
        remote: The repository host, either "github" or "gitlab"
        repository: The repository in owner/repo format (e.g., "coleam00/mcp-mem0")
        branch: The branch that was indexed (e.g., "main")
    """
    try:
        greptile_client = ctx.request_context.lifespan_context.greptile_client
        repository_id = f"{remote}:{branch}:{repository}"
        result = greptile_client.get_repository_info(repository_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting repository info: {str(e)}"

async def main():
    transport = os.getenv("TRANSPORT", "sse")
    if transport == 'sse':
        # Run the MCP server with sse transport
        await mcp.run_sse_async()
    else:
        # Run the MCP server with stdio transport
        await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())