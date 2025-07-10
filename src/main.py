# -*- coding: utf-8 -*-
from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dotenv import load_dotenv
import asyncio
import json
import os
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator, Union, Coroutine
import uuid

from src.utils import (
    get_greptile_client,
    GreptileClient,
    SessionManager,
    generate_session_id
)

# Global client instance (will be initialized on first use)
_greptile_client: Optional[GreptileClient] = None

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

## 🔄 SYSTEMATIC WORKFLOWS FOR "VIBE CODERS"

### ⚡ CRITICAL: After Committing New Code
**Problem**: Your code changed, but Greptile is analyzing old code
**Solution**: ALWAYS re-index with reload=True after commits

```python
# Step 1: Force re-index with latest commits (CRITICAL!)
await index_repository(
    remote="github", 
    repository="your-username/your-repo", 
    branch="main",
    reload=True,  # ← CRITICAL: Forces update with latest commits
    notify=False
)

# Step 2: Verify indexing completed
status = await get_repository_info("github", "your-username/your-repo", "main")
# Wait until status shows "COMPLETED"

# Step 3: Query your updated code
result = await query_repository(
    "How does my new feature work?",
    [{"remote": "github", "repository": "your-username/your-repo", "branch": "main"}]
)
```

### 🔧 SYSTEMATIC DEBUGGING WORKFLOW
When something breaks, follow this exact sequence:

```python
# 1. Understand the error context
await query_repository(
    "What could cause this error: [paste your error]? Show me the relevant code paths",
    repos
)

# 2. Trace the execution flow
await query_repository(
    "Trace the execution from [entry point] to where this error occurs",
    repos,
    session_id=session_id  # Use same session!
)

# 3. Find similar patterns that work
await query_repository(
    "Show me working examples of this same functionality in the codebase",
    repos,
    session_id=session_id
)

# 4. Get specific fix suggestions
await query_repository(
    "How should I fix this specific issue? Give me exact code changes",
    repos,
    session_id=session_id
)
```

### 📋 FEATURE IMPLEMENTATION WORKFLOW
For building new features systematically:

