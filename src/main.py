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
    GreptileClient,
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
    default_session_id: str = "7dc8f451-9bf7-4262-a664-0865ac578e6c"  # Default session ID from our React queries

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
    description="""🔍 Greptile MCP - Natural Language Code Search & Analysis

Search and analyze code across multiple repositories using natural language queries.
Perfect for understanding codebases, comparing implementations, and finding patterns.

QUICK START:
1. Use 'greptile_help' tool for complete guide
2. Index repos first: index_repository("github", "owner/repo", "branch")
3. Query them: query_simple(ctx, "your question", [repos])

Key Features:
✓ Multi-repository search and analysis
✓ Natural language queries
✓ Code-aware responses with references
✓ Framework comparisons
✓ Pattern matching across codebases

Common Use Cases:
- "How does authentication work?"
- "Compare error handling in Express vs Koa"
- "Find all uses of WebSocket"
- "Explain the architecture of this service"
""",
    lifespan=greptile_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=os.getenv("PORT", "8050")
)

@mcp.tool()
async def greptile_help(ctx: Context) -> str:
    """
    Get started with Greptile MCP - Your guide to searching and analyzing code repositories.

    This tool provides comprehensive documentation on how to use all Greptile MCP features.
    """
    help_text = """
# 🚀 Greptile MCP Quick Start Guide

Welcome to Greptile MCP! This tool provides AI expertise for any codebase, helping you understand code structure and get custom integration instructions.

## 🎯 Objectives - What You Can Do

### 1. Understand Code Architecture
- Analyze authentication flows in codebases
- Understand component relationships
- Map out service architectures
- Trace data flow through systems

### 2. Add Features with AI Guidance
- Get step-by-step implementation instructions
- Add authentication (Google Sign-in, OAuth, etc.)
- Integrate third-party services
- Implement new functionality with best practices

### 3. Compare & Learn
- Compare implementations across frameworks
- Understand different approaches to similar problems
- Learn from open-source codebases
- Make informed architectural decisions

### 4. Speed Up Development
- Get up to speed on new codebases quickly
- Find relevant code examples
- Understand existing patterns before coding
- Reduce time spent reading documentation

## 📋 Real-World Example: Adding Google Sign-In

Here's a complete workflow for adding authentication to your app:

### Step 1: Index Your Application
```python
# Add your app's repository
await index_repository(ctx, "github", "mycompany/myapp", "main")
```

### Step 2: Understand Current Authentication
```python
repos = [{"remote": "github", "repository": "mycompany/myapp", "branch": "main"}]
result = await query_repository(ctx,
    "How does authentication work in this codebase? Show me the auth flow",
    repos
)
```

### Step 3: Add Authentication Library Context
```python
# Add the auth library your app uses (e.g., NextAuth)
await index_repository(ctx, "github", "nextauthjs/next-auth", "main")

repos = [
    {"remote": "github", "repository": "mycompany/myapp", "branch": "main"},
    {"remote": "github", "repository": "nextauthjs/next-auth", "main": "main"}
]
```

### Step 4: Get Implementation Instructions
```python
result = await query_repository(ctx,
    "How do I add Google Sign-in to this application? Give me step-by-step instructions",
    repos
)
```

### Step 5: Follow AI-Generated Instructions
Greptile will provide:
- Required library installations
- Google provider configuration
- Environment variable setup (.env.local)
- Code changes needed
- Component updates
- Testing instructions

## 🛠️ Common Use Cases

### Understanding a New Codebase
```python
# 1. Index the repository
await index_repository(ctx, "github", "strapi/strapi", "main")

# 2. Ask architectural questions
repos = [{"remote": "github", "repository": "strapi/strapi", "branch": "main"}]
await query_repository(ctx, "Explain the plugin architecture", repos)
await query_repository(ctx, "How does the database layer work?", repos)
await query_repository(ctx, "What's the authentication flow?", repos)
```

### Comparing Implementations
```python
# Compare authentication in different frameworks
repos = [
    {"remote": "github", "repository": "nestjs/nest", "branch": "master"},
    {"remote": "github", "repository": "expressjs/express", "branch": "master"}
]
result = await compare_repositories(ctx,
    "How do these frameworks handle authentication middleware?",
    repos
)
```

### Finding Code Patterns
```python
# Search for WebSocket implementations
repos = [
    {"remote": "github", "repository": "socketio/socket.io", "branch": "main"},
    {"remote": "github", "repository": "mycompany/myapp", "branch": "main"}
]
result = await search_repository(ctx,
    "WebSocket connection handling",
    repos
)
```

## 🔧 Basic Workflow

### Step 1: Index Repositories
```python
await index_repository(ctx, "github", "owner/repo", "branch")
```

### Step 2: Create Repository List
```python
repos = [{
    "remote": "github",
    "repository": "owner/repo",
    "branch": "main"
}]
```

### Step 3: Query with Natural Language
```python
result = await query_repository(ctx, "Your question here", repos)
```

## 📚 Available Tools

### Essential Tools
1. `greptile_help` - This guide
2. `index_repository` - Make repos searchable
3. `query_repository` - Ask questions with context
4. `compare_repositories` - Compare implementations
5. `search_repository` - Find specific patterns

### Repository Format
```json
{
    "remote": "github",      // or "gitlab"
    "repository": "owner/repo",
    "branch": "main"
}
```

## 💡 Pro Tips

1. **Index First**: Always index repositories before querying
2. **Add Context**: Include relevant libraries for better answers
3. **Be Specific**: Ask detailed questions for better results
4. **Use Examples**: "Show me how X works with code examples"
5. **Iterative Queries**: Build on previous answers

## 📝 Session ID Management: IMPORTANT FOR FOLLOW-UP QUESTIONS

**Are you asking a follow-up question?** If yes, you NEED to use a session ID!

Examples of follow-up questions:
- "Tell me more about X" after asking about X
- "How does this specific part work?" after a general question
- "Can you explain that in more detail?" after any response
- "What about [related topic]?" after discussing a topic

Follow this simple workflow:

1. **First Query**: Make your initial query WITHOUT specifying a session_id
   ```python
   # Initial question
   result1 = await query_repository(ctx,
       "How does authentication work?",
       repositories
   )
   # Every response automatically includes a session ID
   ```

2. **Extract Session ID**: Get the session ID from the response
   ```python
   import json
   response_data = json.loads(result1)
   session_id = response_data["_session_id"]  # This is required for follow-ups!
   ```

3. **ANY Follow-up Question**: ALWAYS use the session ID for ANY follow-up
   ```python
   # This is a follow-up, so we MUST use the session_id
   result2 = await query_repository(ctx,
       "What about password reset functionality?",  # This is a follow-up question
       repositories,
       session_id=session_id  # Without this, the system won't remember your first question
   )
   ```

Without the session ID, the system treats each question as completely new and forgets your previous questions and their context.

## ⚠️ Common Mistakes

❌ Wrong repository format: "https://github.com/owner/repo"
✅ Correct format: "owner/repo"

❌ Not indexing before querying
✅ Always index first

❌ Vague questions: "How does this work?"
✅ Specific questions: "How does the auth middleware validate JWT tokens?"

❌ Generating your own session ID for the first query
✅ Let the system generate a session ID and extract it from the response

❌ Asking a follow-up question WITHOUT using the session_id from the previous response
✅ ALWAYS use the session_id for ANY follow-up question

## 🚀 Quick Examples

### Multi-Turn Conversation Example (Follow-up Questions)
```python
# Step 1: Initial question
result1 = await query_repository(ctx,
    "How do React Server Components work?",
    repos
)

# Step 2: Extract the session ID
import json
response_data = json.loads(result1)
session_id = response_data["_session_id"]

# Step 3: Follow-up question USING the session ID
result2 = await query_repository(ctx,
    "How does caching work with Server Components?",  # This is a follow-up!
    repos,
    session_id=session_id  # REQUIRED for follow-ups!
)

# Another follow-up question
result3 = await query_repository(ctx,
    "Can you show me an example of streaming with Server Components?",  # Another follow-up!
    repos,
    session_id=session_id  # Still using the SAME session ID!
)
```

### Add Feature
```python
await query_repository(ctx,
    "How do I add rate limiting to this Express API?",
    repos
)
```

### Debug Issue
```python
await query_repository(ctx,
    "Why might authentication fail in this flow?",
    repos
)
```

### Best Practices
```python
await compare_repositories(ctx,
    "What are the error handling patterns used?",
    repos
)
```

Happy coding! Use Greptile to understand any codebase and build features faster. 🎉
"""
    return help_text

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
    """
    [REQUIRED FIRST STEP] Index a repository to make it searchable.

    Quick Example:
    await index_repository(ctx, "github", "facebook/react", "main")

    Format: repository MUST be "owner/repo" (e.g., "facebook/react", NOT just "react")

    Args:
        remote: "github" or "gitlab"
        repository: "owner/repo" format (REQUIRED FORMAT)
        branch: branch name (e.g., "main", "master", "develop")
        reload: Force re-index even if already indexed (default: True)
        notify: Email notification when done (default: False)

    Common repos:
    - "facebook/react" (React framework)
    - "vuejs/core" (Vue.js framework)
    - "angular/angular" (Angular framework)
    - "nodejs/node" (Node.js runtime)

    Returns: JSON with indexing status
    Note: Must index before querying!
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
    Query one or more code repositories to get answers with source references.

    QUICK START:
    repositories = [
        {"remote": "github", "repository": "facebook/react", "branch": "main"},
        {"remote": "github", "repository": "vuejs/core", "branch": "main"}
    ]
    result = await query_repository(ctx, "How do these handle state?", repositories)

    REQUIRED FORMAT:
    Each repository must have: remote, repository, branch
    - remote: "github" or "gitlab"
    - repository: "owner/repo" format (e.g., "facebook/react")
    - branch: branch name (e.g., "main", "master", "develop")

    FEATURES:
    ✓ Query multiple repositories simultaneously
    ✓ Get answers with specific code references
    ✓ Maintain conversation history with session_id
    ✓ Stream responses for long queries

    SESSION ID USAGE - REQUIRED FOR ANY FOLLOW-UP QUESTIONS:
    1. First query: Don't specify a session_id (system will generate one)
    2. Extract the session ID from the response: response_data["_session_id"]
    3. ALWAYS use this session ID for ANY follow-up question
       Without it, the system will forget your previous questions!

    COMMON PATTERNS:
    1. Single repo: [{"remote": "github", "repository": "owner/repo", "branch": "main"}]
    2. Compare frameworks: Add multiple repos to compare implementations
    3. Microservices: Query across related service repositories

    Args:
        ctx: MCP context (provided automatically)
        query: Your question about the code
        repositories: List of repos to search (see format above)
        session_id: For follow-up queries, use the _session_id from previous response
        stream: Enable streaming responses (default: False)
        genius: Enhanced accuracy mode (default: True)
        timeout: Max seconds to wait (optional)
        messages: Previous conversation history (optional)

    Returns:
        JSON with answer, source code references, and _session_id for follow-up queries

    Note: Repositories must be indexed first using index_repository()
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

        # Session logic - use default session ID if none provided
        sid = session_id or greptile_context.default_session_id

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
    """Search one or more repositories for relevant files without generating a full answer.

    This tool returns a list of relevant files based on a query without generating
    a complete answer. The repositories must have been indexed first. Supports
    searching across multiple repositories simultaneously.

    SESSION ID USAGE - REQUIRED FOR ANY FOLLOW-UP QUESTIONS:
    1. First query: Don't specify a session_id (system will generate one)
    2. Extract the session ID from the response: response_data["_session_id"]
    3. ALWAYS use this session ID for ANY follow-up question
       Without it, the system will forget your previous questions!

    Args:
        ctx: The MCP server provided context which includes the Greptile client
        query: The natural language query about the codebase(s)
        repositories: List of repositories to search (supports multiple repos)
                     Each should include: remote, repository, and branch
        session_id: For follow-up queries, use the session ID from previous response
        genius: Whether to use the enhanced search capabilities (default: True)
        messages: Optional message history in the format [{"id": "msg1", "content": "...", "role": "user/assistant"}]

    Returns:
        JSON with relevant files and their scores, may include session ID for follow-ups
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

        # Use default session ID if none provided
        greptile_context = ctx.request_context.lifespan_context
        effective_session_id = session_id or greptile_context.default_session_id

        result = await greptile_client.search_repositories(formatted_messages, repositories, effective_session_id, genius)

        # Attach the session_id for client reference
        result["_session_id"] = effective_session_id
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

    SESSION ID USAGE - REQUIRED FOR ANY FOLLOW-UP QUESTIONS:
    1. First query: Don't specify a session_id (system will generate one)
    2. Extract the session ID from the response: response_data["_session_id"]
    3. ALWAYS use this session ID for ANY follow-up question
       Without it, the system will forget your previous questions!

    Args:
        ctx: MCP server provided context
        messages: Full message history in Greptile API format: [{"id": "msg1", "content": "...", "role": "user/assistant"}]
        repositories: List of repositories to query
        session_id: For follow-up queries, use the _session_id from previous response
        stream: Enable streaming for long queries (returns async generator)
        genius: Use enhanced answer quality (may take longer)
        timeout: Optional per-query timeout (seconds)

    Returns:
        - For streaming: async generator yielding JSON strings.
        - For non-streaming: formatted JSON string with answer, references, and _session_id.
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

        # Session logic - use default session ID if none provided
        sid = session_id or greptile_context.default_session_id

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
    [EASIEST WAY TO START] Ask a simple question about code repositories.

    Quick Example:
    repos = [{"remote": "github", "repository": "facebook/react", "branch": "main"}]
    result = await query_simple(ctx, "What is useState?", repos)

    Perfect for:
    - One-off questions
    - Quick code lookups
    - Simple explanations

    Args:
        query: Your question about the code
        repositories: List of repos (see format in example)
        genius: Use smart mode for better answers (default: True)

    No session management needed - just ask and get answers!
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

