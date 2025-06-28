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
    session_manager: Optional[SessionManager] = None  # Add session manager for conversation context

@asynccontextmanager
async def greptile_lifespan(server: FastMCP) -> AsyncIterator[GreptileContext]:
    """
    Manages the session/conv context (no Greptile client, so tool listing does not require config).

    Args:
        server: The FastMCP server instance

    Yields:
        GreptileContext: The context containing the session manager
    """
    session_manager = SessionManager()
    context = GreptileContext(session_manager=session_manager)
    yield context

# Initialize FastMCP server with the session manager as context
mcp = FastMCP(
    "mcp-greptile",
    description="MCP server for code search and querying with Greptile API",
    lifespan=greptile_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=os.getenv("PORT", "8050")
)        

@mcp.tool()
async def index_repository(ctx: Context, remote: str, repository: str, branch: str, reload: bool = True, notify: bool = False) -> str:
    """Index a repository for code search and querying.

    OVERVIEW:
    This tool processes and indexes a Git repository to make it available for intelligent code search 
    and semantic querying. The repository must be indexed before any queries can be performed against it.
    Indexing creates a searchable knowledge base of the codebase that enables natural language queries
    about code structure, implementation patterns, and specific functionality.

    WORKFLOW INTEGRATION:
    1. **First Step**: Always index repositories before querying
    2. **Session Management**: Index once per session, then query multiple times
    3. **Updates**: Re-index when code changes significantly or when reload=True is needed
    4. **Performance**: Initial indexing takes 30 seconds to several minutes depending on repository size

    QUICK START EXAMPLES:
    
    # Index a popular repository
    index_repository("github", "microsoft/vscode", "main")
    
    # Index with custom branch
    index_repository("github", "facebook/react", "18.2.0")
    
    # Index without reloading (use existing cache if available)
    index_repository("github", "openai/gpt-4", "main", reload=False)
    
    # Index with email notification when complete
    index_repository("gitlab", "gitlab-org/gitlab", "master", notify=True)

    PARAMETERS EXPLAINED:
    
    - remote: Repository hosting platform
      * "github" - GitHub repositories (most common)
      * "gitlab" - GitLab repositories
      
    - repository: Full repository path in "owner/name" format
      * Examples: "torvalds/linux", "nodejs/node", "python/cpython"
      * Case-sensitive, must match exact repository name
      
    - branch: Specific branch or tag to index
      * Common: "main", "master", "develop"
      * Version tags: "v1.0.0", "release-2.1"
      * Feature branches: "feature/new-api"
      
    - reload: Controls caching behavior (default: True)
      * True: Force fresh indexing, ignore existing cache
      * False: Use existing index if available, faster for repeated access
      * Use True for: updated code, first-time indexing, troubleshooting
      * Use False for: repeated queries in same session, performance optimization
      
    - notify: Email notification when indexing completes (default: False)
      * True: Send completion email (requires configured email settings)
      * False: No notification, check status manually

    PERFORMANCE EXPECTATIONS:
    
    - Small repos (<1MB): 30-60 seconds
    - Medium repos (1-10MB): 1-3 minutes  
    - Large repos (10-100MB): 3-10 minutes
    - Very large repos (>100MB): 10+ minutes
    
    The tool returns immediately with status, actual processing happens asynchronously.
    Use reload=False for subsequent queries in the same session for faster access.

    COMMON ERROR SCENARIOS:
    
    1. **Repository Not Found**: Verify exact repository name and access permissions
       - Check spelling: "microsoft/vscode" not "Microsoft/VSCode"
       - Ensure repository is public or you have access
       
    2. **Branch Not Found**: Verify branch exists
       - Use "main" instead of "master" for newer repositories
       - Check actual branch names on the repository website
       
    3. **Rate Limiting**: Too many requests
       - Wait before retrying
       - Use reload=False for repeated access
       
    4. **Authentication Issues**: API key problems
       - Verify GREPTILE_API_KEY environment variable is set
       - Check API key permissions and validity
       
    5. **Large Repository Timeouts**: Repository too large
       - Try indexing specific subdirectories if supported
       - Consider using smaller, more focused repositories

    TYPICAL WORKFLOW:
    ```
    # 1. Index the repository (do this once)
    result = index_repository("github", "fastapi/fastapi", "main")
    
    # 2. Wait for indexing to complete (check result status)
    
    # 3. Query the indexed repository multiple times
    query_repository("How does dependency injection work?", [{"remote": "github", "repository": "fastapi/fastapi", "branch": "main"}])
    query_repository("Show me authentication middleware", [{"remote": "github", "repository": "fastapi/fastapi", "branch": "main"}])
    ```

    RETURN VALUE:
    Returns JSON string containing:
    - status: "queued", "processing", "completed", or "failed"
    - message: Human-readable status description
    - timestamp: When indexing was initiated
    - estimated_completion: Expected completion time (if available)

    Args:
        ctx: The MCP server provided context
        remote: The repository host, either "github" or "gitlab"
        repository: The repository in owner/repo format (e.g., "coleam00/mcp-mem0")
        branch: The branch to index (e.g., "main")
        reload: Whether to force reprocessing of the repository (default: True)
        notify: Whether to send an email notification when indexing is complete (default: False)
    """
    try:
        from src.utils import get_greptile_client
        greptile_client = get_greptile_client()
        result = await greptile_client.index_repository(remote, repository, branch, reload, notify)
        await greptile_client.aclose()
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
    previous_messages: Optional[List[Dict[str, Any]]] = None
) -> Union[str, AsyncGenerator[str, None]]:
    """
    Query repositories to get an answer with code references using advanced conversational AI.

    This tool provides sophisticated codebase querying with full session management, 
    streaming capabilities, and intelligent answer quality optimization.

    ## SESSION MANAGEMENT PATTERNS

    ### Session Continuity
    - **session_id**: Persistent identifier for multi-turn conversations
    - **Auto-generation**: If None, creates new session for standalone queries
    - **Persistence**: Session history automatically maintained across calls
    - **Context retention**: Previous messages influence subsequent responses

    ### Message History Patterns
    1. **New Conversation**: session_id=None, previous_messages=None
    2. **Continue Session**: session_id="existing_id", previous_messages=None  
    3. **External History**: session_id=None/existing, previous_messages=[...]
    4. **Hybrid Mode**: session_id="existing_id", previous_messages=[...] (overrides stored history)

    ## GENIUS MODE DECISION TREE

    ```
    Use genius=True when:
    ├── Complex architectural questions
    ├── Cross-file relationship analysis  
    ├── Design pattern identification
    ├── Performance optimization queries
    ├── Security vulnerability analysis
    └── Deep code understanding needed
    
    Use genius=False when:
    ├── Simple file location queries
    ├── Basic syntax questions
    ├── Quick reference lookups
    ├── Time-sensitive queries (<8-10s)
    └── Iterative exploration phases
    ```

    **Timing Considerations**: genius=True adds 8-10 seconds but provides significantly 
    deeper analysis, better context understanding, and more accurate responses.

    ## STREAMING vs NON-STREAMING

    ### Use stream=True for:
    - Long-form explanations
    - Complex analysis requiring time
    - Interactive user experiences
    - Large codebase queries
    - Real-time feedback needs

    ### Use stream=False for:
    - Quick responses needed
    - Automated processing
    - Simple queries
    - Session history persistence priority

    ## MESSAGE FORMAT EXAMPLES

    ### Basic Conversation
    ```python
    # Turn 1: Start new conversation
    query_repository(
        query="How does authentication work?",
        repositories=["github/owner/repo"],
        session_id=None  # Auto-generates new session
    )
    
    # Turn 2: Continue same conversation  
    query_repository(
        query="Show me the login endpoint implementation",
        repositories=["github/owner/repo"], 
        session_id="session_abc123"  # Use returned session_id
    )
    ```

    ### External Message History
    ```python
    previous_messages = [
        {"role": "user", "content": "Explain the database schema"},
        {"role": "assistant", "content": "The schema consists of..."},
        {"role": "user", "content": "How are migrations handled?"}
    ]
    
    query_repository(
        query="Show me the latest migration file",
        repositories=["github/owner/repo"],
        previous_messages=previous_messages
    )
    ```

    ### Streaming Response Handling
    ```python
    async for chunk in query_repository(
        query="Analyze the entire codebase architecture",
        repositories=["github/owner/repo"],
        stream=True,
        genius=True
    ):
        response_data = json.loads(chunk)
        # Process incremental response
    ```

    ## COMPLETE WORKFLOW EXAMPLES

    ### Multi-Turn Code Review Session
    ```python
    # 1. Initial broad question (genius=True for deep analysis)
    result1 = query_repository(
        query="What are the main security vulnerabilities in this codebase?",
        repositories=["github/owner/repo"],
        genius=True,
        session_id=None
    )
    session_id = json.loads(result1)["_session_id"]
    
    # 2. Follow-up on specific finding (genius=False for quick response)
    result2 = query_repository(
        query="Show me the SQL injection vulnerability you mentioned",
        repositories=["github/owner/repo"],
        genius=False,
        session_id=session_id
    )
    
    # 3. Implementation guidance (genius=True for comprehensive solution)
    result3 = query_repository(
        query="How should I fix this vulnerability using prepared statements?",
        repositories=["github/owner/repo"],
        genius=True,
        session_id=session_id
    )
    ```

    ### Performance Analysis Workflow
    ```python
    # 1. Streaming analysis of performance bottlenecks
    async for chunk in query_repository(
        query="Identify all performance bottlenecks and optimization opportunities",
        repositories=["github/owner/repo"],
        stream=True,
        genius=True,
        timeout=300  # 5 minute timeout for comprehensive analysis
    ):
        # Process streaming analysis results
        
    # 2. Deep dive into specific bottleneck
    result = query_repository(
        query="Focus on the database query performance issues",
        repositories=["github/owner/repo"],
        genius=True,
        session_id=session_id
    )
    ```

    ### Onboarding New Developer Session
    ```python
    # External conversation history from documentation/chat
    onboarding_context = [
        {"role": "user", "content": "I'm new to this codebase"},
        {"role": "assistant", "content": "Welcome! Let me help you understand..."},
        {"role": "user", "content": "What's the overall architecture?"}
    ]
    
    result = query_repository(
        query="Show me the main entry points and how data flows through the system",
        repositories=["github/owner/repo"],
        previous_messages=onboarding_context,
        genius=True,
        stream=True  # For comprehensive explanations
    )
    ```

    ## OPTIMIZATION PATTERNS

    ### Genius Mode Strategy
    - **Exploration Phase**: genius=False for rapid iteration
    - **Deep Analysis Phase**: genius=True for thorough understanding  
    - **Implementation Phase**: Mix based on complexity

    ### Session Management Strategy
    - **Logical Grouping**: Use same session_id for related questions
    - **Context Switching**: New session_id for different topics/repos
    - **History Management**: Use previous_messages for external context import

    Args:
        ctx: MCP server provided context
        query: The natural language query about the codebase
        repositories: List of repositories to query (format: ["github/owner/repo"])
        session_id: Session identifier for conversation continuity (auto-generated if None)
        stream: Enable streaming response for long queries (returns AsyncGenerator)
        genius: Enhanced analysis mode (+8-10s, significantly better quality)
        timeout: Query timeout in seconds (default: server-configured)
        previous_messages: Conversation history to import (format: [{"role": str, "content": str}])

    Returns:
        - stream=True: AsyncGenerator[str, None] yielding JSON response chunks
        - stream=False: str containing complete JSON response with _session_id field

    Response Format:
        {
            "output": "Generated response text",
            "messages": [...],  # Full conversation history
            "sources": [...],   # Code references and file locations
            "_session_id": "session_identifier"
        }
    """
    try:
        from src.utils import get_greptile_client
        greptile_client = get_greptile_client()
        greptile_context = ctx.request_context.lifespan_context
        session_manager: SessionManager = greptile_context.session_manager

        # Session logic
        sid = session_id or generate_session_id()
        # Build message history, defaulting to previous_messages if provided
        if previous_messages is not None:
            messages = previous_messages + [{"role": "user", "content": query}]
            await session_manager.set_history(sid, messages)
        else:
            # Retrieve stored history or start new conversation
            history = await session_manager.get_history(sid)
            messages = history + [{"role": "user", "content": query}]
            await session_manager.set_history(sid, messages)

        # Handle streaming response
        if stream:
            async def streaming_gen() -> AsyncGenerator[str, None]:
                async for chunk in greptile_client.stream_query_repositories(
                    messages, repositories, session_id=sid, genius=genius, timeout=timeout
                ):
                    yield json.dumps(chunk)
                await greptile_client.aclose()
            return streaming_gen()

        # Non-streaming query; get response fully then append to session history
        result = await greptile_client.query_repositories(
            messages, repositories, session_id=sid, stream=False, genius=genius, timeout=timeout
        )
        await greptile_client.aclose()

        # Persist new assistant/content response in session history if return has role/content fields
        if "messages" in result:
            await session_manager.set_history(sid, result["messages"])
        elif "output" in result:
            await session_manager.append_message(sid, {"role": "assistant", "content": result["output"]})

        result["_session_id"] = sid
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error querying repositories: {str(e)}"

