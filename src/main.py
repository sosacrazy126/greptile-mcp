#!/usr/bin/env python3
"""
Modern Greptile MCP Server using FastMCP 2.0
Provides code search and querying capabilities through the Greptile API.
"""

import os
import asyncio
import uuid
import json
import time
from typing import Optional, List, Dict, Any
from fastmcp import FastMCP
from src.utils import GreptileClient, generate_session_id, normalize_session_id
from src.validation import InputValidator, create_error_response
from src.logging_config import logger, log_execution_time, APICallLogger
from src.rate_limiting import rate_limited_request, RateLimitExceeded
from src.orchestration.tools import (
    analyze_codebase_feature,
    compare_codebase_patterns,
    explore_codebase_autonomous
)
from src.flow_enhancement import (
    ContinuationPromptsGenerator,
    SessionPersistenceManager
)

# Create the modern MCP server
mcp = FastMCP(
    name="Greptile MCP Server",
    instructions="Modern MCP server for code search and querying with Greptile API"
)

# Initialize flow enhancement components
continuation_generator = ContinuationPromptsGenerator()
session_manager = SessionPersistenceManager()

def enhance_response_with_flow_guidance(
    response_dict: Dict[str, Any],
    query: str,
    session_id: Optional[str],
    tool_name: str = "query_repository"
) -> Dict[str, Any]:
    """
    Enhance response with dynamic continuation prompts and session guidance.
    Breaks the one-loop pattern by encouraging deeper exploration.
    
    Args:
        response_dict: Original response dictionary
        query: The query that was processed
        session_id: Session ID for continuity tracking
        tool_name: Name of the tool that generated the response
        
    Returns:
        Enhanced response dictionary with flow guidance
    """
    if not session_id:
        session_id = generate_session_id()
        response_dict["session_id"] = session_id
    
    # Get response content for context analysis
    response_content = response_dict.get("message", "")
    
    # Track session activity
    domains = continuation_generator.identify_domain_focus(query, response_content)
    session_metadata = session_manager.track_session_query(session_id, query, domains, response_content)
    
    # Generate continuation prompts
    continuation_prompts = continuation_generator.generate_continuation_prompts(
        query=query,
        response_content=response_content,
        session_id=session_id,
        query_count=session_metadata.query_count
    )
    
    # Format and append flow guidance to the response message
    flow_guidance = continuation_generator.format_for_response(continuation_prompts)
    session_guidance = session_manager.format_persistence_guidance(session_id)
    
    # Enhance the response message
    enhanced_message = response_content + flow_guidance + "\n" + session_guidance
    response_dict["message"] = enhanced_message
    
    # Add flow enhancement metadata
    response_dict["flow_enhancement"] = {
        "session_metadata": {
            "session_id": session_id,
            "query_count": session_metadata.query_count,
            "domains_explored": session_metadata.exploration_domains,
            "depth_achieved": session_metadata.depth_achieved
        },
        "continuation_available": True,
        "compound_learning_active": session_metadata.query_count > 1,
        "exploration_momentum": continuation_prompts["depth_info"]["level_name"]
    }
    
    return response_dict

# Global client instance (will be initialized on first use)
_greptile_client: Optional[GreptileClient] = None

async def get_greptile_client() -> GreptileClient:
    """Get or create the Greptile client instance (lazy loading)."""
    global _greptile_client
    if _greptile_client is None:
        api_key = os.getenv("GREPTILE_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")

        if not api_key:
            logger.error("Missing GREPTILE_API_KEY environment variable")
            raise ValueError("GREPTILE_API_KEY environment variable is required for tool execution")
        if not github_token:
            logger.error("Missing GITHUB_TOKEN environment variable")
            raise ValueError("GITHUB_TOKEN environment variable is required for tool execution")

        logger.info("Initializing Greptile client (lazy loading)")
        _greptile_client = GreptileClient(api_key, github_token)
        logger.info("Greptile client initialized successfully")

    return _greptile_client