@mcp.tool()
async def query_multiple_repositories(
    ctx: Context,
    query: str,
    repositories: list,
    genius: bool = True,
    stream: bool = False,
    timeout: Optional[float] = None
) -> Union[str, AsyncGenerator[str, None]]:
    """
    Query multiple repositories simultaneously with a single question.

    This tool allows you to search across multiple repositories at once, getting
    a unified answer that considers code from all specified repositories.

    Args:
        ctx: MCP server provided context
        query: The natural language query about the codebases
        repositories: List of repositories to query, each should include:
                    - remote: "github" or "gitlab"
                    - repository: "owner/repo" format
                    - branch: branch name (e.g., "main")
                    Example: [
                        {"remote": "github", "repository": "facebook/react", "branch": "main"},
                        {"remote": "github", "repository": "vercel/next.js", "branch": "canary"}
                    ]
        genius: Use enhanced answer quality (default: True)
        stream: Enable streaming for long queries (default: False)
        timeout: Optional per-query timeout (seconds)

    Returns:
        - For streaming: async generator yielding JSON strings
        - For non-streaming: formatted JSON string with combined results

    Example:
        repos = [
            {"remote": "github", "repository": "facebook/react", "branch": "main"},
            {"remote": "github", "repository": "vuejs/core", "branch": "main"}
        ]
        result = await query_multiple_repositories(ctx, "How do these frameworks handle state management?", repos)
    """
    try:
        # Validate repositories format
        for repo in repositories:
            if not all(key in repo for key in ["remote", "repository", "branch"]):
                return json.dumps({
                    "error": "Each repository must include 'remote', 'repository', and 'branch' fields"
                }, indent=2)

        # Use query_simple for straightforward implementation
        if not stream:
            return await query_simple(ctx, query, repositories, genius)

        # For streaming, use the advanced method
        messages = [{
            "id": "multi_query_0",
            "content": query,
            "role": "user"
        }]

        return await query_repository_advanced(
            ctx=ctx,
            messages=messages,
            repositories=repositories,
            session_id=None,
            stream=stream,
            genius=genius,
            timeout=timeout
        )
    except Exception as e:
        return f"Error querying multiple repositories: {str(e)}"