@mcp.tool()
async def search_repository(ctx: Context, query: str, repositories: list, session_id: str = None, genius: bool = True) -> str:
    """Search repositories for relevant files without generating a full answer.

    OVERVIEW:
    This tool performs intelligent file discovery and relevance ranking within indexed repositories
    WITHOUT generating conversational responses. It returns structured lists of relevant files,
    code snippets, and locations that match your search criteria. Use this for file discovery,
    code exploration, and as a preprocessing step before detailed querying.

    ## SEARCH vs QUERY - KEY DIFFERENCES

    ### search_repository() - FILE DISCOVERY
    - **Purpose**: Find relevant files and code locations  
    - **Output**: Structured file lists, paths, relevance scores
    - **Use case**: "Where is the authentication logic?"
    - **Speed**: Fast (2-4 seconds)
    - **Session impact**: Minimal - primarily for discovery
    - **Result format**: File paths, snippets, metadata

    ### query_repository() - CONVERSATIONAL AI
    - **Purpose**: Generate detailed explanations and answers
    - **Output**: Natural language responses with code context
    - **Use case**: "How does the authentication system work?"
    - **Speed**: Slower (8-15 seconds with genius=True)
    - **Session impact**: Full conversation history management
    - **Result format**: Explanatory text with code references

    ## SESSION MANAGEMENT WITH SEARCH

    ### Session Continuity Patterns
    ```python
    # Pattern 1: Standalone search (most common)
    search_repository(
        query="find JWT token validation",
        repositories=[{"remote": "github", "repository": "owner/repo", "branch": "main"}],
        session_id=None  # Independent search, no session needed
    )

    # Pattern 2: Search within existing conversation context
    search_repository(
        query="locate the middleware files mentioned earlier",
        repositories=[...],
        session_id="existing_session_123"  # Reference prior conversation
    )

    # Pattern 3: Search preparation for follow-up query
    search_results = search_repository(
        query="find all database migration files",
        repositories=[...],
        session_id="new_session_456"
    )
    # Then use same session for detailed query
    query_repository(
        query="explain how these migrations work together",
        repositories=[...],
        session_id="new_session_456"  # Continue same session
    )
    ```

    ### Session Strategy Guidelines
    - **Independent Discovery**: session_id=None for one-off file searches
    - **Contextual Search**: Use existing session_id when search relates to ongoing conversation
    - **Workflow Preparation**: Create new session for search→query workflows
    - **No History Pollution**: Search operations add minimal context to session history

    ## GENIUS MODE DECISION TREE FOR SEARCH

    ```
    Use genius=True when:
    ├── Complex architectural file discovery
    │   ├── "Find all files implementing the observer pattern"
    │   ├── "Locate cross-cutting concerns and aspects"
    │   └── "Identify all dependency injection configurations"
    ├── Advanced semantic relationships  
    │   ├── "Find files that handle both authentication AND authorization"
    │   ├── "Locate error handling related to network operations"
    │   └── "Identify files implementing caching strategies"
    ├── Performance-critical code discovery
    │   ├── "Find all database query optimization files"
    │   ├── "Locate memory management implementations"
    │   └── "Identify async/await usage patterns"
    ├── Security-sensitive file location
    │   ├── "Find all input validation implementations"
    │   ├── "Locate cryptographic operations"
    │   └── "Identify privilege escalation points"
    └── Deep code pattern analysis
        ├── "Find similar implementation patterns to X"
        ├── "Locate all variations of Y algorithm"
        └── "Identify inconsistent implementations"

    Use genius=False when:
    ├── Simple file name or path searches
    │   ├── "Find config.py files"
    │   ├── "Locate README files"
    │   └── "Find all .env files"
    ├── Basic keyword matching
    │   ├── "Find files containing 'TODO'"
    │   ├── "Locate files with 'deprecated'"
    │   └── "Find test files"
    ├── Quick exploration and iteration
    │   ├── Initial codebase scanning
    │   ├── Rapid file discovery loops
    │   └── Performance-sensitive searches
    ├── Directory structure exploration
    │   ├── "Find all controllers"
    │   ├── "Locate model files"
    │   └── "Find migration directories"
    └── Time-sensitive discovery (<3s needed)
    ```

    **Performance Impact**: genius=True adds 2-4 seconds but provides significantly better
    semantic understanding, context awareness, and relevance ranking.

    ## QUICK START EXAMPLES

    ### Basic File Discovery
    ```python
    # Find authentication-related files
    search_repository(
        query="authentication login files",
        repositories=[{"remote": "github", "repository": "fastapi/fastapi", "branch": "main"}],
        genius=False  # Simple keyword search
    )

    # Advanced pattern discovery
    search_repository(
        query="files implementing middleware pattern with error handling",
        repositories=[{"remote": "github", "repository": "fastapi/fastapi", "branch": "main"}],
        genius=True  # Complex semantic search
    )
    ```

    ### Multi-Repository Search
    ```python
    # Search across multiple related repositories
    search_repository(
        query="database connection pooling implementation",
        repositories=[
            {"remote": "github", "repository": "sqlalchemy/sqlalchemy", "branch": "main"},
            {"remote": "github", "repository": "psycopg/psycopg2", "branch": "master"},
            {"remote": "github", "repository": "PyMySQL/PyMySQL", "branch": "main"}
        ],
        genius=True  # Cross-repo pattern analysis
    )
    ```

    ### Search for Query Workflow
    ```python
    # Step 1: Discover relevant files
    search_results = search_repository(
        query="API route handlers with validation",
        repositories=[{"remote": "github", "repository": "tiangolo/fastapi", "branch": "main"}],
        session_id=None,
        genius=True
    )

    # Step 2: Extract session for follow-up (if search used session)
    files_found = json.loads(search_results)
    
    # Step 3: Deep dive with query_repository
    detailed_analysis = query_repository(
        query=f"Explain how validation works in these files: {files_found['relevant_files']}",
        repositories=[{"remote": "github", "repository": "tiangolo/fastapi", "branch": "main"}],
        session_id="new_session_for_analysis",
        genius=True
    )
    ```

    ## INTEGRATION PATTERNS

    ### Search-First Exploration Pattern
    ```python
    # 1. Broad discovery phase
    core_files = search_repository(
        query="main application entry points and configuration",
        repositories=[target_repo],
        genius=False  # Fast initial discovery
    )

    # 2. Focused discovery phase  
    auth_files = search_repository(
        query="authentication and session management implementations",
        repositories=[target_repo],
        genius=True  # Detailed semantic search
    )

    # 3. Deep analysis phase
    auth_explanation = query_repository(
        query="How do these authentication components work together?",
        repositories=[target_repo],
        genius=True,
        session_id="exploration_session"
    )
    ```

    ### Code Review Preparation Pattern
    ```python
    # 1. Find files changed in recent commits
    recent_changes = search_repository(
        query="files with recent security updates or authentication changes",
        repositories=[target_repo],
        genius=True
    )

    # 2. Find related/dependent files
    dependencies = search_repository(
        query="files that import or depend on authentication modules",
        repositories=[target_repo],
        genius=True
    )

    # 3. Comprehensive review
    review_analysis = query_repository(
        query="Analyze security implications of recent authentication changes",
        repositories=[target_repo],
        genius=True,
        stream=True  # For detailed analysis
    )
    ```

    ### Debugging Discovery Pattern
    ```python
    # 1. Find error-prone areas
    error_files = search_repository(
        query="exception handling and error logging in payment processing",
        repositories=[target_repo],
        genius=True
    )

    # 2. Find similar implementations
    patterns = search_repository(
        query="similar error handling patterns in other modules",
        repositories=[target_repo],
        genius=True
    )

    # 3. Root cause analysis
    analysis = query_repository(
        query="What could cause payment errors based on these implementations?",
        repositories=[target_repo],
        genius=True,
        session_id="debug_session"
    )
    ```

    ### Performance Optimization Discovery
    ```python
    # 1. Find performance-critical paths
    critical_paths = search_repository(
        query="database queries and ORM operations in user-facing endpoints",
        repositories=[target_repo], 
        genius=True
    )

    # 2. Find caching implementations
    caching_files = search_repository(
        query="caching strategies and cache invalidation logic",
        repositories=[target_repo],
        genius=True
    )

    # 3. Optimization planning
    optimization_plan = query_repository(
        query="Suggest performance optimizations for these database operations",
        repositories=[target_repo],
        genius=True,
        stream=True
    )
    ```

    ## RESPONSE FORMAT AND USAGE

    ### Expected Response Structure
    ```json
    {
        "relevant_files": [
            {
                "file_path": "src/auth/authentication.py",
                "relevance_score": 0.95,
                "snippet": "class AuthenticationMiddleware...",
                "line_numbers": [15, 45, 78],
                "summary": "Main authentication logic implementation"
            }
        ],
        "total_files_found": 12,
        "search_metadata": {
            "query_complexity": "high",
            "genius_mode_used": true,
            "search_time_ms": 3240
        }
    }
    ```

    ### Processing Search Results
    ```python
    import json

    # Parse search results
    search_data = json.loads(search_repository(...))
    
    # Extract file paths for further analysis
    file_paths = [f["file_path"] for f in search_data["relevant_files"]]
    
    # Use in follow-up query
    query = f"Explain the interaction between these files: {', '.join(file_paths)}"
    detailed_response = query_repository(query, repositories, genius=True)
    ```

    ## OPTIMIZATION BEST PRACTICES

    ### Search Efficiency Strategy
    - **Quick Iteration**: Use genius=False for rapid exploration cycles
    - **Deep Discovery**: Use genius=True for final comprehensive searches  
    - **Batch Processing**: Combine multiple simple searches rather than complex ones
    - **Result Caching**: Reuse search results within same session when possible

    ### Session Management Strategy
    - **Independent Searches**: No session_id for one-off discoveries
    - **Workflow Sessions**: Consistent session_id for search→query workflows
    - **Context Preservation**: Use existing session_id when search builds on conversation
    - **Clean Separation**: New session_id for unrelated search tasks

    ### Repository Selection Strategy
    - **Single Repository**: Most common, fastest searches
    - **Related Repositories**: For cross-project pattern analysis  
    - **Comparative Analysis**: Multiple implementations of similar functionality
    - **Ecosystem Exploration**: Framework + plugins/extensions searches

    Args:
        ctx: The MCP server provided context
        query: The natural language query about the codebase for file discovery
        repositories: List of repositories to search, each with format {"remote": "github", "repository": "owner/repo", "branch": "main"}
        session_id: Optional session ID for continuing a conversation context
        genius: Whether to use enhanced semantic search capabilities (default: True)

    Returns:
        JSON string containing:
        - relevant_files: List of discovered files with paths, relevance scores, and snippets
        - total_files_found: Total number of matching files
        - search_metadata: Search performance and configuration details
        - file_summaries: Brief descriptions of what each file contains
        - relevance_ranking: Files ordered by relevance to the search query

    Prerequisites:
        - Target repositories must be indexed using index_repository() first
        - Search operates only on previously indexed repository content
        - Repository must be publicly accessible or properly authenticated
    """
    try:
        from src.utils import get_greptile_client
        greptile_client = get_greptile_client()
        messages = [{"role": "user", "content": query}]
        result = await greptile_client.search_repositories(messages, repositories, session_id, genius)
        await greptile_client.aclose()
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error searching repositories: {str(e)}"