def validate_api_keys_available() -> bool:
    """Check if required API keys are available without raising errors."""
    return bool(os.getenv("GREPTILE_API_KEY") and os.getenv("GITHUB_TOKEN"))

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
                with APICallLogger("POST", "/repositories", remote=remote, repository=repository):
                    result = await client.index_repository(
                        remote=remote,
                        repository=repository,
                        branch=branch,
                        reload=reload,
                        notify=notify
                    )
        except RateLimitExceeded as e:
            logger.warning(
                "Rate limit exceeded for repository indexing",
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
    repositories: Optional[str] = None,  # JSON string, optional if session exists
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

    # Only validate repositories if provided (optional for session-based queries)
    repositories_list = []
    if repositories is not None:
        repositories_result, repositories_list = InputValidator.validate_repositories_json(repositories)
        if not repositories_result.is_valid:
            logger.log_validation_error("repositories", "; ".join(repositories_result.errors), repositories=repositories)
            return create_error_response("; ".join(repositories_result.errors), "ValidationError", session_id=session_id)
    elif session_id is None:
        # If no repositories and no session, we can't proceed
        return create_error_response("Either repositories or session_id must be provided", "ValidationError")

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

    # Normalize and generate session ID if not provided
    session_id = normalize_session_id(session_id)
    if session_id is None:
        session_id = generate_session_id()
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
            "Starting repository query",
            session_id=session_id,
            query=query[:100] + "..." if len(query) > 100 else query,
            repositories_count=len(repositories_list),
            stream=stream,
            genius=genius
        )

        if stream:
            # Use enhanced streaming with real-time chunk processing
            message_parts = []
            citations = []
            actual_session_id = session_id
            streaming_metadata = {
                "text_chunks": 0,
                "citations_received": 0,
                "started_at": time.time(),
                "first_chunk_at": None,
                "session_id": session_id
            }
            
            with APICallLogger("POST", "/query", session_id=session_id, stream=True):
                async for chunk in client.stream_query_repositories(
                    messages=messages,
                    repositories=repositories_list,
                    session_id=session_id,
                    genius=genius,
                    timeout=timeout
                ):
                    chunk_type = chunk.get("type")
                    
                    if chunk_type == "text":
                        content = chunk.get("content", "")
                        if content:
                            message_parts.append(content)
                            streaming_metadata["text_chunks"] += 1
                            
                            # Record first chunk timing
                            if streaming_metadata["first_chunk_at"] is None:
                                streaming_metadata["first_chunk_at"] = chunk.get("timestamp", time.time())
                    
                    elif chunk_type == "citation":
                        citation = {
                            "file": chunk.get("file"),
                            "lines": chunk.get("lines"),
                            "timestamp": chunk.get("timestamp")
                        }
                        citations.append(citation)
                        streaming_metadata["citations_received"] += 1
                    
                    elif chunk_type == "session":
                        actual_session_id = chunk.get("sessionId", session_id)
                        streaming_metadata["session_id"] = actual_session_id

            # Build comprehensive streaming response
            streaming_metadata["completed_at"] = time.time()
            streaming_metadata["duration"] = streaming_metadata["completed_at"] - streaming_metadata["started_at"]
            
            if streaming_metadata["first_chunk_at"]:
                streaming_metadata["time_to_first_chunk"] = streaming_metadata["first_chunk_at"] - streaming_metadata["started_at"]
            
            result = {
                "message": "".join(message_parts),
                "session_id": actual_session_id,
                "sources": citations,
                "streamed": True,
                "streaming_metadata": streaming_metadata
            }

            logger.info(
                "Streaming query completed",
                session_id=actual_session_id,
                text_chunks=streaming_metadata["text_chunks"],
                citations=streaming_metadata["citations_received"],
                duration=streaming_metadata["duration"],
                time_to_first_chunk=streaming_metadata.get("time_to_first_chunk")
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
                "Query completed",
                session_id=session_id,
                has_sources=bool(result.get("sources")),
                sources_count=len(result.get("sources", []))
            )

        # Enhance response with flow guidance to break the one-loop pattern
        enhanced_result = enhance_response_with_flow_guidance(result, query, session_id, "query_repository")
        return json.dumps(enhanced_result)

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
    repositories: Optional[str] = None,  # JSON string, optional if session exists
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
    # Validate inputs
    query_result = InputValidator.validate_query(query)
    if not query_result.is_valid:
        return create_error_response("; ".join(query_result.errors), "ValidationError", session_id=session_id)

    # Only validate repositories if provided (optional for session-based queries)
    repositories_list = []
    if repositories is not None:
        repositories_result, repositories_list = InputValidator.validate_repositories_json(repositories)
        if not repositories_result.is_valid:
            return create_error_response("; ".join(repositories_result.errors), "ValidationError", session_id=session_id)
    elif session_id is None:
        # If no repositories and no session, we can't proceed
        return create_error_response("Either repositories or session_id must be provided", "ValidationError")

    session_result = InputValidator.validate_session_id(session_id)
    if not session_result.is_valid:
        return create_error_response("; ".join(session_result.errors), "ValidationError", session_id=session_id)

    timeout_result = InputValidator.validate_timeout(timeout)
    if not timeout_result.is_valid:
        return create_error_response("; ".join(timeout_result.errors), "ValidationError", session_id=session_id)

    messages_result, previous_messages_list = InputValidator.validate_messages_json(previous_messages)
    if not messages_result.is_valid:
        return create_error_response("; ".join(messages_result.errors), "ValidationError", session_id=session_id)

    # Normalize and generate session ID if not provided
    session_id = normalize_session_id(session_id)
    if session_id is None:
        session_id = generate_session_id()

    try:
        client = await get_greptile_client()

        # Convert query to messages format
        messages = [{"role": "user", "content": query}]
        if previous_messages_list:
            messages = previous_messages_list + messages

        logger.info(
            "Starting repository search",
            session_id=session_id,
            query=query[:100] + "..." if len(query) > 100 else query,
            repositories_count=len(repositories_list),
            genius=genius
        )

        with APICallLogger("POST", "/search", session_id=session_id, stream=False):
            result = await client.search_repositories(
                messages=messages,
                repositories=repositories_list,
                session_id=session_id,
                genius=genius,
                timeout=timeout
            )
            result["session_id"] = session_id
            result["search_metadata"] = {
                "query_length": len(query),
                "repositories_searched": len(repositories_list),
                "genius_mode": genius,
                "timestamp": time.time()
            }

        logger.info(
            "Repository search completed",
            session_id=session_id,
            sources_found=len(result.get("sources", [])),
            genius=genius
        )

        # Enhance response with flow guidance to encourage deeper exploration
        enhanced_result = enhance_response_with_flow_guidance(result, query, session_id, "search_repository")
        return json.dumps(enhanced_result)

    except Exception as e:
        logger.log_exception(
            e,
            context="search_repository",
            session_id=session_id,
            query=query[:100] + "..." if len(query) > 100 else query
        )
        return create_error_response(str(e), type(e).__name__, session_id=session_id)

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

# ============================================================================
# Orchestration Tools - Multi-Agent Coordination
# ============================================================================