```python
# 1. Research existing patterns
await query_repository(
    "How is similar functionality implemented in this codebase?",
    repos
)

# 2. Get step-by-step blueprint
await query_repository(
    "Give me a step-by-step implementation plan for [your feature]",
    repos,
    session_id=session_id
)

# 3. Get specific code examples
await query_repository(
    "Show me exact code examples for each step",
    repos,
    session_id=session_id
)
```

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
    """📚 INDEX UTILITY: Make repositories searchable (REQUIRED FIRST STEP).

    ⚡ PERFORMANCE PROFILE:
    • Operation: Repository preprocessing for search/query operations
    • Duration: 30 seconds - 10 minutes (depends on repo size)
    • Cost: API rate limits apply - use reload strategically
    • Prerequisite: Required before any search/query operations

    🎯 WHEN TO USE THIS TOOL:
    ✅ Before first search/query of any repository
    ✅ After committing new code (reload=True)
    ✅ When switching to different branch
    ✅ When repository structure changed significantly
    ✅ After major refactoring or new features
    
    ❌ DON'T OVERUSE:
    ❌ Repeatedly without code changes (wastes resources)
    ❌ For every single query (index once, query many)
    ❌ On identical branch/commit (use reload=False)

    🚀 QUICK START EXAMPLES:
    
    # Index your own project (FIRST TIME)
    await index_repository(ctx, "github", "myusername/myproject", "main")
    
    # Re-index after pushing changes (CRITICAL FOR FRESH CODE)
    await index_repository(ctx, "github", "myusername/myproject", "main", 
                         reload=True)  # Forces latest commit analysis
    
    # Index popular framework for learning
    await index_repository(ctx, "github", "facebook/react", "main")
    
    # Index specific branch
    await index_repository(ctx, "github", "vercel/next.js", "canary")

    🔄 RELOAD LOGIC (CRITICAL FOR ACCURACY):
    
    reload=True (DEFAULT - Recommended):
    ✅ Forces fresh analysis of latest commits
    ✅ Captures recent code changes
    ✅ Essential after pushing new code
    ✅ Ensures search/query accuracy
    ⚠️  Uses API quota (but necessary for accuracy)
    
    reload=False (Optimization):
    ✅ Faster if repository unchanged
    ✅ Saves API quota for unchanged repos
    ❌ May analyze stale code if changes exist
    ❌ Risk of outdated search results

    📊 STRATEGIC RELOAD PATTERNS:
    
    YOUR ACTIVE PROJECT: Always reload=True
    ```python
    # After git push - ALWAYS reload=True
    await index_repository(ctx, "github", "you/project", "main", reload=True)
    ```
    
    STABLE LIBRARIES: reload=False for repeated access
    ```python
    # Framework learning - reload=False after first index
    await index_repository(ctx, "github", "facebook/react", "main", reload=False)
    ```
    
    COMPARISON STUDIES: reload=False for batch indexing
    ```python
    # Indexing multiple frameworks - reload=False for efficiency
    frameworks = [("facebook/react", "main"), ("vuejs/core", "main")]
    for repo, branch in frameworks:
        await index_repository(ctx, "github", repo, branch, reload=False)
    ```

    📁 REPOSITORY FORMAT REQUIREMENTS:
    
    CORRECT FORMAT: "owner/repo"
    ✅ "facebook/react" - Facebook's React repository
    ✅ "microsoft/vscode" - Microsoft's VS Code
    ✅ "torvalds/linux" - Linus Torvalds' Linux kernel
    ✅ "your-username/your-project" - Your personal project
    
    INVALID FORMATS:
    ❌ "https://github.com/facebook/react" - Full URL not accepted
    ❌ "react" - Missing owner
    ❌ "facebook-react" - Wrong separator
    ❌ "facebook/react.git" - Don't include .git

    🌐 SUPPORTED PLATFORMS:
    
    GitHub ("github"):
    • Public repositories: Full access
    • Private repositories: Requires authentication
    • Organization repositories: Full access if public
    
    GitLab ("gitlab"):
    • Public repositories: Full access  
    • Private repositories: Requires authentication
    • Self-hosted: Not supported (GitLab.com only)

    🎯 BRANCH TARGETING:
    
    COMMON BRANCHES:
    • "main" - Most modern repositories
    • "master" - Older repositories
    • "develop" - Development branches
    • "canary" - Next.js and other frameworks
    • "v1.0" - Tagged releases
    
    BRANCH DISCOVERY:
    Check repository on GitHub/GitLab to see available branches.
    Default branch is usually "main" or "master".

    🔧 TROUBLESHOOTING:
    
    "Repository not found":
    • Verify repository exists and is public
    • Check owner/repo format (not URL)
    • Ensure you have access to private repos
    
    "Branch not found":
    • Check available branches on GitHub/GitLab
    • Common branches: main, master, develop
    • Case-sensitive: "Main" ≠ "main"
    
    "Indexing failed":
    • Repository might be too large
    • Try again after a few minutes
    • Check rate limits and quotas
    
    "Stale search results":
    • Code changed but results don't reflect changes
    • Solution: Re-run with reload=True
    • Always reload after pushing commits

    📈 PERFORMANCE OPTIMIZATION:
    
    FASTEST: Small repo + reload=False + notify=False
    ```python
    await index_repository(ctx, "github", "owner/small-repo", "main", 
                         reload=False, notify=False)
    ```
    
    BALANCED: Medium repo + reload=True + notify=False  
    ```python
    await index_repository(ctx, "github", "owner/app", "main", 
                         reload=True, notify=False)
    ```
    
    MONITORED: Large repo + reload=True + notify=True
    ```python
    await index_repository(ctx, "github", "large/framework", "main", 
                         reload=True, notify=True)
    ```

    ⏱️ INDEXING STATUS MONITORING:
    
    After indexing, monitor progress:
    ```python
    # Start indexing
    result = await index_repository(ctx, "github", "owner/repo", "main")
    
    # Check status periodically
    status = await get_repository_info(ctx, "github", "owner/repo", "main")
    print(status["status"])  # INDEXING, COMPLETED, FAILED
    
    # Wait for COMPLETED before searching/querying
    ```

    🏗️ SYSTEMATIC DEVELOPMENT WORKFLOW:
    
    1. INITIAL PROJECT SETUP:
    ```python
    await index_repository(ctx, "github", "you/newproject", "main", reload=True)
    ```
    
    2. AFTER EACH DEVELOPMENT SESSION:
    ```python
    # After git push
    await index_repository(ctx, "you/project", "main", reload=True)
    ```
    
    3. ADDING REFERENCE LIBRARIES:
    ```python
    # One-time indexing for learning/comparison
    await index_repository(ctx, "facebook/react", "main", reload=False)
    ```

    📋 REPOSITORY EXAMPLES BY CATEGORY:
    
    WEB FRAMEWORKS:
    • "facebook/react" - React library
    • "vuejs/core" - Vue.js framework  
    • "angular/angular" - Angular framework
    • "sveltejs/svelte" - Svelte framework
    
    BACKEND FRAMEWORKS:
    • "expressjs/express" - Express.js
    • "nestjs/nest" - NestJS framework
    • "django/django" - Django framework
    • "rails/rails" - Ruby on Rails
    
    DEVELOPMENT TOOLS:
    • "microsoft/vscode" - VS Code editor
    • "webpack/webpack" - Webpack bundler
    • "vitejs/vite" - Vite build tool
    • "typescript-eslint/typescript-eslint" - TypeScript ESLint

    Args:
        ctx: MCP context (auto-provided)
        remote: Repository platform ("github" or "gitlab")
        repository: Repository identifier in "owner/repo" format
        branch: Target branch name ("main", "master", etc.)
        reload: Force re-index latest commits (default: True for accuracy)
        notify: Email notification when indexing completes (default: False)

    Returns:
        JSON with:
        • status: Indexing operation status
        • repository: Confirmed repository identifier
        • branch: Confirmed branch name
        • timestamp: When indexing started
        • estimated_completion: Expected completion time
        
    🚨 CRITICAL SUCCESS FACTOR:
    ALWAYS re-index with reload=True after committing new code.
    Stale indexes lead to outdated search/query results!
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

async def get_greptile_client() -> Coroutine[Any, Any, GreptileClient]:
    """Get or create the Greptile client instance."""
    global _greptile_client
    if _greptile_client is None:
        api_key = os.getenv("GREPTILE_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")
        
        if not api_key:
            raise ValueError("GREPTILE_API_KEY environment variable is required")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
            
        _greptile_client = get_greptile_client(api_key, github_token)
    
    return _greptile_client

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
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})

@mcp.tool
async def query_repository(
    ctx: Context,
    query: str,
    repositories: str,  # JSON string representation
    session_id: Optional[str] = None,
    genius: bool = True,
    messages: Optional[List[Dict[str, str]]] = None,
) -> Union[str, AsyncGenerator[str, None]]:
    """Light-weight wrapper around `query_repository_advanced` that accepts the
    original JSON-string parameters expected by Smithery."""

    # Parse repositories JSON
    try:
        repos: List[Dict[str, str]] = json.loads(repositories) if isinstance(repositories, str) else repositories
    except json.JSONDecodeError as exc:
        return json.dumps({"error": f"Invalid repositories JSON: {exc}"})

    # Build the messages list expected by the advanced endpoint
    history: List[Dict[str, str]] = messages or []
    history.append({"id": f"msg_{len(history)}", "content": query, "role": "user"})

    return await query_repository_advanced(
        ctx,
        history,
        repos,
        session_id=session_id,
        stream=False,
        genius=genius,
        timeout=None,
    )

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
        repository_id = f"{remote}:{branch}:{repository}"
        result = await client.get_repository_info(repository_id)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})

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
    🔧 ADVANCED TOOL: Direct message history control - Maximum flexibility for complex conversations.
    
    This is the most powerful query tool that gives you complete control over conversation history.
    Use when you need to construct custom message flows or have specific conversation patterns.
    Most users should use query_repository() instead.

    ═══════════════════════════════════════════════════════════════════════════════════════════════
    🎯 GENIUS MODE DECISION TREE - When to Use This Tool
    ═══════════════════════════════════════════════════════════════════════════════════════════════
    
    USE query_repository_advanced() WHEN:
    ✅ You need to construct custom conversation histories
    ✅ You're building chatbots or complex conversation flows
    ✅ You want to replay specific message sequences
    ✅ You need exact control over message formatting
    ✅ You're integrating with external conversation systems
    ✅ You want to simulate multi-turn conversations programmatically
    
    DON'T USE query_repository_advanced() WHEN:
    ❌ Normal question-answer scenarios → use query_repository()
    ❌ Simple one-off queries → use query_simple()
    ❌ You don't need custom message control → use query_repository()
    ❌ You're just starting out → use query_simple() or query_repository()

    ═══════════════════════════════════════════════════════════════════════════════════════════════
    🚀 WORKING EXAMPLES - Copy & Paste Ready
    ═══════════════════════════════════════════════════════════════════════════════════════════════
    
    # Example 1: Custom Conversation History
    repositories = [{"remote": "github", "repository": "facebook/react", "branch": "main"}]
    
    messages = [
        {"id": "msg_1", "content": "How does useState work?", "role": "user"},
        {"id": "msg_2", "content": "useState is a React Hook that...", "role": "assistant"},
        {"id": "msg_3", "content": "How does it compare to class state?", "role": "user"}
    ]
    
    result = await query_repository_advanced(ctx, messages, repositories)
    
    # Example 2: Simulating Multi-Turn Conversation
    messages = [
        {"id": "user_1", "content": "Explain React hooks", "role": "user"},
        {"id": "assistant_1", "content": "React hooks are functions that...", "role": "assistant"},
        {"id": "user_2", "content": "Show me useEffect examples", "role": "user"},
        {"id": "assistant_2", "content": "Here are useEffect examples...", "role": "assistant"},
        {"id": "user_3", "content": "What about custom hooks?", "role": "user"}
    ]
    
    result = await query_repository_advanced(ctx, messages, repositories)
    
    # Example 3: Streaming Long Responses
    messages = [{"id": "complex_query", "content": "Analyze the entire React codebase architecture", "role": "user"}]
    
    async for chunk in await query_repository_advanced(ctx, messages, repositories, stream=True):
        # Process each chunk as it arrives
        chunk_data = json.loads(chunk)
        print(chunk_data)

    ═══════════════════════════════════════════════════════════════════════════════════════════════
    📋 COMPLETE MESSAGE FORMAT SPECIFICATION
    ═══════════════════════════════════════════════════════════════════════════════════════════════
    
    📋 messages parameter - EXACT REQUIRED FORMAT:
    ```python
    messages = [
        {
            "id": "unique_message_id",      # String: Unique identifier for this message
            "content": "message text here",   # String: The actual message content
            "role": "user"                   # String: "user" or "assistant"
        },
        {
            "id": "msg_2",
            "content": "Assistant response here",
            "role": "assistant"
        },
        {
            "id": "msg_3",
            "content": "Follow-up question",
            "role": "user"
        }
    ]
    ```
    
    📋 ROLE VALUES:
    • "user"      → Human questions or input
    • "assistant" → AI responses or system answers
    
    📋 ID REQUIREMENTS:
    • Must be unique within the message list
    • Can be any string ("msg_1", "user_question_1", "response_abc", etc.)
    • Used for internal tracking and debugging
    
    📋 CONTENT GUIDELINES:
    • Can be any length (short questions to long explanations)
    • Supports natural language, code snippets, technical terms
    • No special escaping needed for JSON-safe content

    ═══════════════════════════════════════════════════════════════════════════════════════════════
    📋 COMPLETE SESSION LIFECYCLE WITH ADVANCED CONTROL
    ═══════════════════════════════════════════════════════════════════════════════════════════════
    
    🔄 PATTERN 1: Building Custom Conversation
    ```python
    import json
    
    # Step 1: Start with initial message (no session_id)
    messages = [{"id": "q1", "content": "How does React rendering work?", "role": "user"}]
    result1 = await query_repository_advanced(ctx, messages, repositories)
    
    # Step 2: Extract session and build on conversation
    response1 = json.loads(result1)
    session_id = response1["_session_id"]
    
    # Step 3: Add assistant response to your messages
    messages.append({
        "id": "a1",
        "content": response1["message"],  # Use actual response
        "role": "assistant"
    })
    
    # Step 4: Add next user question
    messages.append({
        "id": "q2",
        "content": "What about the virtual DOM?",
        "role": "user"
    })
    
    # Step 5: Continue conversation with full history
    result2 = await query_repository_advanced(ctx, messages, repositories, session_id=session_id)
    ```
    
    🔄 PATTERN 2: Replaying Conversation
    ```python
    # Replay a previous conversation or simulate a specific scenario
    conversation_history = [
        {"id": "user_1", "content": "Explain hooks", "role": "user"},
        {"id": "bot_1", "content": "Hooks are functions that...", "role": "assistant"},
        {"id": "user_2", "content": "Show useState examples", "role": "user"},
        {"id": "bot_2", "content": "Here's useState usage...", "role": "assistant"},
        {"id": "user_3", "content": "What about useEffect?", "role": "user"}
    ]
    
    # Continue from this exact conversation state
    result = await query_repository_advanced(ctx, conversation_history, repositories)
    ```
    
    🔄 PATTERN 3: Integration with External Systems
    ```python
    # Convert from external chat format to Greptile format
    def convert_external_to_greptile(external_messages):
        greptile_messages = []
        for i, msg in enumerate(external_messages):
            greptile_messages.append({
                "id": f"ext_msg_{i}",
                "content": msg['text'],
                "role": "user" if msg['sender'] == 'human' else "assistant"
            })
        return greptile_messages
    
    # Use converted messages
    greptile_format = convert_external_to_greptile(external_chat_history)
    result = await query_repository_advanced(ctx, greptile_format, repositories)
    ```

    ═══════════════════════════════════════════════════════════════════════════════════════════════
    📋 COMPLETE PARAMETER REFERENCE
    ═══════════════════════════════════════════════════════════════════════════════════════════════
    
    💬 messages (List[Dict[str, str]]) - REQUIRED conversation history
    ┌─ Format: [{"id": "msg1", "content": "text", "role": "user/assistant"}]
    ┌─ Must include at least one message with role="user"
    ┌─ Last message typically should be "user" role for new question
    └─ Each message must have unique "id" within the list
    
    📂 repositories (list) - Same format as other query tools
    ┌─ [{"remote": "github", "repository": "owner/repo", "branch": "main"}]
    ┌─ Supports multiple repositories for comparison
    └─ All repos must be indexed first
    
    🔗 session_id (Optional[str]) - Session continuity
    ┌─ None: System generates new session (normal for first query)
    ┌─ "uuid-string": Use existing session (extract from previous response)
    └─ Critical for maintaining conversation context across calls
    
    🌊 stream (bool = False) - Response delivery mode
    ┌─ False: Complete response at once (easier to handle)
    ┌─ True: Stream chunks as they arrive (for very long responses)
    └─ Streaming returns AsyncGenerator, non-streaming returns string
    
    🧠 genius (bool = True) - Enhanced processing mode
    ┌─ True: Better accuracy and deeper analysis (recommended)
    ┌─ False: Faster processing with standard quality
    └─ Set to True for complex or important queries
    
    ⏱️ timeout (Optional[float]) - Query timeout control
    ┌─ None: Use system default timeout (recommended)
    ┌─ 60.0: Custom timeout in seconds for complex queries
    └─ Only needed for very large or complex analyses

    ═══════════════════════════════════════════════════════════════════════════════════════════════
    🚨 ERROR PREVENTION & ADVANCED TROUBLESHOOTING
    ═══════════════════════════════════════════════════════════════════════════════════════════════
    
    ❌ MISTAKE: Empty messages list
    ```python
    # WRONG - Will fail!
    messages = []
    result = await query_repository_advanced(ctx, messages, repositories)
    
    # CORRECT - At least one message required
    messages = [{"id": "q1", "content": "Your question here", "role": "user"}]
    result = await query_repository_advanced(ctx, messages, repositories)
    ```
    
    ❌ MISTAKE: Missing required message fields
    ```python
    # WRONG - Missing 'role' field
    messages = [{"id": "q1", "content": "How does this work?"}]
    
    # WRONG - Missing 'id' field  
    messages = [{"content": "How does this work?", "role": "user"}]
    
    # CORRECT - All fields present
    messages = [{"id": "q1", "content": "How does this work?", "role": "user"}]
    ```
    
    ❌ MISTAKE: Duplicate message IDs
    ```python
    # WRONG - Same ID used twice
    messages = [
        {"id": "msg1", "content": "First question", "role": "user"},
        {"id": "msg1", "content": "Second question", "role": "user"}  # Duplicate ID!
    ]
    
    # CORRECT - Unique IDs
    messages = [
        {"id": "msg1", "content": "First question", "role": "user"},
        {"id": "msg2", "content": "Second question", "role": "user"}
    ]
    ```
    
    ❌ MISTAKE: Invalid role values
    ```python
    # WRONG - Invalid role
    messages = [{"id": "q1", "content": "Question", "role": "human"}]
    
    # CORRECT - Valid roles only
    messages = [{"id": "q1", "content": "Question", "role": "user"}]
    # Valid roles: "user" or "assistant" only
    ```
    
    ❌ MISTAKE: Improper session management with custom messages
    ```python
    # WRONG - Building custom history but not managing session properly
    messages1 = [{"id": "q1", "content": "First question", "role": "user"}]
    result1 = await query_repository_advanced(ctx, messages1, repositories)
    
    messages2 = [
        {"id": "q1", "content": "First question", "role": "user"},
        {"id": "q2", "content": "Second question", "role": "user"}
    ]
    result2 = await query_repository_advanced(ctx, messages2, repositories)  # No session_id!
    
    # CORRECT - Extract and use session_id
    import json
    session_id = json.loads(result1)["_session_id"]
    result2 = await query_repository_advanced(ctx, messages2, repositories, session_id=session_id)
    ```

    ═══════════════════════════════════════════════════════════════════════════════════════════════
    🎯 ADVANCED USE CASES & PATTERNS
    ═══════════════════════════════════════════════════════════════════════════════════════════════
    
    🤖 PATTERN: Building Chatbot with Code Knowledge
    ```python
    class CodeChatbot:
        def __init__(self, repositories):
            self.repositories = repositories
            self.conversation_history = []
            self.session_id = None
        
        async def ask(self, user_question):
            # Add user message to history
            self.conversation_history.append({
                "id": f"user_{len(self.conversation_history)}",
                "content": user_question,
                "role": "user"
            })
            
            # Query with full history
            result = await query_repository_advanced(
                ctx, self.conversation_history, self.repositories, 
                session_id=self.session_id
            )
            
            # Extract response and session
            response_data = json.loads(result)
            if not self.session_id:
                self.session_id = response_data["_session_id"]
            
            # Add assistant response to history
            self.conversation_history.append({
                "id": f"assistant_{len(self.conversation_history)}",
                "content": response_data["message"],
                "role": "assistant"
            })
            
            return response_data["message"]
    
    # Usage
    bot = CodeChatbot(repositories)
    answer1 = await bot.ask("How does authentication work?")
    answer2 = await bot.ask("What about password reset?")  # Remembers context!
    ```
    
    🔄 PATTERN: Conversation Replay and Analysis
    ```python
    # Replay a specific conversation scenario for testing
    test_conversation = [
        {"id": "test_q1", "content": "Explain React hooks", "role": "user"},
        {"id": "test_a1", "content": "React hooks are...", "role": "assistant"},
        {"id": "test_q2", "content": "Show useState example", "role": "user"},
        {"id": "test_a2", "content": "Here's useState...", "role": "assistant"},
        {"id": "test_q3", "content": "Now explain useEffect", "role": "user"}
    ]
    
    # Continue from this exact conversation state
    result = await query_repository_advanced(ctx, test_conversation, repositories)
    
    # Useful for:
    # - Testing specific conversation flows
    # - Reproducing user issues
    # - Training scenarios
    # - Quality assurance
    ```
    
    🔍 PATTERN: Complex Multi-Step Analysis
    ```python
    # Perform complex analysis with precise control over each step
    analysis_steps = [
        {"id": "step1", "content": "Analyze the overall architecture", "role": "user"},
        {"id": "response1", "content": "[Previous AI analysis]", "role": "assistant"},
        {"id": "step2", "content": "Focus on the authentication module", "role": "user"},
        {"id": "response2", "content": "[Previous auth analysis]", "role": "assistant"},
        {"id": "step3", "content": "Compare with industry best practices", "role": "user"}
    ]
    
    result = await query_repository_advanced(ctx, analysis_steps, repositories, stream=True)
    ```

    ═══════════════════════════════════════════════════════════════════════════════════════════════
    🎯 GENIUS MODE DEFAULTS & STREAMING
    ═══════════════════════════════════════════════════════════════════════════════════════════════
    
    🧠 SMART DEFAULTS:
    • genius=True     → Maximum accuracy for complex conversations
    • stream=False    → Complete responses (easier for message history management)
    • session_id=None → Let system generate proper session tracking
    • timeout=None    → Appropriate timeout for complex queries
    
    🌊 STREAMING CONSIDERATIONS:
    • Use stream=True for very long analyses or large codebases
    • Streaming complicates message history management
    • Each chunk needs to be processed individually
    • Final complete response must be reconstructed for history
    
    ```python
    # Example: Handling streaming with message history
    async def stream_with_history(messages, repositories, session_id=None):
        full_response = ""
        async for chunk in await query_repository_advanced(
            ctx, messages, repositories, session_id=session_id, stream=True
        ):
            chunk_data = json.loads(chunk)
            if "content" in chunk_data:
                full_response += chunk_data["content"]
            # Process chunk immediately if needed
            yield chunk_data
        
        # Add complete response to message history
        messages.append({
            "id": f"assistant_{len(messages)}",
            "content": full_response,
            "role": "assistant"
        })
    ```

    Args:
        ctx: MCP context (provided automatically by the MCP framework)
        messages: Complete conversation history in Greptile API format
        repositories: List of repositories to query (same format as other tools)
        session_id: Session ID for continuity (extract from previous response)
        stream: Enable streaming for very long responses (default: False)
        genius: Enhanced accuracy mode for better results (default: True)
        timeout: Maximum seconds to wait for response (default: uses system default)

    Returns:
        For stream=False: JSON string with answer, source references, and _session_id
        For stream=True: AsyncGenerator yielding response chunks as JSON strings
    
    Raises:
        Exception: If messages format invalid, repositories not indexed, or API errors
        
    Note: This is the most advanced tool - use query_repository() for normal usage
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
    🔥 ADVANCED: Query multiple repositories simultaneously for comprehensive cross-codebase analysis.

    GENIUS MODE DEFAULT: Complex multi-repo analysis requires maximum accuracy, so genius=True by default.
    This tool excels at synthesizing information across multiple codebases to provide unified insights.

    🎯 PERFECT FOR:
    • Microservices Architecture Analysis: "How do authentication flows work across all our services?"
    • Technology Stack Migration: "Compare authentication in our old PHP app vs new Node.js services"
    • Framework Evaluation: "How do React, Vue, and Angular handle component state?"
    • Design Pattern Research: "Show me different implementations of the Observer pattern"
    • Cross-team Code Standards: "How do different teams handle error logging?"

    📋 COMPLETE WORKFLOW - MICROSERVICES ANALYSIS:
    ```python
    # Step 1: Index all your microservices
    await index_repository(ctx, "github", "company/auth-service", "main")
    await index_repository(ctx, "github", "company/user-service", "main")
    await index_repository(ctx, "github", "company/payment-service", "main")
    await index_repository(ctx, "github", "company/notification-service", "main")

    # Step 2: Define your service repositories
    microservices = [
        {"remote": "github", "repository": "company/auth-service", "branch": "main"},
        {"remote": "github", "repository": "company/user-service", "branch": "main"},
        {"remote": "github", "repository": "company/payment-service", "branch": "main"},
        {"remote": "github", "repository": "company/notification-service", "branch": "main"}
    ]

    # Step 3: Comprehensive architecture analysis
    analysis = await query_multiple_repositories(ctx,
        "Analyze the overall architecture: How do these services communicate? 
         What patterns are used for data consistency? How is authentication handled?",
        microservices
    )

    # Step 4: Security audit across services
    security = await query_multiple_repositories(ctx,
        "Audit security practices: How do these services handle authentication tokens? 
         What validation patterns are used? Are there any security inconsistencies?",
        microservices
    )
    ```

    📋 COMPLETE WORKFLOW - FRAMEWORK COMPARISON:
    ```python
    # Compare modern web frameworks
    frameworks = [
        {"remote": "github", "repository": "facebook/react", "branch": "main"},
        {"remote": "github", "repository": "vuejs/core", "branch": "main"},
        {"remote": "github", "repository": "angular/angular", "branch": "main"},
        {"remote": "github", "repository": "sveltejs/svelte", "branch": "master"}
    ]

    # Comprehensive framework analysis
    comparison = await query_multiple_repositories(ctx,
        "Compare these frameworks: How does each handle component lifecycle? 
         What are the performance optimization strategies? How do they manage state?",
        frameworks
    )
    ```

    📋 COMPLETE WORKFLOW - MIGRATION ANALYSIS:
    ```python
    # Legacy system migration planning
    migration_repos = [
        {"remote": "github", "repository": "company/legacy-monolith", "branch": "main"},
        {"remote": "github", "repository": "company/new-api-gateway", "branch": "main"},
        {"remote": "github", "repository": "company/shared-components", "branch": "main"}
    ]

    migration_plan = await query_multiple_repositories(ctx,
        "Create a migration strategy: What functionality from the legacy system 
         needs to be replicated? How can we leverage the new architecture? 
         What are the integration points?",
        migration_repos
    )
    ```

    🔧 REPOSITORY VALIDATION:
    All repositories MUST be pre-indexed and include:
    • remote: "github" or "gitlab"
    • repository: "owner/repo" format (e.g., "facebook/react")
    • branch: specific branch name (e.g., "main", "master", "develop")

    🚨 VALIDATION ERRORS TO AVOID:
    ❌ Missing required fields: {"repository": "facebook/react"} # Missing remote and branch
    ❌ Wrong format: {"remote": "github", "repository": "https://github.com/facebook/react"}
    ✅ Correct format: {"remote": "github", "repository": "facebook/react", "branch": "main"}

    ⚡ PERFORMANCE CONSIDERATIONS:
    • Genius Mode Impact: With genius=True, queries are more accurate but take 15-30% longer
    • Repository Limit: Optimal performance with 2-6 repositories; 10+ may hit rate limits
    • Streaming Mode: Use stream=True for queries that might take >30 seconds
    • Timeout Strategy: Set timeout=120 for complex multi-repo analysis

    🎯 QUERY OPTIMIZATION PATTERNS:
    
    SPECIFIC QUERIES (Better):
    "How do these frameworks handle component state management and lifecycle hooks?"
    "Compare the authentication middleware patterns used in these Node.js frameworks"
    "What are the different error handling strategies across these microservices?"
    
    VAGUE QUERIES (Avoid):
    "How do these work?"
    "Tell me about these repositories"
    "What's different?"

    Args:
        ctx: MCP server provided context (automatically provided)
        query: Specific natural language query about the codebases
               Best practices: Be specific, mention what you want to compare/analyze
        repositories: List of 2-10 repositories for cross-analysis
                     Format: [{"remote": "github", "repository": "owner/repo", "branch": "main"}]
                     All repositories must be pre-indexed with index_repository()
        genius: Enhanced accuracy mode (default: True)
                Recommended: Always True for multi-repo analysis requiring accuracy
        stream: Enable real-time streaming for long queries (default: False)
                Use True for complex analysis that might take >30 seconds
        timeout: Maximum seconds to wait (default: None)
                Recommended: 120-300 seconds for complex multi-repo queries

    Returns:
        For stream=False: Comprehensive JSON analysis with cross-repository insights
        For stream=True: AsyncGenerator yielding real-time analysis chunks
        
        Response includes:
        • Unified analysis across all repositories
        • Specific code examples from each repository
        • Comparative insights and patterns
        • Best practice recommendations
        • Implementation differences and similarities

    🔄 FOLLOW-UP PATTERNS:
    Extract session_id from response for detailed follow-up questions:
    ```python
    import json
    response = json.loads(await query_multiple_repositories(ctx, query, repos))
    session_id = response["_session_id"]
    
    # Follow-up with same context
    followup = await query_repository(ctx, 
        "Can you elaborate on the performance differences?", 
        repos, 
        session_id=session_id
    )
    ```

    💡 PRO TIPS:
    1. Index all repositories before querying for best results
    2. Use specific queries mentioning what aspects to compare
    3. Include both your code and reference implementations for learning
    4. Combine related services/frameworks for comprehensive analysis
    5. Use streaming for complex queries involving 5+ repositories
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
    🔥 EXPERT-LEVEL: Deep comparative analysis across multiple repositories for architectural decisions.

    GENIUS MODE ENFORCED: Complex comparisons demand maximum accuracy - genius=True is locked as default.
    This tool specializes in side-by-side analysis, pattern identification, and architectural comparison.

    🎯 SPECIALIZED COMPARISON USE CASES:

    🏗️ FRAMEWORK ARCHITECTURE COMPARISON:
    "Compare the component architecture and rendering strategies between React, Vue, and Angular"
    "How do Express.js vs Koa.js vs Fastify handle middleware and request processing?"
    "Compare state management patterns: Redux vs Vuex vs NgRx vs Zustand"

    🔐 SECURITY PATTERN ANALYSIS:
    "Compare authentication implementations: OAuth flows, JWT handling, session management"
    "How do different frameworks handle CSRF protection and input validation?"
    "Compare API security: rate limiting, CORS, and request sanitization approaches"

    ⚡ PERFORMANCE OPTIMIZATION COMPARISON:
    "Compare bundle splitting and lazy loading strategies across meta-frameworks"
    "How do different ORMs handle connection pooling and query optimization?"
    "Compare caching strategies: Redis vs Memcached vs in-memory solutions"

    📋 COMPLETE WORKFLOW - FRAMEWORK SELECTION:
    ```python
    # Step 1: Index candidate frameworks
    await index_repository(ctx, "github", "expressjs/express", "master")
    await index_repository(ctx, "github", "koajs/koa", "master")
    await index_repository(ctx, "github", "fastify/fastify", "main")
    await index_repository(ctx, "github", "hapijs/hapi", "master")

    # Step 2: Define comparison repositories
    node_frameworks = [
        {"remote": "github", "repository": "expressjs/express", "branch": "master"},
        {"remote": "github", "repository": "koajs/koa", "branch": "master"},
        {"remote": "github", "repository": "fastify/fastify", "branch": "main"},
        {"remote": "github", "repository": "hapijs/hapi", "branch": "master"}
    ]

    # Step 3: Comprehensive architecture comparison
    architecture = await compare_repositories(ctx,
        "Compare the middleware architecture, request handling pipeline, 
         and plugin systems across these Node.js frameworks",
        node_frameworks
    )

    # Step 4: Performance and ecosystem comparison
    performance = await compare_repositories(ctx,
        "Compare performance characteristics, memory usage patterns, 
         and ecosystem maturity across these frameworks",
        node_frameworks
    )

    # Step 5: Developer experience comparison
    dev_experience = await compare_repositories(ctx,
        "Compare developer experience: API design, TypeScript support, 
         testing frameworks, and learning curve",
        node_frameworks
    )
    ```

    📋 COMPLETE WORKFLOW - MIGRATION DECISION:
    ```python
    # Current vs Target technology comparison
    migration_comparison = [
        {"remote": "github", "repository": "company/legacy-rails-app", "branch": "main"},
        {"remote": "github", "repository": "vercel/next.js", "branch": "canary"},
        {"remote": "github", "repository": "remix-run/remix", "branch": "main"}
    ]

    migration_analysis = await compare_repositories(ctx,
        "Compare our current Rails architecture with Next.js and Remix: 
         What are the migration complexities? How do routing, data fetching, 
         and rendering strategies differ? What are the performance implications?",
        migration_comparison
    )
    ```

    📋 COMPLETE WORKFLOW - COMPETITIVE ANALYSIS:
    ```python
    # Analyze competitor implementations
    competitive_repos = [
        {"remote": "github", "repository": "company/our-product", "branch": "main"},
        {"remote": "github", "repository": "competitor1/their-product", "branch": "main"},
        {"remote": "github", "repository": "competitor2/alternative", "branch": "main"}
    ]

    competitive_analysis = await compare_repositories(ctx,
        "Compare our architecture with competitors: What are their advantages? 
         How do they solve similar problems? What can we learn and improve?",
        competitive_repos
    )
    ```

    🔧 COMPARISON QUERY OPTIMIZATION:
    
    HIGH-VALUE QUERIES (Recommended):
    ✅ "Compare error handling: How do these frameworks catch, log, and respond to errors?"
    ✅ "Analyze authentication flows: What are the security trade-offs and implementation differences?"
    ✅ "Compare testing strategies: Unit testing, integration testing, and mocking approaches"
    ✅ "Evaluate API design: REST vs GraphQL implementation patterns and best practices"
    
    LOW-VALUE QUERIES (Avoid):
    ❌ "Compare these repositories" (too vague)
    ❌ "What's different?" (no specific focus)
    ❌ "Tell me about these" (not comparative)

    🎯 COMPARISON DIMENSIONS TO EXPLORE:
    
    🏛️ ARCHITECTURAL PATTERNS:
    • "Compare dependency injection patterns and IoC container implementations"
    • "How do these frameworks handle modular architecture and plugin systems?"
    • "Compare microservices communication patterns: events vs direct calls"
    
    🔒 SECURITY APPROACHES:
    • "Compare OWASP Top 10 mitigation strategies across these applications"
    • "How do these frameworks handle input validation and sanitization?"
    • "Compare session management and CSRF protection implementations"
    
    ⚡ PERFORMANCE STRATEGIES:
    • "Compare caching layers: in-memory, distributed, and CDN strategies"
    • "How do these ORMs handle N+1 query problems and optimization?"
    • "Compare bundle optimization and code splitting approaches"
    
    🧪 TESTING METHODOLOGIES:
    • "Compare testing pyramid implementations: unit, integration, e2e"
    • "How do these projects handle mocking, fixtures, and test data?"
    • "Compare CI/CD pipeline testing strategies and quality gates"

    📊 RESPONSE STRUCTURE:
    The comparison includes:
    • Side-by-side implementation analysis
    • Pros and cons of each approach
    • Code examples from each repository
    • Performance and maintainability implications
    • Recommendation matrix based on use cases
    • Migration complexity assessment

    🚨 REPOSITORY VALIDATION:
    Ensure all repositories:
    ✅ Are pre-indexed with index_repository()
    ✅ Use correct format: {"remote": "github", "repository": "owner/repo", "branch": "main"}
    ✅ Represent comparable technologies or approaches
    ✅ Are accessible and contain relevant code

    ⚡ PERFORMANCE GUIDELINES:
    • Optimal: 2-4 repositories for detailed comparison
    • Maximum: 6-8 repositories before analysis becomes shallow
    • Processing time: 30-90 seconds for complex comparisons
    • Memory usage: Scales linearly with repository count

    Args:
        ctx: MCP server provided context (automatically provided)
        comparison_query: Specific comparative question focusing on particular aspects
                         Best practice: Mention specific features, patterns, or strategies to compare
                         Examples: "Compare authentication flows", "Analyze error handling patterns"
        repositories: List of 2-8 repositories to compare
                     All must be pre-indexed and represent comparable technologies
                     Format: [{"remote": "github", "repository": "owner/repo", "branch": "main"}]
        genius: Enhanced accuracy mode (locked to True for comparison quality)
                Ensures deep analysis and accurate comparative insights

    Returns:
        Comprehensive JSON comparative analysis including:
        • Detailed side-by-side comparison
        • Implementation differences and similarities
        • Pros/cons analysis for each approach
        • Specific code examples from each repository
        • Performance and scalability implications
        • Recommendation matrix for different use cases
        • Migration complexity assessment

    💡 EXPERT TIPS:
    1. Focus on specific aspects rather than general comparisons
    2. Include both your code and industry standards for benchmarking
    3. Compare similar-sized projects for meaningful insights
    4. Use results to inform architectural decisions and migrations
    5. Follow up with specific implementation questions using session_id
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
    🔍 PRECISION SEARCH: Find specific patterns, functions, or implementations across multiple codebases.

    GENIUS MODE DEFAULT: Pattern detection across repositories requires enhanced search intelligence.
    This tool excels at finding needle-in-haystack code patterns without generating full explanations.

    🎯 SPECIALIZED SEARCH SCENARIOS:

    🔧 FUNCTION & API DISCOVERY:
    "WebSocket connection handling" across real-time communication libraries
    "rate limiting implementation" across API frameworks
    "JWT token validation" across authentication systems
    "database connection pooling" across ORM libraries

    🏗️ ARCHITECTURAL PATTERN HUNTING:
    "Observer pattern implementation" across design pattern examples
    "Factory method usage" across framework codebases
    "Singleton pattern variations" across configuration management
    "Strategy pattern examples" across payment processing systems

    🔐 SECURITY IMPLEMENTATION SEARCH:
    "CSRF protection mechanisms" across web frameworks
    "input sanitization functions" across security libraries
    "password hashing algorithms" across authentication systems
    "API key validation" across service integrations

    📋 COMPLETE WORKFLOW - SECURITY AUDIT ACROSS SERVICES:
    ```python
    # Step 1: Index all security-relevant repositories
    await index_repository(ctx, "github", "company/auth-service", "main")
    await index_repository(ctx, "github", "company/api-gateway", "main")
    await index_repository(ctx, "github", "company/user-service", "main")
    await index_repository(ctx, "github", "owasp/cheatsheets", "master")

    # Step 2: Define security audit scope
    security_repos = [
        {"remote": "github", "repository": "company/auth-service", "branch": "main"},
        {"remote": "github", "repository": "company/api-gateway", "branch": "main"},
        {"remote": "github", "repository": "company/user-service", "branch": "main"},
        {"remote": "github", "repository": "owasp/cheatsheets", "branch": "master"}
    ]

    # Step 3: Search for authentication patterns
    auth_patterns = await search_multiple_repositories(ctx,
        "JWT token validation", security_repos, "*.js,*.ts,*.py"
    )

    # Step 4: Search for input validation
    validation_patterns = await search_multiple_repositories(ctx,
        "input sanitization and validation", security_repos, "*.js,*.ts,*.py"
    )

    # Step 5: Search for rate limiting
    rate_limiting = await search_multiple_repositories(ctx,
        "rate limiting middleware", security_repos
    )
    ```

    📋 COMPLETE WORKFLOW - DESIGN PATTERN RESEARCH:
    ```python
    # Research design patterns across industry examples
    pattern_repos = [
        {"remote": "github", "repository": "iluwatar/java-design-patterns", "branch": "master"},
        {"remote": "github", "repository": "faif/python-patterns", "branch": "master"},
        {"remote": "github", "repository": "sohamkamani/javascript-design-patterns", "branch": "master"},
        {"remote": "github", "repository": "company/our-codebase", "branch": "main"}
    ]

    # Search for specific patterns
    observer_pattern = await search_multiple_repositories(ctx,
        "Observer pattern implementation", pattern_repos
    )

    factory_pattern = await search_multiple_repositories(ctx,
        "Factory method pattern", pattern_repos
    )

    strategy_pattern = await search_multiple_repositories(ctx,
        "Strategy pattern examples", pattern_repos
    )
    ```

    📋 COMPLETE WORKFLOW - API INTEGRATION RESEARCH:
    ```python
    # Find API integration patterns across services
    integration_repos = [
        {"remote": "github", "repository": "stripe/stripe-node", "branch": "master"},
        {"remote": "github", "repository": "paypal/paypal-js", "branch": "main"},
        {"remote": "github", "repository": "square/square-nodejs-sdk", "branch": "master"},
        {"remote": "github", "repository": "company/payment-service", "branch": "main"}
    ]

    # Search for payment processing patterns
    payment_patterns = await search_multiple_repositories(ctx,
        "payment processing and webhook handling", integration_repos, "*.js,*.ts"
    )

    # Search for error handling in payments
    error_handling = await search_multiple_repositories(ctx,
        "payment error handling and retries", integration_repos
    )
    ```

    🎯 FILE PATTERN OPTIMIZATION:
    
    LANGUAGE-SPECIFIC PATTERNS:
    • JavaScript/TypeScript: "*.js,*.ts,*.jsx,*.tsx"
    • Python: "*.py,*.pyx,*.pyi"
    • Java: "*.java,*.kt,*.scala"
    • C/C++: "*.c,*.cpp,*.cc,*.h,*.hpp"
    • Web: "*.html,*.css,*.scss,*.vue"
    • Config: "*.json,*.yaml,*.yml,*.toml"
    
    FUNCTIONAL PATTERNS:
    • Tests: "*test*,*spec*,test/**,tests/**"
    • Documentation: "*.md,*.rst,*.txt,docs/**"
    • Configuration: "*config*,*.env*,*.ini"
    • Database: "*migration*,*schema*,*.sql"

    🔍 SEARCH TERM OPTIMIZATION:
    
    HIGH-PRECISION TERMS (Recommended):
    ✅ "async/await error handling patterns"
    ✅ "Redis connection pooling implementation"
    ✅ "GraphQL resolver authentication middleware"
    ✅ "WebSocket message queuing strategies"
    
    BROAD TERMS (Use with file patterns):
    ⚠️ "authentication" → Use with "*.js,*.ts" to narrow scope
    ⚠️ "database" → Use with "*model*,*schema*" for relevance
    ⚠️ "testing" → Use with "*test*,*spec*" for precision

    📊 RESULT INTERPRETATION:
    Search results include:
    • File paths and locations where patterns are found
    • Relevance scores for each match
    • Code snippets showing pattern usage
    • Repository-specific context for each finding
    • Aggregated pattern analysis across all repositories

    🚨 COMMON SEARCH PITFALLS:
    ❌ Too broad: "error" (returns thousands of matches)
    ❌ Too specific: "very_specific_function_name_12345" (no matches)
    ❌ Wrong file pattern: "*.js" when searching Python repos
    ❌ Typos: "authntication" instead of "authentication"
    
    ✅ OPTIMIZATION STRATEGIES:
    ✅ Use 2-4 word descriptive phrases
    ✅ Include context: "middleware authentication", "async error handling"
    ✅ Match file patterns to search repositories
    ✅ Combine multiple searches for comprehensive coverage

    ⚡ PERFORMANCE CONSIDERATIONS:
    • Search Speed: 5-15 seconds depending on repository size
    • Result Limit: Top 50 most relevant matches per repository
    • File Pattern Impact: Reduces search scope, improves speed
    • Repository Count: Linear scaling, optimal with 2-6 repos

    🔄 FOLLOW-UP WORKFLOW:
    Use search results to guide detailed analysis:
    ```python
    # 1. Search for patterns
    search_results = await search_multiple_repositories(ctx, 
        "authentication middleware", repos, "*.js,*.ts"
    )
    
    # 2. Extract specific findings and ask detailed questions
    detailed_analysis = await query_multiple_repositories(ctx,
        "Explain the authentication middleware implementations found in the search. 
         How do they differ in approach and security?",
        repos
    )
    ```

    Args:
        ctx: MCP server provided context (automatically provided)
        search_term: Specific term, pattern, or concept to find across repositories
                    Best practice: Use 2-4 descriptive words with context
                    Examples: "JWT token validation", "async error handling", "Redis caching"
        repositories: List of 2-10 pre-indexed repositories to search
                     Format: [{"remote": "github", "repository": "owner/repo", "branch": "main"}]
                     All repositories must be indexed with index_repository() first
        file_pattern: Optional file pattern to focus search scope (default: None)
                     Examples: "*.js,*.ts", "*.py", "*test*", "*config*"
                     Significantly improves search precision and speed
        genius: Enhanced pattern recognition mode (default: True)
                Recommended: Always True for accurate cross-repository pattern detection

    Returns:
        JSON with comprehensive search results including:
        • Matched files and locations across all repositories
        • Relevance scores for each match
        • Code snippets showing pattern usage in context
        • Repository-specific analysis of found patterns
        • Aggregated insights across all searched codebases
        • File path and line number references for easy navigation

    💡 EXPERT SEARCH STRATEGIES:
    1. Start broad, then narrow with file patterns
    2. Search industry examples alongside your code for learning
    3. Use multiple related searches to build comprehensive understanding
    4. Combine search results with query_multiple_repositories for deep analysis
    5. Save successful search terms for future reference and team sharing
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
