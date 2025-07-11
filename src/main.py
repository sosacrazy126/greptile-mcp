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
from src.utils import GreptileClient
from src.validation import InputValidator, create_validation_error_response, create_error_response
from src.logging_config import logger, log_execution_time, APICallLogger
from src.rate_limiting import rate_limited_request, RateLimitExceeded

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
            logger.error("Missing GREPTILE_API_KEY environment variable")
            raise ValueError("GREPTILE_API_KEY environment variable is required")
        if not github_token:
            logger.error("Missing GITHUB_TOKEN environment variable")
            raise ValueError("GITHUB_TOKEN environment variable is required")

        logger.info("Initializing Greptile client")
        _greptile_client = GreptileClient(api_key, github_token)
        logger.info("Greptile client initialized successfully")

    return _greptile_client

@mcp.tool
@log_execution_time("index_repository")
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
        repository: Repository in owner/repo format (e.g., "greptileai/greptile")
        branch: The branch to index (e.g., "main")
        reload: Whether to force reprocessing of a previously indexed repository
        notify: Whether to send an email notification when indexing is complete

    Returns:
        Dictionary containing indexing status and information
    """
    # Input validation
    validation_errors = []

    remote_result = InputValidator.validate_remote(remote)
    if not remote_result.is_valid:
        validation_errors.extend(remote_result.errors)

    repo_result = InputValidator.validate_repository(repository)
    if not repo_result.is_valid:
        validation_errors.extend(repo_result.errors)

    branch_result = InputValidator.validate_branch(branch)
    if not branch_result.is_valid:
        validation_errors.extend(branch_result.errors)

    if validation_errors:
        logger.log_validation_error(
            "index_repository",
            "; ".join(validation_errors),
            remote=remote,
            repository=repository,
            branch=branch
        )
        return create_error_response(
            "; ".join(validation_errors),
            "ValidationError"
        )

    # Log warnings if any
    all_warnings = remote_result.warnings + repo_result.warnings + branch_result.warnings
    if all_warnings:
        logger.warning(
            f"Validation warnings for index_repository: {'; '.join(all_warnings)}",
            remote=remote,
            repository=repository,
            branch=branch
        )

    try:
        client = await get_greptile_client()

        logger.info(
            f"Starting repository indexing: {remote}/{repository}@{branch}",
            remote=remote,
            repository=repository,
            branch=branch,
            reload=reload,
            notify=notify
        )

        # Use session_id as rate limit identifier, fallback to repository
        rate_limit_id = f"{remote}/{repository}"

        try:
            async with rate_limited_request(rate_limit_id):
                with APICallLogger("POST", f"/repositories", remote=remote, repository=repository):
                    result = await client.index_repository(
                        remote=remote,
                        repository=repository,
                        branch=branch,
                        reload=reload,
                        notify=notify
                    )
        except RateLimitExceeded as e:
            logger.warning(
                f"Rate limit exceeded for repository indexing",
                remote=remote,
                repository=repository,
                error=str(e)
            )
            return create_error_response(str(e), "RateLimitExceeded")

        logger.info(
            f"Repository indexing completed: {remote}/{repository}@{branch}",
            remote=remote,
            repository=repository,
            branch=branch,
            result=result
        )

        return json.dumps(result)

    except Exception as e:
        logger.log_exception(
            e,
            context="index_repository",
            remote=remote,
            repository=repository,
            branch=branch
        )
        return create_error_response(str(e), type(e).__name__)

@mcp.tool
@log_execution_time("query_repository")
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
    # Input validation
    query_result = InputValidator.validate_query(query)
    if not query_result.is_valid:
        logger.log_validation_error("query", "; ".join(query_result.errors), query=query)
        return create_error_response("; ".join(query_result.errors), "ValidationError", session_id=session_id)

    repositories_result, repositories_list = InputValidator.validate_repositories_json(repositories)
    if not repositories_result.is_valid:
        logger.log_validation_error("repositories", "; ".join(repositories_result.errors), repositories=repositories)
        return create_error_response("; ".join(repositories_result.errors), "ValidationError", session_id=session_id)

    session_result = InputValidator.validate_session_id(session_id)
    if not session_result.is_valid:
        logger.log_validation_error("session_id", "; ".join(session_result.errors), session_id=session_id)
        return create_error_response("; ".join(session_result.errors), "ValidationError", session_id=session_id)

    timeout_result = InputValidator.validate_timeout(timeout)
    if not timeout_result.is_valid:
        logger.log_validation_error("timeout", "; ".join(timeout_result.errors), timeout=timeout)
        return create_error_response("; ".join(timeout_result.errors), "ValidationError", session_id=session_id)

    messages_result, previous_messages_list = InputValidator.validate_messages_json(previous_messages)
    if not messages_result.is_valid:
        logger.log_validation_error("previous_messages", "; ".join(messages_result.errors), previous_messages=previous_messages)
        return create_error_response("; ".join(messages_result.errors), "ValidationError", session_id=session_id)

    # Generate session ID if not provided
    if session_id is None:
        session_id = str(uuid.uuid4())
        logger.debug(f"Generated new session ID: {session_id}")

    # Log warnings
    all_warnings = (query_result.warnings + repositories_result.warnings +
                   session_result.warnings + timeout_result.warnings + messages_result.warnings)
    if all_warnings:
        logger.warning(
            f"Validation warnings for query_repository: {'; '.join(all_warnings)}",
            session_id=session_id,
            query=query[:100] + "..." if len(query) > 100 else query
        )

    try:
        client = await get_greptile_client()

        # Convert query to messages format
        messages = [{"role": "user", "content": query}]
        if previous_messages_list:
            messages = previous_messages_list + messages

        logger.info(
            f"Starting repository query",
            session_id=session_id,
            query=query[:100] + "..." if len(query) > 100 else query,
            repositories_count=len(repositories_list),
            stream=stream,
            genius=genius
        )

        if stream:
            # For streaming, collect all chunks and return as complete response
            chunks = []
            with APICallLogger("POST", "/query", session_id=session_id, stream=True):
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

            logger.info(
                f"Streaming query completed",
                session_id=session_id,
                chunks_received=len(chunks)
            )
        else:
            with APICallLogger("POST", "/query", session_id=session_id, stream=False):
                result = await client.query_repositories(
                    messages=messages,
                    repositories=repositories_list,
                    session_id=session_id,
                    genius=genius,
                    timeout=timeout
                )
            result["session_id"] = session_id

            logger.info(
                f"Query completed",
                session_id=session_id,
                has_sources=bool(result.get("sources")),
                sources_count=len(result.get("sources", []))
            )

        return json.dumps(result)

    except Exception as e:
        logger.log_exception(
            e,
            context="query_repository",
            session_id=session_id,
            query=query[:100] + "..." if len(query) > 100 else query
        )
        return create_error_response(str(e), type(e).__name__, session_id=session_id)

@mcp.tool
async def search_repository(
    query: str,
    repositories: str,  # JSON string instead of List[Dict[str, str]]
    session_id: Optional[str] = None,
    genius: bool = True,
    timeout: Optional[float] = None,
    previous_messages: Optional[str] = None  # JSON string instead of List[Dict[str, Any]]
) -> str:  # Simplified return type
    """
    Search repositories to find relevant files without generating a full answer.

    Args:
        query: The search query about the codebase
        repositories: JSON string of repositories to search (e.g., '[{"remote":"github","repository":"owner/repo","branch":"main"}]')
        session_id: Optional session ID for conversation continuity
        genius: Whether to use enhanced search capabilities (default: True)
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