@mcp.tool
@log_execution_time("analyze_codebase_feature")
async def analyze_codebase_feature_tool(
    feature: str,
    repositories: Optional[str] = None,
    session_id: Optional[str] = None,
    analysis_depth: str = "comprehensive",
    include_implementation: bool = True,
    include_examples: bool = False
) -> str:
    """
    Autonomous codebase feature analysis using multi-stage orchestration.
    
    Implements Claude Code sub-agent pattern for comprehensive analysis:
    - Lead agent decomposes the analysis task
    - Spawns specialized sub-agents for discovery, analysis, implementation
    - Coordinates execution using session continuity
    - Synthesizes results into unified response
    
    Args:
        feature: Feature or pattern to analyze (e.g., "authentication", "state management")
        repositories: JSON string of repositories (optional if session exists)
        session_id: Optional session ID for context continuity
        analysis_depth: "basic", "comprehensive", or "expert"
        include_implementation: Include implementation guidance
        include_examples: Include code examples in response
    
    Returns:
        JSON string with comprehensive multi-stage analysis
    """
    try:
        client = await get_greptile_client()
        return await analyze_codebase_feature(
            client=client,
            feature=feature,
            repositories=repositories,
            session_id=session_id,
            analysis_depth=analysis_depth,
            include_implementation=include_implementation,
            include_examples=include_examples
        )
    except Exception as e:
        logger.error(f"Orchestration tool error: {str(e)}", session_id=session_id)
        return json.dumps({
            "error": f"Codebase feature analysis failed: {str(e)}",
            "type": type(e).__name__,
            "session_id": session_id
        })

@mcp.tool
@log_execution_time("compare_codebase_patterns")
async def compare_codebase_patterns_tool(
    pattern_focus: str,
    repositories: str,  # Required for multi-repo comparison
    session_id: Optional[str] = None,
    comparison_depth: str = "architectural"
) -> str:
    """
    Cross-repository pattern comparison using orchestrated analysis.
    
    Implements multi-repository orchestration pattern:
    - Lead agent coordinates overall comparison
    - Spawns analysis sub-agents for each repository
    - Spawns synthesis agent for cross-repository insights
    - Integrates results into comparative analysis
    
    Args:
        pattern_focus: Pattern or aspect to compare (e.g., "error handling", "testing patterns")
        repositories: JSON string of repositories to compare (minimum 2)
        session_id: Optional session ID for context continuity
        comparison_depth: "basic", "architectural", or "implementation"
    
    Returns:
        JSON string with cross-repository comparative analysis
    """
    try:
        client = await get_greptile_client()
        return await compare_codebase_patterns(
            client=client,
            pattern_focus=pattern_focus,
            repositories=repositories,
            session_id=session_id,
            comparison_depth=comparison_depth
        )
    except Exception as e:
        logger.error(f"Pattern comparison error: {str(e)}", session_id=session_id)
        return json.dumps({
            "error": f"Pattern comparison failed: {str(e)}",
            "type": type(e).__name__,
            "session_id": session_id
        })

