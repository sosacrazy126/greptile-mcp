# Greptile MCP Agent Usage Guide

This guide provides clear instructions on how to use the Greptile MCP tools with AI agents. The Greptile MCP server exposes several tools that allow agents to interact with the Greptile API for code search and querying.

## Available Tools

The Greptile MCP server provides the following tools:

### index_repository

Indexes a repository for code search and querying. This must be done before querying or searching.

```json
{
  "remote": "github",
  "repository": "owner/repo",
  "branch": "main",
  "reload": false,
  "notify": false
}
```

**Parameters:**
- `remote`: The repository host, either "github" or "gitlab"
- `repository`: The repository in owner/repo format
- `branch`: The branch to index
- `reload` (optional): Whether to force reprocessing, defaults to false
- `notify` (optional): Whether to send an email notification, defaults to false

**Response Example:**
```json
{
  "status": "queued",
  "id": "github:main:owner/repo",
  "message": "Repository indexing queued"
}
```

### query_repository

Queries repositories to get an answer with code references.

```json
{
  "query": "How does the authentication system work?",
  "repositories": [
    {
      "remote": "github",
      "repository": "owner/repo",
      "branch": "main"
    }
  ],
  "session_id": null,
  "stream": false,
  "genius": true
}
```

**Parameters:**
- `query`: The natural language query about the codebase
- `repositories`: List of repositories to query, each with format shown above
- `session_id` (optional): Session ID for continuing a conversation
- `stream` (optional): Whether to stream the response, defaults to false
- `genius` (optional): Whether to use enhanced query capabilities, defaults to true

**Response Example:**
```json
{
  "answer": "The authentication system uses JWT (JSON Web Tokens) for user authentication...",
  "references": [
    {
      "file": "src/auth.py",
      "snippet": "def authenticate(user, password):\n    # Verify credentials\n    if verify_password(user, password):\n        return generate_token(user)",
      "start_line": 15,
      "end_line": 18
    }
  ],
  "confidence": 0.95
}
```

### search_repository

Searches repositories for relevant files without generating a full answer.

```json
{
  "query": "Find files related to authentication",
  "repositories": [
    {
      "remote": "github",
      "repository": "owner/repo",
      "branch": "main"
    }
  ],
  "session_id": null,
  "genius": true
}
```

**Parameters:**
- `query`: The natural language query about the codebase
- `repositories`: List of repositories to search
- `session_id` (optional): Session ID for continuing a conversation
- `genius` (optional): Whether to use enhanced search capabilities, defaults to true

**Response Example:**
```json
{
  "files": [
    {
      "path": "src/auth.py",
      "score": 0.95,
      "matches": [
        {
          "line": 15,
          "content": "def authenticate(user, password):"
        }
      ]
    },
    {
      "path": "src/middleware/jwt.py",
      "score": 0.85,
      "matches": [
        {
          "line": 22,
          "content": "def verify_token(token):"
        }
      ]
    }
  ]
}
```

### get_repository_info

Gets information about an indexed repository.

```json
{
  "remote": "github",
  "repository": "owner/repo",
  "branch": "main"
}
```

**Parameters:**
- `remote`: The repository host, either "github" or "gitlab"
- `repository`: The repository in owner/repo format
- `branch`: The branch that was indexed

**Response Example:**
```json
{
  "id": "github:main:owner/repo",
  "status": "completed",
  "last_indexed": "2023-01-01T00:00:00Z",
  "branch": "main"
}
```

## Common Workflows

### Typical Usage Pattern

1. **Index a repository:**
   ```
   index_repository(remote="github", repository="owner/repo", branch="main")
   ```

2. **Check indexing status:**
   ```
   get_repository_info(remote="github", repository="owner/repo", branch="main")
   ```

3. **Query the repository:**
   ```
   query_repository(
       query="How does error handling work in this codebase?",
       repositories=[{"remote": "github", "repository": "owner/repo", "branch": "main"}]
   )
   ```

### Managing Session Context

Session IDs are crucial for maintaining conversation context across multiple queries:

