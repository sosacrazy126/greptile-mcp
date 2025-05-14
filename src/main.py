from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dotenv import load_dotenv
import asyncio
import json
import os
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator, Union

from src.utils import (
    get_greptile_client,
    SessionManager,
    generate_session_id
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create a dataclass for our application context
@dataclass
class GreptileContext:
    """Context for the Greptile MCP server."""
    greptile_client: GreptileClient  # The Greptile API client
    initialized: bool = False  # Track if initialization is complete
    session_manager: Optional[SessionManager] = None  # Add session manager for conversation context

@asynccontextmanager
async def greptile_lifespan(server: FastMCP) -> AsyncIterator[GreptileContext]:
    """
    Manages the Greptile client lifecycle and session/conv context.

    Args:
        server: The FastMCP server instance

    Yields:
        GreptileContext: The context containing the Greptile client and session manager
    """
    greptile_client = get_greptile_client()
    session_manager = SessionManager()
    context = GreptileContext(greptile_client=greptile_client, initialized=False, session_manager=session_manager)

    try:
        print("Initializing Greptile client...")
        try:
            await asyncio.sleep(0.5)
            context.initialized = True
            print("Greptile client successfully initialized")
        except Exception as e:
            print(f"Error during Greptile client initialization: {e}")
            raise

        yield context
    finally:
        await greptile_client.aclose()
        print("Greptile client closed.")

# Initialize FastMCP server with the Greptile client and session manager as context
mcp = FastMCP(
    "mcp-greptile",
    description="MCP server for code search and querying with Greptile API",
    lifespan=greptile_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=os.getenv("PORT", "8050")
)        

def format_messages_for_api(messages: List[Union[Dict, str]], current_query: str = None) -> List[Dict[str, str]]:
    """
    Format messages to match the Greptile API specification.
    
    Args:
        messages: List of messages in various formats
        current_query: Optional current query to append
    
    Returns:
        List of properly formatted messages with id, content, and role
    """
    formatted_messages = []
    
    for idx, msg in enumerate(messages):
        if isinstance(msg, dict):
            # Ensure proper format
            formatted_msg = {
                "id": msg.get("id", f"msg_{idx}"),
                "content": msg.get("content", ""),
                "role": msg.get("role", "user")
            }
            formatted_messages.append(formatted_msg)
        else:
            # Handle string messages
            formatted_messages.append({
                "id": f"msg_{idx}",
                "content": str(msg),
                "role": "user"
            })
    
    # Add current query if provided
    if current_query:
        formatted_messages.append({
            "id": f"msg_{len(formatted_messages)}",
            "content": current_query,
            "role": "user"
        })
    
    return formatted_messages

@mcp.tool()
async def index_repository(ctx: Context, remote: str, repository: str, branch: str, reload: bool = True, notify: bool = False) -> str:
    """Index a repository for code search and querying.
    
    This tool initiates the processing of a repository, making it available for future queries.
    A repository must be indexed before it can be queried or searched.
    
    Args:
        ctx: The MCP server provided context which includes the Greptile client
        remote: The repository host, either "github" or "gitlab"
        repository: The repository in owner/repo format (e.g., "coleam00/mcp-mem0")
        branch: The branch to index (e.g., "main")
        reload: Whether to force reprocessing of the repository (default: True). 
                When False, won't reprocess if previously indexed successfully.
        notify: Whether to send an email notification when indexing is complete (default: False)
    """
    try:
        greptile_context = ctx.request_context.lifespan_context
        
        # Check if initialization is complete
        if not getattr(greptile_context, 'initialized', False):
            return json.dumps({
                "error": "Server initialization is not complete. Please try again in a moment.",
                "status": "initializing"
            }, indent=2)
            
        greptile_client = greptile_context.greptile_client
        result = await greptile_client.index_repository(remote, repository, branch, reload, notify)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error indexing repository: {str(e)}"

@mcp.tool()
async def query_repository(
    ctx: Context,
    query: str,
    repositories: list,
    session_id: Optional[str] = None,
    stream: bool = False,
    genius: bool = True,
    timeout: Optional[float] = None,
    messages: Optional[List[Dict[str, str]]] = None
) -> Union[str, AsyncGenerator[str, None]]:
    """
    Query repositories to get an answer with code references.

    Supports both single-turn and multi-turn (conversational) context with full message history.

    Args:
        ctx: MCP server provided context
        query: The natural language query about the codebase
        repositories: List of repositories to query
        session_id: Used for multi-turn conversations; generates new if not provided
        stream: Enable streaming for long queries (returns async generator)
        genius: Use enhanced answer quality (may take longer)
        timeout: Optional per-query timeout (seconds)
        messages: Optional message history in the format [{"id": "msg1", "content": "...", "role": "user/assistant"}]
                 This follows the official Greptile API format for messages

    Returns:
        - For streaming: async generator yielding JSON strings.
        - For non-streaming: formatted JSON string (single result).
    """
    try:
        greptile_context = ctx.request_context.lifespan_context
        if not getattr(greptile_context, 'initialized', False):
            return json.dumps({
                "error": "Server initialization is not complete. Please try again in a moment.",
                "status": "initializing"
            }, indent=2)

        greptile_client = greptile_context.greptile_client
        session_manager: SessionManager = greptile_context.session_manager

        # Session logic
        sid = session_id or generate_session_id()
        
        # Build message history
        if messages is not None:
            # If messages are provided, ensure they have the correct format
            formatted_messages = []
            for idx, msg in enumerate(messages):
                if isinstance(msg, dict):
                    # Ensure each message has an id
                    formatted_msg = {
                        "id": msg.get("id", f"msg_{idx}"),
                        "content": msg.get("content", ""),
                        "role": msg.get("role", "user")
                    }
                    formatted_messages.append(formatted_msg)
                else:
                    # Handle legacy string format
                    formatted_messages.append({
                        "id": f"msg_{idx}",
                        "content": str(msg),
                        "role": "user"
                    })
            
            # Add the current query as the latest message
            query_msg = {
                "id": f"msg_{len(formatted_messages)}",
                "content": query,
                "role": "user"
            }
            formatted_messages.append(query_msg)
            await session_manager.set_history(sid, formatted_messages)
        else:
            # Retrieve stored history or start new conversation
            history = await session_manager.get_history(sid)
            # Add the current query
            query_msg = {
                "id": f"msg_{len(history)}",
                "content": query,
                "role": "user"
            }
            formatted_messages = history + [query_msg]
            await session_manager.set_history(sid, formatted_messages)

        # Handle streaming response
        if stream:
            async def streaming_gen() -> AsyncGenerator[str, None]:
                async for chunk in greptile_client.stream_query_repositories(
                    formatted_messages, repositories, session_id=sid, genius=genius, timeout=timeout
                ):
                    # Optionally, add chunk/response to session history (system/assistant)
                    # If Greptile API returns role/content, could append to session
                    yield json.dumps(chunk)
            return streaming_gen()

        # Non-streaming query; get response fully then append to session history
        result = await greptile_client.query_repositories(
            formatted_messages, repositories, session_id=sid, stream=False, genius=genius, timeout=timeout
        )

        # Persist new assistant/content response in session history if return has role/content fields
        if "messages" in result:
            # If API returns messages array, update session
            await session_manager.set_history(sid, result["messages"])
        elif "message" in result:
            # If API returns a message string, append it as assistant response
            assistant_msg = {
                "id": f"msg_{len(formatted_messages)}",
                "content": result["message"],
                "role": "assistant"
            }
            await session_manager.append_message(sid, assistant_msg)
        elif "output" in result:
            # Legacy format support
            assistant_msg = {
                "id": f"msg_{len(formatted_messages)}",
                "content": result["output"],
                "role": "assistant"
            }
            await session_manager.append_message(sid, assistant_msg)

        # Attach the session_id for client reference
        result["_session_id"] = sid
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error querying repositories: {str(e)}"

@mcp.tool()
async def search_repository(
    ctx: Context, 
    query: str, 
    repositories: list, 
    session_id: str = None, 
    genius: bool = True,
    messages: Optional[List[Dict[str, str]]] = None
) -> str:
    """Search repositories for relevant files without generating a full answer.
    
    This tool returns a list of relevant files based on a query without generating
    a complete answer. The repositories must have been indexed first.
    
    Args:
        ctx: The MCP server provided context which includes the Greptile client
        query: The natural language query about the codebase
        repositories: List of repositories to search, each with format {"remote": "github", "repository": "owner/repo", "branch": "main"}
        session_id: Optional session ID for continuing a conversation
        genius: Whether to use the enhanced search capabilities (default: True)
        messages: Optional message history in the format [{"id": "msg1", "content": "...", "role": "user/assistant"}]
    """
    try:
        greptile_context = ctx.request_context.lifespan_context
        
        # Check if initialization is complete
        if not getattr(greptile_context, 'initialized', False):
            return json.dumps({
                "error": "Server initialization is not complete. Please try again in a moment.",
                "status": "initializing"
            }, indent=2)
            
        greptile_client = greptile_context.greptile_client
        
        # Format messages properly
        if messages is not None:
            # Use provided message history
            formatted_messages = []
            for idx, msg in enumerate(messages):
                if isinstance(msg, dict):
                    formatted_msg = {
                        "id": msg.get("id", f"msg_{idx}"),
                        "content": msg.get("content", ""),
                        "role": msg.get("role", "user")
                    }
                    formatted_messages.append(formatted_msg)
            # Add current query
            formatted_messages.append({
                "id": f"msg_{len(formatted_messages)}",
                "content": query,
                "role": "user"
            })
        else:
            # Create a simple message list with just the query
            formatted_messages = [{
                "id": "msg_0",
                "content": query,
                "role": "user"
            }]
        
        result = await greptile_client.search_repositories(formatted_messages, repositories, session_id, genius)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error searching repositories: {str(e)}"

@mcp.tool()
async def get_repository_info(ctx: Context, remote: str, repository: str, branch: str) -> str:
    """Get information about an indexed repository.
    
    This tool retrieves information about a specific repository that has been indexed,
    including its status and other metadata.
    
    The tool handles proper URL encoding internally to ensure repository identifiers
    with special characters (like '/') are correctly processed.
    
    Args:
        ctx: The MCP server provided context which includes the Greptile client
        remote: The repository host, either "github" or "gitlab"
        repository: The repository in owner/repo format (e.g., "coleam00/mcp-mem0")
        branch: The branch that was indexed (e.g., "main")
        
    Returns:
        A JSON string containing repository information such as status, last indexed time,
        and other metadata. If the repository is still being indexed, the status will 
        indicate the current progress.
        
    Example Response:
        {
          "id": "github:main:owner/repo",
          "status": "COMPLETED",
          "repository": "owner/repo",
          "remote": "github",
          "branch": "main",
          "private": false,
          "filesProcessed": 234,
          "numFiles": 234
        }
    """
    try:
        greptile_context = ctx.request_context.lifespan_context
        
        # Check if initialization is complete
        if not getattr(greptile_context, 'initialized', False):
            return json.dumps({
                "error": "Server initialization is not complete. Please try again in a moment.",
                "status": "initializing"
            }, indent=2)
            
        greptile_client = greptile_context.greptile_client
        repository_id = f"{remote}:{branch}:{repository}"
        result = await greptile_client.get_repository_info(repository_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting repository info: {str(e)}"

@mcp.tool()
async def query_repository_advanced(
    ctx: Context,
    messages: List[Dict[str, str]],
    repositories: list,
    session_id: Optional[str] = None,
    stream: bool = False,
    genius: bool = True,
    timeout: Optional[float] = None
) -> Union[str, AsyncGenerator[str, None]]:
    """
    Advanced query with full message history support following Greptile API format.
    
    This is the most flexible query method that directly maps to the Greptile API.
    
    Args:
        ctx: MCP server provided context
        messages: Full message history in Greptile API format: [{"id": "msg1", "content": "...", "role": "user/assistant"}]
        repositories: List of repositories to query
        session_id: Used for multi-turn conversations; generates new if not provided
        stream: Enable streaming for long queries (returns async generator)
        genius: Use enhanced answer quality (may take longer)
        timeout: Optional per-query timeout (seconds)
    
    Returns:
        - For streaming: async generator yielding JSON strings.
        - For non-streaming: formatted JSON string (single result).
    """
    try:
        greptile_context = ctx.request_context.lifespan_context
        if not getattr(greptile_context, 'initialized', False):
            return json.dumps({
                "error": "Server initialization is not complete. Please try again in a moment.",
                "status": "initializing"
            }, indent=2)

        greptile_client = greptile_context.greptile_client
        session_manager: SessionManager = greptile_context.session_manager

        # Session logic
        sid = session_id or generate_session_id()
        
        # Store the message history
        await session_manager.set_history(sid, messages)

        # Handle streaming response
        if stream:
            async def streaming_gen() -> AsyncGenerator[str, None]:
                async for chunk in greptile_client.stream_query_repositories(
                    messages, repositories, session_id=sid, genius=genius, timeout=timeout
                ):
                    yield json.dumps(chunk)
            return streaming_gen()

        # Non-streaming query
        result = await greptile_client.query_repositories(
            messages, repositories, session_id=sid, stream=False, genius=genius, timeout=timeout
        )

        # Update session history with response
        if "messages" in result:
            await session_manager.set_history(sid, result["messages"])
        elif "message" in result:
            # Append assistant response
            assistant_msg = {
                "id": f"msg_{len(messages)}",
                "content": result["message"],
                "role": "assistant"
            }
            await session_manager.append_message(sid, assistant_msg)

        # Attach the session_id for client reference
        result["_session_id"] = sid
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error querying repositories: {str(e)}"

@mcp.tool()
async def query_simple(
    ctx: Context,
    query: str,
    repositories: list,
    genius: bool = True
) -> str:
    """
    Simple single-turn query without session management.
    
    This is the easiest way to query repositories for one-off questions.
    
    Args:
        ctx: MCP server provided context
        query: The natural language query about the codebase
        repositories: List of repositories to query
        genius: Use enhanced answer quality (default: True)
    
    Returns:
        JSON string with the query result
    """
    # Create a single message
    messages = [{
        "id": "query_0",
        "content": query,
        "role": "user"
    }]
    
    return await query_repository_advanced(
        ctx=ctx,
        messages=messages,
        repositories=repositories,
        session_id=None,
        stream=False,
        genius=genius,
        timeout=None
    )

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