@mcp.tool
@log_execution_time("explore_codebase_autonomous")
async def explore_codebase_autonomous_tool(
    starting_point: str,
    repositories: Optional[str] = None,
    exploration_depth: int = 3,
    session_id: Optional[str] = None
) -> str:
    """
    Autonomous codebase exploration using recursive sub-agent pattern.
    
    Implements recursive exploration pattern:
    - Lead agent analyzes starting point and spawns exploration sub-agents
    - Each sub-agent recursively explores discovered concepts/patterns
    - Depth-limited recursion prevents infinite exploration
    - Builds comprehensive exploration tree and synthesis
    
    Args:
        starting_point: Initial concept/pattern to explore (e.g., "component architecture")
        repositories: JSON string of repositories (optional if session exists)
        exploration_depth: Maximum recursion depth (1-5)
        session_id: Optional session ID for context continuity
    
    Returns:
        JSON string with autonomous exploration results and tree
    """
    try:
        client = await get_greptile_client()
        return await explore_codebase_autonomous(
            client=client,
            starting_point=starting_point,
            repositories=repositories,
            exploration_depth=exploration_depth,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Autonomous exploration error: {str(e)}", session_id=session_id)
        return json.dumps({
            "error": f"Autonomous exploration failed: {str(e)}",
            "type": type(e).__name__,
            "session_id": session_id
        })

# ============================================================================
# MCP Resources - Live Documentation and Patterns
# ============================================================================

@mcp.resource("greptile://docs/workflows")
async def greptile_workflows_resource() -> str:
    """Live documentation of Greptile workflow patterns and best practices."""
    return json.dumps({
        "type": "workflows",
        "content": {
            "basic_workflow": {
                "name": "Repository Discovery",
                "steps": [
                    "Index repository with index_repository()",
                    "Check status with get_repository_info()",
                    "Query architecture with query_repository()",
                    "Search specific patterns with search_repository()"
                ],
                "memory_trigger": "Notice how indexing creates the foundation for all subsequent understanding"
            },
            "expert_consultation": {
                "name": "Architectural Consultation",
                "phases": [
                    "Discovery - What patterns exist?",
                    "Analysis - How do they connect?", 
                    "Synthesis - What do they reveal?",
                    "Implementation - How to enhance?"
                ],
                "memory_trigger": "Each query builds on previous understanding like layered insight"
            },
            "context_building": {
                "name": "Session Context Development",
                "pattern": "session_id creates conversation threads that accumulate understanding",
                "memory_trigger": "Context isn't just data - it's the story of your exploration"
            }
        }
    })

@mcp.resource("greptile://patterns/architectural")
async def greptile_architectural_patterns_resource() -> str:
    """Architectural patterns and consultation approaches."""
    return json.dumps({
        "type": "architectural_patterns",
        "content": {
            "blueprint_first": {
                "description": "Understand the intended architecture before diving into implementation",
                "seed_question": "What did the original architects assume you'd know?",
                "approach": "Query for design decisions, not just code structure"
            },
            "evolutionary_architecture": {
                "description": "How codebases adapt and grow over time",
                "seed_question": "What stories does this codebase tell about its evolution?",
                "approach": "Look for patterns of change, not just current state"
            },
            "distributed_intelligence": {
                "description": "Using Greptile as an expert system, not just search",
                "seed_question": "What would an expert notice that I'm missing?",
                "approach": "Ask for analysis and insights, not just information"
            },
            "context_accumulation": {
                "description": "Building understanding through connected queries",
                "seed_question": "How does this new information connect to what I already learned?",
                "approach": "Use session_id to create knowledge threads"
            }
        }
    })

@mcp.resource("greptile://context-seeds/discovery")
async def greptile_context_seeds_resource() -> str:
    """Context seeds for organic discovery and learning."""
    return json.dumps({
        "type": "context_seeds",
        "content": {
            "memory_triggers": [
                "When you index a repository, notice how it transforms from static files to living knowledge",
                "Session IDs aren't just technical - they're the DNA of your exploration journey",
                "Genius mode isn't just slower - it's deeper, like the difference between skimming and studying",
                "Streaming responses reveal the thinking process, not just the final answer"
            ],
            "pattern_seeds": [
                "Architecture emerges through questions, not just answers",
                "Code patterns reflect human decision-making patterns", 
                "The best insights come from asking what the code assumes you understand",
                "Context builds like layers: syntax → semantics → intent → wisdom"
            ],
            "discovery_questions": [
                "What questions reveal this codebase's story?",
                "How does this code want to be understood?",
                "What would surprise the original authors about how their code is used?",
                "What patterns exist that aren't explicitly documented?"
            ],
            "reflection_hooks": [
                "How did your understanding change through this exploration?",
                "What connections did you make that surprised you?",
                "What would you tell past-you about this codebase?",
                "Which questions led to the most insight?"
            ]
        }
    })

@mcp.resource("greptile://session/{session_id}/context")
async def greptile_session_context_resource(session_id: str) -> str:
    """Session-specific context and conversation history patterns."""
    return json.dumps({
        "type": "session_context",
        "session_id": session_id,
        "content": {
            "context_building": {
                "description": "How context accumulates through conversation",
                "pattern": "Each query in a session builds on previous understanding",
                "memory_trigger": f"Session {session_id} is your exploration narrative"
            },
            "conversation_flow": {
                "stages": [
                    "Initial curiosity - What is this?",
                    "Pattern recognition - How does this work?",
                    "Deep understanding - Why was this chosen?",
                    "Expert insight - What can be improved?"
                ],
                "memory_trigger": "Conversations have rhythms - notice yours"
            },
            "thread_continuity": {
                "description": "Maintaining context across multiple queries",
                "approach": "Use previous_messages to build on prior insights",
                "memory_trigger": "Context isn't just remembered - it's actively built"
            }
        }
    })

@mcp.resource("greptile://examples/progressive-learning")
async def greptile_progressive_learning_resource() -> str:
    """Examples of progressive learning patterns with Greptile."""
    return json.dumps({
        "type": "progressive_learning",
        "content": {
            "beginner_flow": {
                "focus": "Understanding the basics",
                "questions": [
                    "What is the main purpose of this repository?",
                    "What are the key files and their roles?",
                    "How is the project structured?"
                ],
                "memory_trigger": "Start with the forest, then examine the trees"
            },
            "intermediate_flow": {
                "focus": "Connecting patterns",
                "questions": [
                    "How do these components interact?",
                    "What patterns repeat across the codebase?",
                    "What design decisions shaped this architecture?"
                ],
                "memory_trigger": "Patterns reveal the thinking behind the code"
            },
            "advanced_flow": {
                "focus": "Expert consultation",
                "questions": [
                    "What would an expert refactor first?",
                    "How could this architecture evolve?",
                    "What hidden complexities exist?"
                ],
                "memory_trigger": "Expert thinking is about seeing what others miss"
            }
        }
    })

# ============================================================================
# MCP Prompts - Context Seeds for Organic Discovery
# ============================================================================

@mcp.prompt("discover_architecture")
async def discover_architecture_prompt(repository: str = "current", focus: str = "general") -> list[dict]:
    """Context seed prompt for organic architectural discovery."""
    return [
        {
            "role": "system",
            "content": f"""You are exploring {repository} as distributed intelligence, not just searching it.

Context Seeds:
- Architecture emerges through questions, not just answers
- The best insights come from asking what the code assumes you understand
- Code patterns reflect human decision-making patterns

Your approach should be exploratory, building understanding through connected insights."""
        },
        {
            "role": "user",
            "content": f"""What architectural patterns want to emerge from this codebase?

Focus area: {focus}

Rather than just describing structure, help me understand:
- What did the original architects assume I'd know?
- What stories does this codebase tell about its evolution?
- What would surprise the original authors about how their code is used?

Remember: Context builds like layers: syntax → semantics → intent → wisdom"""
        }
    ]

@mcp.prompt("explore_codebase")
async def explore_codebase_prompt(repository: str = "current", exploration_type: str = "patterns") -> list[dict]:
    """Context seed prompt for organic codebase exploration."""
    return [
        {
            "role": "system", 
            "content": f"""You are conducting a discovery session with {repository}.

Memory Triggers:
- When you index a repository, notice how it transforms from static files to living knowledge
- Session IDs aren't just technical - they're the DNA of your exploration journey
- The best insights come from asking what the code assumes you understand

Pattern Seeds:
- Code patterns reflect human decision-making patterns
- Architecture emerges through questions, not just answers
- Context builds like layers: syntax → semantics → intent → wisdom"""
        },
        {
            "role": "user",
            "content": f"""How does this code want to be understood?

Exploration type: {exploration_type}

Guide me through discovering:
- What questions reveal this codebase's story?
- How do these components want to connect?
- What patterns exist that aren't explicitly documented?

Discovery Questions to Consider:
- What would an expert notice that I'm missing?
- How does this new information connect to what I already learned?
- What patterns repeat across the codebase?"""
        }
    ]

@mcp.prompt("expert_consultation")
async def expert_consultation_prompt(
    repository: str = "current", 
    consultation_phase: str = "discovery",
    context: str = "general"
) -> list[dict]:
    """Context seed prompt for expert consultation workflow."""
    
    phases = {
        "discovery": "What patterns exist? Map the codebase landscape.",
        "analysis": "How do they connect? Understand relationships and dependencies.",
        "synthesis": "What do they reveal? Extract insights and implications.",
        "implementation": "How to enhance? Generate actionable improvements."
    }
    
    return [
        {
            "role": "system",
            "content": f"""You are an expert consultant analyzing {repository}.

Current Phase: {consultation_phase.title()} - {phases.get(consultation_phase, "General exploration")}

Expert Consultation Approach:
- Treat Greptile as distributed intelligence, not just search
- Ask for analysis and insights, not just information
- Build understanding through connected queries
- Use session_id to create knowledge threads

Context: {context}

Memory Trigger: Each query builds on previous understanding like layered insight"""
        },
        {
            "role": "user",
            "content": f"""Conduct expert-level {consultation_phase} of this codebase.

What would an expert notice that others miss?

Phase-Specific Focus:
{phases.get(consultation_phase, "Explore the codebase with expert insight")}

Remember:
- Context isn't just data - it's the story of your exploration
- Expert thinking is about seeing what others miss
- Conversations have rhythms - notice yours"""
        }
    ]

@mcp.prompt("pattern_recognition")
async def pattern_recognition_prompt(
    repository: str = "current",
    pattern_type: str = "architectural",
    depth: str = "intermediate"
) -> list[dict]:
    """Context seed prompt for pattern recognition and learning."""
    
    depth_approaches = {
        "beginner": "Start with the forest, then examine the trees",
        "intermediate": "Patterns reveal the thinking behind the code", 
        "advanced": "Expert thinking is about seeing what others miss"
    }
    
    return [
        {
            "role": "system",
            "content": f"""You are recognizing {pattern_type} patterns in {repository}.

Learning Depth: {depth.title()}
Approach: {depth_approaches.get(depth, "Explore patterns organically")}

Pattern Recognition Seeds:
- Architecture emerges through questions, not just answers
- Code patterns reflect human decision-making patterns
- The best insights come from asking what the code assumes you understand
- Context builds like layers: syntax → semantics → intent → wisdom

Memory Trigger: Patterns reveal the thinking behind the code"""
        },
        {
            "role": "user",
            "content": f"""Help me recognize {pattern_type} patterns in this codebase.

Pattern Type: {pattern_type}
Learning Level: {depth}

Guide me to discover:
- What patterns repeat across the codebase?
- What design decisions shaped this architecture?
- How do these patterns connect to larger architectural principles?

Reflection Questions:
- How did your understanding change through this exploration?
- What connections did you make that surprised you?
- Which questions led to the most insight?"""
        }
    ]

@mcp.prompt("context_integration")
async def context_integration_prompt(
    session_id: str,
    previous_insights: str = "none",
    integration_focus: str = "connections"
) -> list[dict]:
    """Context seed prompt for integrating session context and building understanding."""
    return [
        {
            "role": "system",
            "content": f"""You are integrating context from session {session_id}.

Integration Focus: {integration_focus}

Context Integration Principles:
- Context isn't just remembered - it's actively built
- Session IDs are the DNA of your exploration journey
- Each query in a session builds on previous understanding
- Context builds like layers: syntax → semantics → intent → wisdom

Memory Trigger: Context isn't just data - it's the story of your exploration"""
        },
        {
            "role": "user",
            "content": f"""Help me integrate my current understanding with previous insights.

Session: {session_id}
Previous Insights: {previous_insights}
Focus: {integration_focus}

Integration Questions:
- How does this new information connect to what I already learned?
- What patterns are emerging across our conversation?
- What would you tell past-you about this codebase?

Reflection Hooks:
- How did your understanding change through this exploration?
- What connections did you make that surprised you?
- Which questions led to the most insight?

Thread Continuity: Use previous_messages to build on prior insights"""
        }
    ]

# ============================================================================
# Greptile Help Tool - Context Seeds Approach
# ============================================================================

@mcp.tool
async def greptile_help(
    learning_level: str = "beginner",
    context_type: str = "discovery",
    focus_area: str = "general"
) -> str:
    """
    Context seeds and memory triggers for organic Greptile MCP exploration.
    
    This is not a manual - it's a collection of seeds that grow into understanding through use.
    
    Args:
        learning_level: beginner, intermediate, advanced (default: beginner)
        context_type: discovery, patterns, workflows, integration (default: discovery)
        focus_area: general, architectural, consultation, session_management (default: general)
    
    Returns:
        JSON with context seeds, memory triggers, and discovery prompts
    """
    
    # Base context seeds that adapt to learning level
    base_seeds = {
        "memory_triggers": {
            "beginner": [
                "When you index a repository, notice how it transforms from static files to living knowledge",
                "Session IDs aren't just technical - they're the DNA of your exploration journey",
                "Start with the forest, then examine the trees"
            ],
            "intermediate": [
                "Genius mode isn't just slower - it's deeper, like the difference between skimming and studying",
                "Context builds like layers: syntax → semantics → intent → wisdom",
                "Patterns reveal the thinking behind the code"
            ],
            "advanced": [
                "Expert thinking is about seeing what others miss",
                "Treat Greptile as distributed intelligence, not just search",
                "Each query builds on previous understanding like layered insight",
                "Orchestration tools spawn specialized sub-agents for comprehensive analysis",
                "Multi-stage pipelines create compound intelligence from coordinated queries"
            ]
        },
        "pattern_seeds": {
            "discovery": [
                "Architecture emerges through questions, not just answers",
                "The best insights come from asking what the code assumes you understand",
                "Code patterns reflect human decision-making patterns"
            ],
            "patterns": [
                "What patterns repeat across the codebase?",
                "What design decisions shaped this architecture?",
                "How do these patterns connect to larger architectural principles?"
            ],
            "workflows": [
                "Context isn't just data - it's the story of your exploration",
                "Conversations have rhythms - notice yours",
                "Context isn't just remembered - it's actively built"
            ],
            "integration": [
                "How does this new information connect to what I already learned?",
                "What patterns are emerging across our conversation?",
                "Thread continuity: Use previous_messages to build on prior insights"
            ]
        },
        "discovery_questions": {
            "general": [
                "What questions reveal this codebase's story?",
                "How does this code want to be understood?",
                "What would an expert notice that I'm missing?"
            ],
            "architectural": [
                "What did the original architects assume I'd know?",
                "What stories does this codebase tell about its evolution?",
                "What would surprise the original authors about how their code is used?"
            ],
            "consultation": [
                "What would an expert refactor first?",
                "How could this architecture evolve?",
                "What hidden complexities exist?"
            ],
            "session_management": [
                "How does my understanding change through this exploration?",
                "What connections did I make that surprised me?",
                "Which questions led to the most insight?"
            ]
        }
    }
    
    # Available resources and prompts
    available_resources = [
        "greptile://docs/workflows - Live workflow documentation",
        "greptile://patterns/architectural - Architectural patterns and approaches",
        "greptile://context-seeds/discovery - Context seeds for organic learning",
        "greptile://session/{session_id}/context - Session-specific context patterns",
        "greptile://examples/progressive-learning - Progressive learning examples"
    ]
    
    available_prompts = [
        "discover_architecture - Organic architectural discovery",
        "explore_codebase - Codebase exploration and pattern recognition",
        "expert_consultation - Expert consultation workflow",
        "pattern_recognition - Pattern recognition and learning",
        "context_integration - Session context integration",
        "multi_repo_discovery - Multi-repository discovery and exploration"
    ]
    
    # Core tools reminder
    core_tools = {
        "index_repository": "Index a repository (required first step)",
        "query_repository": "Natural language queries with code context",
        "search_repository": "Find relevant files without full answers",
        "get_repository_info": "Get repository status and metadata"
    }
    
    orchestration_tools = {
        "analyze_codebase_feature_tool": "Autonomous multi-stage feature analysis",
        "compare_codebase_patterns_tool": "Cross-repository pattern comparison",
        "explore_codebase_autonomous_tool": "Recursive autonomous codebase exploration"
    }
    
    # Growth paths based on learning level
    growth_paths = {
        "beginner": {
            "next_steps": [
                "Try indexing a repository first",
                "Use query_repository to ask about the codebase",
                "Explore the greptile://docs/workflows resource"
            ],
            "focus": "Understanding the basics and building confidence"
        },
        "intermediate": {
            "next_steps": [
                "Use session_id to maintain conversation context",
                "Try analyze_codebase_feature_tool for comprehensive analysis",
                "Explore the architectural patterns resource"
            ],
            "focus": "Connecting patterns and using orchestration tools"
        },
        "advanced": {
            "next_steps": [
                "Use compare_codebase_patterns_tool for cross-repository analysis",
                "Try explore_codebase_autonomous_tool for recursive exploration",
                "Master multi-stage orchestration workflows"
            ],
            "focus": "Expert-level orchestration and multi-agent coordination"
        }
    }
    
    # Reflection hooks for organic learning
    reflection_hooks = [
        "How did your understanding change through this exploration?",
        "What connections did you make that surprised you?",
        "What would you tell past-you about this codebase?",
        "Which questions led to the most insight?"
    ]
    
    # Build the response
    response = {
        "type": "context_seeds",
        "learning_level": learning_level,
        "context_type": context_type,
        "focus_area": focus_area,
        "seeds": {
            "memory_triggers": base_seeds["memory_triggers"].get(learning_level, base_seeds["memory_triggers"]["beginner"]),
            "pattern_seeds": base_seeds["pattern_seeds"].get(context_type, base_seeds["pattern_seeds"]["discovery"]),
            "discovery_questions": base_seeds["discovery_questions"].get(focus_area, base_seeds["discovery_questions"]["general"])
        },
        "growth_path": growth_paths.get(learning_level, growth_paths["beginner"]),
        "reflection_hooks": reflection_hooks,
        "available_resources": available_resources,
        "available_prompts": available_prompts,
        "core_tools": core_tools,
        "orchestration_tools": orchestration_tools,
        "philosophy": {
            "approach": "Seeds that grow through use, not rigid instructions",
            "principle": "Context builds like layers: syntax → semantics → intent → wisdom",
            "mindset": "Treat Greptile as distributed intelligence, not just search"
        },
        "quick_start": {
            "basic": {
                "step_1": "Index a repository: index_repository(remote='github', repository='owner/repo', branch='main')",
                "step_2": "Check status: get_repository_info(remote='github', repository='owner/repo', branch='main')",
                "step_3": "Query: query_repository('What is the architecture?', repositories='[{...}]')",
                "step_4": "Build context: Use session_id for conversation continuity"
            },
            "orchestration": {
                "step_1": "Comprehensive analysis: analyze_codebase_feature_tool(feature='authentication', repositories='[{...}]')",
                "step_2": "Cross-repository comparison: compare_codebase_patterns_tool(pattern_focus='error handling', repositories='[{repo1}, {repo2}]')",
                "step_3": "Autonomous exploration: explore_codebase_autonomous_tool(starting_point='component system', exploration_depth=3)",
                "step_4": "Use session_id across all orchestration tools for compound intelligence"
            }
        }
    }
    
    return json.dumps(response, indent=2)

# ============================================================================
# Enhanced Session Context Resources and Pattern Libraries
# ============================================================================

@mcp.resource("greptile://agents/coordination-patterns")
async def greptile_agent_coordination_resource() -> str:
    """Personal capability multiplication patterns for indie developer agent coordination."""
    return json.dumps({
        "type": "agent_coordination_patterns",
        "content": {
            "learning_amplification": {
                "name": "Learning Amplification Pattern",
                "purpose": "Multiply personal learning velocity through codebase exploration",
                "agent_roles": {
                    "exploration_agent": "Navigate and map codebase structure",
                    "pattern_agent": "Extract and catalog reusable patterns", 
                    "synthesis_agent": "Connect insights across different codebases",
                    "learning_agent": "Track personal knowledge growth and gaps"
                },
                "coordination_flow": [
                    "Exploration agent maps unfamiliar territory",
                    "Pattern agent identifies teachable moments",
                    "Synthesis agent connects to previous knowledge",
                    "Learning agent updates personal knowledge graph"
                ],
                "personal_value": "Transform weeks of reverse engineering into hours of guided learning"
            },
            "capability_multiplication": {
                "name": "Capability Multiplication Pattern",
                "purpose": "Enhance coding agent capabilities through codebase context",
                "agent_roles": {
                    "context_agent": "Maintain full project understanding",
                    "generation_agent": "Create code using learned patterns",
                    "validation_agent": "Ensure consistency with project architecture",
                    "optimization_agent": "Apply performance patterns from similar projects"
                },
                "coordination_flow": [
                    "Context agent provides architectural awareness",
                    "Generation agent creates contextually appropriate code",
                    "Validation agent checks against project patterns",
                    "Optimization agent applies proven techniques"
                ],
                "personal_value": "Generate code that fits seamlessly into existing architecture"
            },
            "cross_project_intelligence": {
                "name": "Cross-Project Intelligence Pattern", 
                "purpose": "Build compound intelligence across multiple codebase explorations",
                "agent_roles": {
                    "comparison_agent": "Find similarities across different projects",
                    "abstraction_agent": "Extract generalizable patterns",
                    "application_agent": "Apply learned patterns to new contexts",
                    "evolution_agent": "Track pattern effectiveness over time"
                },
                "coordination_flow": [
                    "Comparison agent identifies recurring solutions",
                    "Abstraction agent generalizes to reusable principles",
                    "Application agent suggests relevant patterns for current work",
                    "Evolution agent refines patterns based on outcomes"
                ],
                "personal_value": "Each project you explore makes all future projects easier"
            }
        },
        "coordination_principles": {
            "session_continuity": "Maintain context across multi-turn explorations",
            "compound_learning": "Each interaction builds on previous understanding",
            "personal_adaptation": "Agents adapt to your learning style and preferences",
            "capability_growth": "Focus on multiplying individual capabilities, not team coordination"
        },
        "indie_philosophy": {
            "empowerment_over_efficiency": "Optimize for learning and capability growth, not just speed",
            "deep_understanding": "Prioritize comprehension over completion",
            "pattern_library_building": "Accumulate reusable knowledge for future projects",
            "personal_ai_evolution": "Your agents get smarter as you explore more codebases"
        }
    }, indent=2)

@mcp.resource("greptile://patterns/consultation-phases")
async def greptile_consultation_phases_resource() -> str:
    """Detailed consultation phases for expert architectural analysis."""
    return json.dumps({
        "type": "consultation_phases",
        "content": {
            "phase_1_discovery": {
                "name": "Discovery - What patterns exist?",
                "objectives": ["Map codebase landscape", "Identify architectural patterns", "Locate anti-patterns"],
                "key_questions": [
                    "What is the intended architecture?",
                    "How is the code actually structured?",
                    "What patterns repeat across modules?"
                ],
                "memory_trigger": "Discovery is about seeing the forest AND the trees",
                "next_phase": "analysis"
            },
            "phase_2_analysis": {
                "name": "Analysis - How do they connect?",
                "objectives": ["Understand relationships", "Map dependencies", "Identify bottlenecks"],
                "key_questions": [
                    "How do components interact?",
                    "Where are the coupling points?",
                    "What are the data flows?"
                ],
                "memory_trigger": "Analysis reveals the hidden connections",
                "next_phase": "synthesis"
            },
            "phase_3_synthesis": {
                "name": "Synthesis - What do they reveal?",
                "objectives": ["Extract insights", "Identify improvements", "Assess risks"],
                "key_questions": [
                    "What do these patterns tell us?",
                    "What are the design implications?",
                    "Where are the architectural debt points?"
                ],
                "memory_trigger": "Synthesis transforms patterns into wisdom",
                "next_phase": "implementation"
            },
            "phase_4_implementation": {
                "name": "Implementation - How to enhance?",
                "objectives": ["Generate solutions", "Create migration paths", "Provide specifications"],
                "key_questions": [
                    "What should be refactored first?",
                    "How can we improve the architecture?",
                    "What are the implementation steps?"
                ],
                "memory_trigger": "Implementation makes insights actionable",
                "next_phase": "validation"
            }
        }
    })

@mcp.resource("greptile://session/{session_id}/learning-trajectory")
async def greptile_learning_trajectory_resource(session_id: str) -> str:
    """Learning trajectory and insight evolution for a specific session."""
    return json.dumps({
        "type": "learning_trajectory",
        "session_id": session_id,
        "content": {
            "trajectory_tracking": {
                "description": "How understanding evolves through conversation",
                "stages": [
                    "Initial questions - What am I looking at?",
                    "Pattern recognition - How does this work?",
                    "Context building - Why was this chosen?",
                    "Expert synthesis - What can be improved?"
                ],
                "memory_trigger": f"Session {session_id} is your learning journey in code"
            },
            "insight_evolution": {
                "description": "How insights build on each other",
                "pattern": "Each query should build on previous understanding",
                "approach": "Use previous_messages to reference earlier insights",
                "memory_trigger": "Context accumulates like sedimentary layers"
            },
            "conversation_patterns": {
                "effective_patterns": [
                    "Start broad, then focus",
                    "Connect new insights to previous ones",
                    "Ask follow-up questions based on discoveries",
                    "Integrate findings across queries"
                ],
                "memory_trigger": "Good conversations have rhythm and flow"
            }
        }
    })

@mcp.resource("greptile://tools/enhanced-usage")
async def greptile_enhanced_usage_resource() -> str:
    """Enhanced usage patterns and 2025 MCP features."""
    return json.dumps({
        "type": "enhanced_usage",
        "content": {
            "tool_output_schemas": {
                "description": "2025 MCP feature for predictable tool outputs",
                "benefit": "Improved context efficiency and parsing",
                "usage": "Tools now provide structured output schemas for better integration",
                "memory_trigger": "Structured outputs enable better context management"
            },
            "session_management": {
                "description": "Advanced session and context management",
                "patterns": [
                    "Maintain session_id across related queries",
                    "Use previous_messages to build context",
                    "Track learning trajectory through sessions"
                ],
                "memory_trigger": "Sessions are conversations, not just API calls"
            },
            "resource_integration": {
                "description": "How to combine tools, resources, and prompts",
                "workflow": [
                    "Access resources for context and patterns",
                    "Use prompts for structured exploration",
                    "Apply tools for specific operations",
                    "Integrate insights across all three"
                ],
                "memory_trigger": "Tools, resources, and prompts work together as a system"
            }
        }
    })

@mcp.prompt("multi_repo_discovery")
async def multi_repo_discovery_prompt(
    exploration_type: str = "comprehensive",
    session_context: str = "new_exploration"
) -> list[dict]:
    """Multi-repository discovery and exploration prompt."""
    return [
        {
            "role": "system",
            "content": f"""You are exploring multiple repositories as a unified knowledge space.

Exploration Type: {exploration_type}
Session Context: {session_context}

Multi-Repository Discovery Approach:
- Treat repositories as facets of a larger domain understanding
- Look for patterns that emerge across implementations
- Identify unique innovations worth cross-pollination
- Build unified insights that span all repositories

Pattern Seeds:
- Cross-repository insights reveal universal patterns and unique innovations
- Each query builds understanding that spans all included repositories
- Comparative analysis generates insights impossible from single repositories

Memory Trigger: Multi-repo exploration reveals both patterns and innovations"""
        },
        {
            "role": "user",
            "content": f"""Help me explore these repositories as a unified knowledge domain.

Exploration Focus: {exploration_type}

Discovery Questions:
- What story emerges when viewing these repositories together?
- How do different approaches complement each other?
- What patterns repeat across implementations?
- Which unique innovations deserve attention?

Cross-Repository Synthesis:
- What can each project learn from the others?
- How do domain constraints shape different approaches?
- What hybrid strategies could emerge from combining insights?

Integration Approach:
- Use session continuity to build compound understanding
- Connect insights across repositories in each query
- Accumulate cross-repository patterns and innovations"""
        }
    ]

# ============================================================================
# Tool Output Schemas (2025 MCP Feature)
# ============================================================================

# Note: Tool output schemas would be implemented as part of the MCP server configuration
# This is a placeholder for the 2025 feature that provides structured output definitions

@mcp.resource("greptile://schemas/tool-outputs")
async def greptile_tool_output_schemas_resource() -> str:
    """Tool output schemas for enhanced context efficiency."""
    return json.dumps({
        "type": "tool_output_schemas",
        "content": {
            "index_repository": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "statusEndpoint": {"type": "string"},
                        "repository": {"type": "string"},
                        "branch": {"type": "string"},
                        "status": {"type": "string"}
                    }
                },
                "description": "Structured indexing response for better parsing"
            },
            "query_repository": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "sources": {"type": "array"},
                        "session_id": {"type": "string"},
                        "streamed": {"type": "boolean"}
                    }
                },
                "description": "Structured query response with source references"
            },
            "greptile_help": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "learning_level": {"type": "string"},
                        "context_type": {"type": "string"},
                        "seeds": {"type": "object"},
                        "growth_path": {"type": "object"},
                        "philosophy": {"type": "object"}
                    }
                },
                "description": "Structured help response with context seeds"
            }
        }
    })

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
    
    # Check transport method from environment
    transport = os.getenv("TRANSPORT", "stdio").lower()
    
    if transport == "sse":
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8080))
        logger.info(f"Starting MCP server with SSE transport on {host}:{port}")
        mcp.run(transport="sse", host=host, port=port)
    else:
        logger.info("Starting MCP server with stdio transport")
        mcp.run(transport="stdio")