1. **Initial query** - Generate and store a unique session ID:
   ```
   session_id = "session-" + generate_unique_id()
   
   result = query_repository(
       query="How does error handling work in this codebase?",
       repositories=[{"remote": "github", "repository": "owner/repo", "branch": "main"}],
       session_id=session_id
   )
   ```

2. **Follow-up queries** - Reuse the same session ID:
   ```
   # Use the SAME session_id from the initial query
   result = query_repository(
       query="Can you show me more examples of this pattern?",
       repositories=[{"remote": "github", "repository": "owner/repo", "branch": "main"}],
       session_id=session_id
   )
   ```

> **Important**: Session IDs are NOT automatically generated after indexing a repository. You must generate, store, and reuse the same session ID throughout a conversation to maintain context.

### For Smithery Integration

When integrating with Smithery:

1. Agents should generate and store session IDs as part of their state
2. The same session ID must be passed for all related queries in a conversation
3. If a new conversation starts, generate a new session ID
4. Session IDs should be unique strings (UUIDs or similar format recommended)

### Finding Specific Files

If you want to find specific files without generating a complete answer:

```
search_repository(
    query="Find files related to database connections",
    repositories=[{"remote": "github", "repository": "owner/repo", "branch": "main"}]
)
```

## Error Handling

All tools return error messages as strings if something goes wrong. For example:

```
"Error indexing repository: Repository not found"
```

## Tips for Effective Usage

1. Always index a repository before querying or searching it
2. Use specific, clear queries for better results
3. Check repository status with `get_repository_info` if indexing is taking time
4. For complex questions, use `query_repository` with `genius=true`
5. For finding specific files, use `search_repository`
6. The system handles URL encoding of repository identifiers internally - you can directly use the standard `owner/repo` format without worrying about special character encoding

## Important Implementation Notes

### Repository ID Encoding

Repository IDs are formatted as `remote:branch:owner/repo` and require proper URL encoding when used in API requests. The MCP tools handle this encoding automatically, so you don't need to worry about it when using the tools.

If you're accessing the Greptile API directly without using these tools, make sure to:

1. Construct the repository ID in the correct format: `remote:branch:owner/repo`
2. Fully URL-encode the entire ID, including any slashes (`/`)
3. Use `urllib.parse.quote_plus(repository_id, safe='')` in Python or equivalent in other languages

Example:
```python
# Correct way to encode repository IDs
import urllib.parse
repository_id = "github:main:fastapi/fastapi"
encoded_id = urllib.parse.quote_plus(repository_id, safe='')
url = f"https://api.greptile.com/v2/repositories/{encoded_id}"
```

### Server Initialization and Health Checks

The Greptile MCP server performs initialization steps when it starts up. During this initialization phase, requests to the tools may return an initialization status message rather than executing the requested operation.

**Handling Initialization State:**

1. **Initialization Response**: If you call a tool while the server is still initializing, you'll receive:
   ```json
   {
     "error": "Server initialization is not complete. Please try again in a moment.",
     "status": "initializing"
   }
   ```

2. **Best Practices**:
   - Wait a few seconds after server startup before making tool calls
   - Implement retry logic with exponential backoff if initialization errors occur
   - If a tool returns an initialization error, wait briefly and try again

## Example Session

Here's an example of a complete session with proper session ID management:

```
// Index a repository
index_repository(remote="github", repository="fastapi/fastapi", branch="master")

// Wait for indexing to complete
get_repository_info(remote="github", repository="fastapi/fastapi", branch="master")

// Generate a session ID for this conversation
const session_id = "session-" + Date.now() + "-" + Math.random().toString(36).substring(2);

// Initial query with the session ID
query_repository(
    query="How does dependency injection work in FastAPI?",
    repositories=[{"remote": "github", "repository": "fastapi/fastapi", "branch": "master"}],
    session_id=session_id
)

// Follow-up query using the SAME session ID
query_repository(
    query="Can you show me an example of using Depends with a database?",
    repositories=[{"remote": "github", "repository": "fastapi/fastapi", "branch": "master"}],
    session_id=session_id
)
```

This pattern ensures that conversation context is maintained between related queries. 