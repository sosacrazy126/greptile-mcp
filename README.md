# Greptile MCP Server

An MCP (Model Context Protocol) server implementation that integrates with the Greptile API to provide code search and querying capabilities to AI agents.

[![smithery badge](https://smithery.ai/badge/@sosacrazy126/greptile-mcp)](https://smithery.ai/server/@sosacrazy126/greptile-mcp)

## Features

The server provides four essential Greptile tools that enable AI agents to interact with codebases:

1. **`index_repository`**: Index a repository for code search and querying.
   - Process a repository to make it searchable
   - Update existing indexes when repositories change
   - Configure notification preferences

2. **`query_repository`**: Query repositories to get answers with code references.
   - Ask natural language questions about the codebase
   - Get detailed answers that reference specific code locations
   - Support for conversation history with session IDs

3. **`search_repository`**: Search repositories for relevant files without generating a full answer.
   - Find files related to specific concepts or features
   - Get contextual matches ranked by relevance
   - Faster than full queries when only file locations are needed

4. **`get_repository_info`**: Get information about an indexed repository.
   - Check indexing status and progress
   - Verify which repositories are available for querying
   - Get metadata about indexed repositories

## Smithery Deployment

The Greptile MCP server supports deployment via Smithery. A `smithery.yaml` configuration file is included in the project root.

### Smithery Configuration

The Smithery configuration is defined in `smithery.yaml` and supports the following options:

```yaml
build:
  dockerfile: Dockerfile

startCommand:
  type: stdio
  configSchema:
    type: object
    required:
      - greptileApiKey
      - githubToken
    properties:
      greptileApiKey:
        type: string
        description: "API key for accessing the Greptile API"
      githubToken:
        type: string
        description: "GitHub Personal Access Token for repository access"
      host:
        type: string
        description: "Host to bind to when using SSE transport"
        default: "0.0.0.0"
      port:
        type: string
        description: "Port to listen on when using SSE transport"
        default: "8050"
```

### Using with Smithery

To deploy using Smithery:

1. Install Smithery: `npm install -g smithery`
2. Deploy the server: `smithery deploy`
3. Configure your Smithery client with the required API keys

## Prerequisites

- **Python 3.12+**
- **Greptile API Key** (from [https://app.greptile.com/settings/api](https://app.greptile.com/settings/api))
- **GitHub or GitLab Personal Access Token (PAT)** with `repo` (or equivalent read) permissions for the repositories you intend to index
- **Docker** (recommended for deployment)

### Required Python Packages

- `fastmcp` - MCP server implementation
- `httpx` - Async HTTP client
- `python-dotenv` - Environment variable management
- `uvicorn` - ASGI server for SSE transport

## Installation

### Installing via Smithery

To install Greptile Code Search Server for Claude automatically via [Smithery](https://smithery.ai/server/@sosacrazy126/greptile-mcp):

```bash
npx -y @smithery/cli install @sosacrazy126/greptile-mcp --client claude
```

### Using pip

1. Clone this repository:
   ```bash
   git clone https://github.com/sosacrazy126/greptile-mcp.git
   cd greptile-mcp
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set your environment variables:
   ```bash
   export GREPTILE_API_KEY=your_api_key_here
   export GITHUB_TOKEN=your_github_token_here
   ```

### Using Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/sosacrazy126/greptile-mcp.git
   cd greptile-mcp
   ```

2. Build the Docker image:
   ```bash
   docker build -t greptile-mcp .
   ```

## Running the Server

### Using pip

```bash
python -m src.main
```

### Using Docker

```bash
docker run --rm -e GREPTILE_API_KEY=your_key -e GITHUB_TOKEN=your_token -p 8050:8050 greptile-mcp
```

## Integration with MCP Clients

Configure your MCP client to connect to the server:

```json
{
  "mcpServers": {
    "greptile": {
      "transport": "sse",
      "url": "http://localhost:8050/sse"
    }
  }
}
```

## Detailed Usage Guide

### Workflow for Codebase Analysis

1. **Index repositories** you want to analyze using `index_repository`
2. **Verify indexing status** with `get_repository_info` to ensure processing is complete
3. **Query the repositories** using natural language with `query_repository`
4. **Find specific files** related to features or concepts using `search_repository`

### Session Management for Conversation Context

When interacting with the Greptile MCP server through any client (including Smithery), proper session management is crucial for maintaining conversation context:

1. **Generate a unique session ID** at the beginning of a conversation
2. **Reuse the same session ID** for all related follow-up queries
3. **Create a new session ID** when starting a new conversation

Example session ID management:

```python
# Generate a unique session ID
import uuid
session_id = str(uuid.uuid4())

# Initial query
initial_response = query_repository(
    query="How is authentication implemented?",
    repositories=[{"remote": "github", "repository": "owner/repo", "branch": "main"}],
    session_id=session_id  # Include the session ID
)

# Follow-up query using the SAME session ID
followup_response = query_repository(
    query="Can you provide more details about the JWT verification?",
    repositories=[{"remote": "github", "repository": "owner/repo", "branch": "main"}],
    session_id=session_id  # Reuse the same session ID
)
```

> **Important for Smithery Integration**: Agents connecting via Smithery must generate and maintain their own session IDs. The Greptile MCP server does NOT automatically generate session IDs. The session ID should be part of the agent's conversation state.

### Best Practices

- **Indexing Performance**: Smaller repositories index faster. For large monorepos, consider indexing specific branches or tags.
- **Query Optimization**: Be specific in your queries. Include relevant technical terms for better results.
- **Repository Selection**: When querying multiple repositories, list them in order of relevance to get the best results.
- **Session Management**: Use session IDs for follow-up questions to maintain context across queries.

## API Reference

### 1. Index Repository

Indexes a repository to make it searchable in future queries.

**Parameters:**
- `remote` (string): The repository host, either "github" or "gitlab"
- `repository` (string): The repository in owner/repo format (e.g., "greptileai/greptile")
- `branch` (string): The branch to index (e.g., "main")
- `reload` (boolean, optional): Whether to force reprocessing of a previously indexed repository
- `notify` (boolean, optional): Whether to send an email notification when indexing is complete

**Example:**

```javascript
// Tool Call: index_repository
{
  "remote": "github",
  "repository": "greptileai/greptile",
  "branch": "main",
  "reload": false,
  "notify": false
}
```

**Response:**
```json
{
  "message": "Indexing Job Submitted for: greptileai/greptile",
  "statusEndpoint": "https://api.greptile.com/v2/repositories/github:main:greptileai%2Fgreptile"
}
```

### 2. Query Repository

Queries repositories with natural language to get answers with code references.

**Parameters:**
- `query` (string): The natural language query about the codebase
- `repositories` (array): List of repositories to query, each with format:
  ```json
  {
    "remote": "github",
    "repository": "owner/repo",
    "branch": "main"
  }
  ```
- `session_id` (string, optional): Session ID for continuing a conversation
- `stream` (boolean, optional): Whether to stream the response
- `genius` (boolean, optional): Whether to use enhanced query capabilities

**Example:**

```javascript
// Tool Call: query_repository
{
  "query": "How is authentication handled in this codebase?",
  "repositories": [
    {
      "remote": "github",
      "repository": "greptileai/greptile",
      "branch": "main"
    }
  ],
  "session_id": null,
  "stream": false,
  "genius": true
}
```

**Response:**
```json
{
  "message": "Authentication in this codebase is handled using JWT tokens...",
  "sources": [
    {
      "repository": "greptileai/greptile",
      "remote": "github",
      "branch": "main",
      "filepath": "/src/auth/jwt.js",
      "linestart": 14,
      "lineend": 35,
      "summary": "JWT token validation middleware"
    }
  ]
}
```

### 3. Search Repository

Searches repositories to find relevant files without generating a full answer.

**Parameters:**
- `query` (string): The search query about the codebase
- `repositories` (array): List of repositories to search
- `session_id` (string, optional): Session ID for continuing a conversation
- `genius` (boolean, optional): Whether to use enhanced search capabilities

### 4. Get Repository Info

Gets information about a specific repository that has been indexed.

**Parameters:**
- `remote` (string): The repository host, either "github" or "gitlab"
- `repository` (string): The repository in owner/repo format
- `branch` (string): The branch that was indexed

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GREPTILE_API_KEY` | Your Greptile API key | (required) |
| `GITHUB_TOKEN` | GitHub/GitLab personal access token | (required) |
| `HOST` | Host to bind to | `0.0.0.0` |
| `PORT` | Port to listen on | `8050` |

## License

This project is licensed under the MIT License.

---

Built by [@sosacrazy126](https://github.com/sosacrazy126)