@mcp.tool()
async def get_repository_info(ctx: Context, remote: str, repository: str, branch: str) -> str:
    """Get comprehensive information about an indexed repository including status, progress, and metadata.

    This tool is essential for monitoring repository indexing progress and determining when 
    repositories are ready for querying. It provides real-time status information and 
    detailed metadata about indexed repositories.

    ## REPOSITORY STATUS CHECKING

    ### Core Purpose
    - **Status Monitoring**: Check if repository indexing is complete, in progress, or failed
    - **Progress Tracking**: Monitor files processed vs total files during indexing
    - **Metadata Retrieval**: Get repository configuration and indexing statistics
    - **Workflow Orchestration**: Determine when repositories are ready for querying

    ## STATUS INTERPRETATION GUIDE

    ### Primary Status Values
    ```
    "COMPLETED"   → Repository fully indexed and ready for querying
    "PROCESSING"  → Indexing in progress, check filesProcessed/numFiles for progress
    "FAILED"      → Indexing failed, repository not available for queries
    "QUEUED"      → Repository waiting to be processed
    "NOT_FOUND"   → Repository not indexed or doesn't exist
    ```

    ### Progress Indicators
    - **filesProcessed**: Number of files successfully indexed
    - **numFiles**: Total files detected in repository
    - **Progress %**: (filesProcessed / numFiles) * 100

    ## QUICK START EXAMPLES

    ### Example 1: Check Repository Status
    ```python
    # Check if a repository is ready for querying
    info = await get_repository_info("github", "facebook/react", "main")
    status_data = json.loads(info)
    
    if status_data["status"] == "COMPLETED":
        print("Repository ready for queries!")
    elif status_data["status"] == "PROCESSING":
        progress = (status_data["filesProcessed"] / status_data["numFiles"]) * 100
        print(f"Indexing {progress:.1f}% complete")
    ```

    ### Example 2: Monitor Multiple Repositories
    ```python
    repos = [
        ("github", "microsoft/vscode", "main"),
        ("github", "nodejs/node", "main")
    ]
    
    for remote, repo, branch in repos:
        info = await get_repository_info(remote, repo, branch)
        data = json.loads(info)
        print(f"{repo}: {data['status']}")
    ```

    ## INTEGRATION WORKFLOWS

    ### Workflow 1: Index → Monitor → Query Pattern
    ```
    1. index_repository(remote, repo, branch)
    2. get_repository_info(remote, repo, branch)  ← Monitor until COMPLETED
    3. query_repository(query, [f"{remote}:{branch}:{repo}"])
    ```

    ### Workflow 2: Batch Processing
    ```
    1. Index multiple repositories
    2. Use get_repository_info to check all statuses
    3. Query only COMPLETED repositories
    4. Retry FAILED repositories with reload=True
    ```

    ### Workflow 3: Real-time Monitoring
    ```python
    async def wait_for_indexing(remote, repo, branch, timeout=300):
        start_time = time.time()
        while time.time() - start_time < timeout:
            info = await get_repository_info(remote, repo, branch)
            data = json.loads(info)
            
            if data["status"] == "COMPLETED":
                return True
            elif data["status"] == "FAILED":
                return False
                
            await asyncio.sleep(10)  # Check every 10 seconds
        return False  # Timeout
    ```

    ## RESPONSE SCHEMA

    ### Complete Response Structure
    ```json
    {
      "id": "github:main:owner/repo",           // Unique repository identifier
      "status": "COMPLETED",                    // Current indexing status
      "repository": "owner/repo",               // Repository path
      "remote": "github",                       // Source platform
      "branch": "main",                         // Indexed branch
      "private": false,                         // Repository visibility
      "filesProcessed": 234,                    // Files successfully indexed
      "numFiles": 234,                          // Total files in repository
      "lastIndexed": "2024-01-15T10:30:00Z",   // Last indexing timestamp
      "indexingTime": 45.2,                    // Indexing duration in seconds
      "size": "12.5MB"                         // Repository size
    }
    ```

    ## TROUBLESHOOTING GUIDANCE

    ### Status-Based Troubleshooting

    #### FAILED Status
    ```
    Possible Causes:
    ├── Repository access denied (private repo without auth)
    ├── Invalid repository path or branch
    ├── Repository too large (exceeds limits)
    ├── Network connectivity issues
    └── Temporary service issues
    
    Solutions:
    ├── Verify repository exists and is accessible
    ├── Check branch name spelling
    ├── Retry with reload=True in index_repository
    └── Contact support for persistent failures
    ```

    #### PROCESSING Stuck
    ```
    If filesProcessed doesn't increase after 15+ minutes:
    ├── Large repository may take time (normal for 1000+ files)
    ├── Check progress ratio: filesProcessed/numFiles
    ├── Consider canceling and re-indexing if truly stuck
    └── Monitor for 30+ minutes before concluding it's stuck
    ```

    #### NOT_FOUND Status
    ```
    Repository not in Greptile system:
    ├── Repository was never indexed
    ├── Repository was deleted/removed
    ├── Incorrect remote/repository/branch combination
    └── Use index_repository first to add repository
    ```

    ### Error Response Patterns
    ```
    "Error getting repository info: 404" → Repository not found
    "Error getting repository info: 403" → Access denied
    "Error getting repository info: 500" → Server error, retry
    ```

    ## WORKFLOW ORCHESTRATION EXAMPLES

    ### Smart Query Preparation
    ```python
    async def prepare_for_query(repos_list):
        ready_repos = []
        for remote, repo, branch in repos_list:
            info = await get_repository_info(remote, repo, branch)
            data = json.loads(info)
            
            if data["status"] == "COMPLETED":
                ready_repos.append(f"{remote}:{branch}:{repo}")
            elif data["status"] == "PROCESSING":
                print(f"Waiting for {repo} to finish indexing...")
            else:
                print(f"Repository {repo} not ready: {data['status']}")
                
        return ready_repos
    ```

    ### Health Check Implementation
    ```python
    async def repository_health_check(remote, repo, branch):
        try:
            info = await get_repository_info(remote, repo, branch)
            data = json.loads(info)
            
            return {
                "healthy": data["status"] == "COMPLETED",
                "status": data["status"],
                "progress": data.get("filesProcessed", 0) / data.get("numFiles", 1),
                "last_indexed": data.get("lastIndexed"),
                "recommendations": get_health_recommendations(data)
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    ```

    Args:
        ctx: The MCP server provided context
        remote: The repository host, either "github" or "gitlab"
        repository: The repository in owner/repo format (e.g., "facebook/react")
        branch: The branch that was indexed (e.g., "main", "develop")

    Returns:
        JSON string containing complete repository information and status.
        Parse with json.loads() to access individual fields programmatically.

    Raises:
        Returns error string if repository access fails or network issues occur.
    """
    try:
        from src.utils import get_greptile_client
        greptile_client = get_greptile_client()
        repository_id = f"{remote}:{branch}:{repository}"
        result = await greptile_client.get_repository_info(repository_id)
        await greptile_client.aclose()
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