@mcp.tool()
async def compare_repositories(
    ctx: Context,
    comparison_query: str,
    repositories: list,
    genius: bool = True
) -> str:
    """
    Compare implementation details across multiple repositories.

    This specialized tool is optimized for comparing how different repositories
    handle similar concepts, patterns, or features.

    Args:
        ctx: MCP server provided context
        comparison_query: Query focused on comparing aspects across repos
                         e.g., "Compare error handling approaches"
        repositories: List of repositories to compare
        genius: Use enhanced analysis (default: True)

    Returns:
        JSON string with comparative analysis

    Example:
        repos = [
            {"remote": "github", "repository": "expressjs/express", "branch": "master"},
            {"remote": "github", "repository": "koajs/koa", "branch": "master"}
        ]
        result = await compare_repositories(ctx, "Compare middleware implementation", repos)
    """
    # Enhance the query for better comparison
    enhanced_query = f"Compare and contrast the following across the provided repositories: {comparison_query}. Provide specific examples from each codebase."

    return await query_multiple_repositories(
        ctx=ctx,
        query=enhanced_query,
        repositories=repositories,
        genius=genius,
        stream=False
    )

@mcp.tool()
async def search_multiple_repositories(
    ctx: Context,
    search_term: str,
    repositories: list,
    file_pattern: Optional[str] = None,
    genius: bool = True
) -> str:
    """
    Search for specific terms or patterns across multiple repositories.

    This tool is optimized for finding specific code patterns, function names,
    or implementations across multiple codebases without generating a full answer.

    Args:
        ctx: MCP server provided context
        search_term: The term or pattern to search for
        repositories: List of repositories to search
        file_pattern: Optional file pattern to filter results (e.g., "*.ts", "*.py")
        genius: Use enhanced search capabilities (default: True)

    Returns:
        JSON string with search results from all repositories

    Example:
        repos = [
            {"remote": "github", "repository": "django/django", "branch": "main"},
            {"remote": "github", "repository": "pallets/flask", "branch": "main"}
        ]
        result = await search_multiple_repositories(ctx, "authentication middleware", repos, "*.py")
    """
    # Enhance search query with file pattern if provided
    search_query = search_term
    if file_pattern:
        search_query = f"{search_term} in files matching {file_pattern}"

    # Use the existing search_repository function which already supports multiple repos
    return await search_repository(
        ctx=ctx,
        query=search_query,
        repositories=repositories,
        genius=genius
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
