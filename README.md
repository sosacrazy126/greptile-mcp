# Greptile MCP Server

An MCP (Model Context Protocol) server implementation that integrates with the Greptile API to provide code search and querying capabilities to AI agents. This connector allows AI assistants to understand, analyze, and query codebases with natural language.


**Project Structure:**
```
greptile-mcp/
├── src/
│   ├── main.py             # Core MCP server with Greptile tool definitions
│   ├── utils.py            # Greptile client configuration and helpers
│   └── tests/              # Unit and integration tests
├── .env.example            # Template for environment variables
├── pyproject.toml          # Dependencies and project metadata
├── Dockerfile              # Container setup
└── README.md               # Documentation
```

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Server](#running-the-server)
- [Integration with MCP Clients](#integration-with-mcp-clients)
- [Detailed Usage Guide](#detailed-usage-guide)
- [API Reference](#api-reference)
- [Integration Examples](#integration-examples)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)
- [Contributing](#contributing)
- [License](#license)
- [Smithery Deployment](#smithery-deployment)

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
      baseUrl:
        type: string
        description: "Base URL for Greptile API"
        default: "https://api.greptile.com/v2"
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

### Additional Documentation

For detailed usage instructions for AI agents, see the [Agent Usage Guide](./AGENT_USAGE.md).

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

### Using pip (for development or local testing)

1. Clone this repository:
   ```bash
   git clone https://github.com/sosacrazy126/greptile-mcp.git
   cd greptile-mcp
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Configure your environment variables in the `.env` file:
   ```
   GREPTILE_API_KEY=your_api_key_here
   GITHUB_TOKEN=your_github_token_here
   ```

### Using Docker (Recommended for deployment)

1. Clone the repository:
   ```bash
   git clone https://github.com/sosacrazy126/greptile-mcp.git
   cd greptile-mcp
   ```

2. Create a `.env` file based on `.env.example` and configure your environment variables.

3. Build the Docker image:
   ```bash
   docker build -t greptile-mcp .
   ```

## Running the Server

### Using pip

#### SSE Transport (Default)

  Ensure `TRANSPORT=sse` and `PORT=8050` (or your chosen port) are set in your `.env` file.

  ```bash
  python -m src.main
  ```

  The server will listen on `http://<HOST>:<PORT>/sse`.

#### Stdio Transport

Set `TRANSPORT=stdio` in your `.env` file. With stdio, the MCP client typically spins up
 the MCP server process.

```bash
# Usually invoked by an MCP client, not directly
TRANSPORT=stdio python -m src.main
```

### Using Docker

#### SSE Transport (Default)

  ```bash
  # Mounts the .env file for configuration and maps the port
  docker run --rm --env-file .env -p 8050:8050 greptile-mcp
  ```

  The server will listen on `http://localhost:8050/sse` (or the host IP if not localhost).

#### Stdio Transport

  Configure your MCP client to run the Docker container with `TRANSPORT=stdio`.

```bash
# Example of running with stdio transport
docker run --rm -i --env-file .env -e TRANSPORT=stdio greptile-mcp
```

## Integration with MCP Clients

### SSE Configuration Example

Add this to your MCP client's configuration (e.g., `mcp_config.json`):

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

### Python with Stdio Configuration Example

Ensure `TRANSPORT=stdio` is set in the environment where the command runs:

```json
{
  "mcpServers": {
    "greptile": {
      "transport": "stdio",
      "command": "/path/to/your/greptile-mcp/.venv/bin/python",
      "args": ["-m", "src.main"],
      "env": {
        "TRANSPORT": "stdio",
        "GREPTILE_API_KEY": "YOUR-GREPTILE-API-KEY",
        "GITHUB_TOKEN": "YOUR-GITHUB-TOKEN",
        "GREPTILE_BASE_URL": "https://api.greptile.com/v2"
      }
    }
  }
}
```

### Docker with Stdio Configuration Example

```json
{
  "mcpServers": {
    "greptile": {
      "transport": "stdio",
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TRANSPORT=stdio",
        "-e", "GREPTILE_API_KEY",
        "-e", "GITHUB_TOKEN",
        "-e", "GREPTILE_BASE_URL",
        "greptile-mcp"
      ],
      "env": {
        "GREPTILE_API_KEY": "YOUR-GREPTILE-API-KEY",
        "GITHUB_TOKEN": "YOUR-GITHUB-TOKEN",
        "GREPTILE_BASE_URL": "https://api.greptile.com/v2"
      }
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

**Example:**

```javascript
// Tool Call: search_repository
{
  "query": "Find files related to authentication middleware",
  "repositories": [
    {
      "remote": "github",
      "repository": "greptileai/greptile", 
      "branch": "main"
    }
  ],
  "session_id": null,
  "genius": true
}
```

**Response:**
```json
{
  "sources": [
    {
      "repository": "greptileai/greptile",
      "remote": "github",
      "branch": "main",
      "filepath": "/src/auth/middleware.js",
      "linestart": 1,
      "lineend": 45,
      "summary": "Authentication middleware implementation"
    },
    {
      "repository": "greptileai/greptile",
      "remote": "github",
      "branch": "main",
      "filepath": "/src/auth/jwt.js",
      "linestart": 1,
      "lineend": 78,
      "summary": "JWT token handling functions"
    }
  ]
}
```

### 4. Get Repository Info

Gets information about a specific repository that has been indexed.

**Parameters:**
- `remote` (string): The repository host, either "github" or "gitlab"
- `repository` (string): The repository in owner/repo format
- `branch` (string): The branch that was indexed

**Example:**

```javascript
// Tool Call: get_repository_info
{
  "remote": "github",
  "repository": "greptileai/greptile",
  "branch": "main"
}
```

**Response:**
```json
{
  "repository": "greptileai/greptile",
  "remote": "github",
  "branch": "main",
  "private": false,
  "status": "COMPLETED",
  "filesProcessed": 234,
  "numFiles": 234,
  "sha": "a1b2c3d4e5f6..."
}
```

## Integration Examples

### 1. Integration with Claude.ai via Anthropic API

```python
from anthropic import Anthropic
import json
import requests

# Set up Anthropic client
anthropic = Anthropic(api_key="your_anthropic_key")

# Function to call Greptile MCP
def query_code(question, repositories):
    response = requests.post(
        "http://localhost:8050/tools/greptile/query_repository",
        json={
            "query": question,
            "repositories": repositories,
            "genius": True
        }
    )
    return json.loads(response.text)

# Ask Claude with enhanced code context
def ask_claude_with_code_context(question, repositories):
    # Get code context from Greptile
    code_context = query_code(question, repositories)
    
    # Format the context for Claude
    formatted_context = f"Code Analysis Result:\n{code_context['message']}\n\nRelevant Files:\n"
    for source in code_context.get('sources', []):
        formatted_context += f"- {source['filepath']} (lines {source['linestart']}-{source['lineend']})\n"
    
    # Send to Claude with context
    message = anthropic.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": f"Based on this code context:\n\n{formatted_context}\n\nQuestion: {question}"}
        ]
    )
    
    return message.content

# Example usage
answer = ask_claude_with_code_context(
    "How does the authentication system work?",
    [{"remote": "github", "repository": "greptileai/greptile", "branch": "main"}]
)
print(answer)
```

### 2. Integration with an LLM-based Chatbot

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
import json

app = FastAPI()

# Greptile MCP endpoint
GREPTILE_MCP_URL = "http://localhost:8050/tools/greptile"

@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_message = data.get("message", "")
    
    # Check if this is a code-related question
    if "code" in user_message or "repository" in user_message or "function" in user_message:
        # Query the repository through Greptile MCP
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GREPTILE_MCP_URL}/query_repository",
                json={
                    "query": user_message,
                    "repositories": [
                        {"remote": "github", "repository": "your-org/your-repo", "branch": "main"}
                    ],
                    "genius": True
                }
            )
            
            greptile_result = response.json()
            
            # Process the result and return to the user
            answer = greptile_result.get("message", "")
            sources = greptile_result.get("sources", [])
            
            return JSONResponse({
                "message": answer,
                "code_references": sources
            })
    
    # For non-code questions, use your regular LLM
    return JSONResponse({
        "message": "This appears to be a general question. I'll handle it normally."
    })

# Run with: uvicorn app:app --reload
```

### 3. Command-line Code Querying Tool

```python
#!/usr/bin/env python3
import argparse
import json
import requests
import sys

def main():
    parser = argparse.ArgumentParser(description="Query code repositories using natural language")
    parser.add_argument("query", help="The natural language query about the code")
    parser.add_argument("--repo", "-r", required=True, help="Repository in format github:owner/repo:branch")
    parser.add_argument("--genius", "-g", action="store_true", help="Use enhanced query capabilities")
    args = parser.parse_args()
    
    # Parse the repository string
    try:
        remote, repo_path = args.repo.split(":", 1)
        if ":" in repo_path:
            repo, branch = repo_path.split(":", 1)
        else:
            repo = repo_path
            branch = "main"
    except ValueError:
        print("Error: Repository must be in format 'github:owner/repo:branch' or 'github:owner/repo'")
        sys.exit(1)
        
    # Prepare the request
    payload = {
        "query": args.query,
        "repositories": [
            {
                "remote": remote,
                "repository": repo,
                "branch": branch
            }
        ],
        "genius": args.genius
    }
    
    # Make the request
    try:
        response = requests.post(
            "http://localhost:8050/tools/greptile/query_repository",
            json=payload
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Process the response
    result = response.json()
    
    # Display the answer
    print("\n=== ANSWER ===\n")
    print(result.get("message", "No answer found"))
    
    # Display the sources
    sources = result.get("sources", [])
    if sources:
        print("\n=== CODE REFERENCES ===\n")
        for i, source in enumerate(sources, 1):
            print(f"{i}. {source['filepath']} (lines {source.get('linestart', '?')}-{source.get('lineend', '?')})")
            print(f"   Repository: {source['repository']} ({source['branch']})")
            if 'summary' in source:
                print(f"   Summary: {source['summary']}")
            print()

if __name__ == "__main__":
    main()
```

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

**Symptom**: You receive `401 Unauthorized` or `Repository not found with configured credentials` errors.

**Solutions**:
- Verify your Greptile API key is valid and correctly set in the `.env` file
- Check if your GitHub/GitLab token has expired (they typically expire after a set period)
- Ensure your GitHub/GitLab token has the `repo` scope for accessing repositories
- Test your GitHub token directly with the GitHub API to verify it's working

**Testing GitHub Token**:
```bash
curl -H "Authorization: token YOUR_GITHUB_TOKEN" https://api.github.com/user
```

#### 2. Repository Not Found

**Symptom**: The API returns a 404 error or "Repository not found" message.

**Solutions**:
- Verify the repository exists and is accessible with your GitHub/GitLab token
- Double-check the repository format (it should be `owner/repo`)
- For private repositories, ensure your token has appropriate access permissions
- Verify the branch name is correct

#### 3. Connection Issues

**Symptom**: Unable to connect to the MCP server.

**Solutions**:
- Check if the server is running (`ps aux | grep src.main`)
- Verify the port is not being used by another application
- Check network settings and firewall configurations
- Try a different port by changing the `PORT` value in your `.env` file

#### 4. Docker Issues

**Symptom**: Docker container fails to start or operate correctly.

**Solutions**:
- Check Docker logs: `docker logs <container_id>`
- Verify the `.env` file is correctly mounted
- Ensure the port mapping is correct in your `docker run` command
- Check if the Docker network configuration allows required connections

### Logs and Debugging

To enable more verbose logging, set the following environment variables:

```bash
# Add to your .env file
DEBUG=true
LOG_LEVEL=debug
```

For troubleshooting specific MCP interactions, examine the MCP server logs:

```bash
# Run with enhanced logging
LOG_LEVEL=debug python -m src.main
```

## Advanced Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TRANSPORT` | Transport method (`sse` or `stdio`) | `sse` |
| `HOST` | Host to bind to for SSE transport | `0.0.0.0` |
| `PORT` | Port for SSE transport | `8050` |
| `GREPTILE_API_KEY` | Your Greptile API key | (required) |
| `GITHUB_TOKEN` | GitHub/GitLab personal access token | (required) |
| `GREPTILE_BASE_URL` | Greptile API base URL | `https://api.greptile.com/v2` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `info` |

### Custom API Endpoints

If you need to use a custom Greptile API endpoint (e.g., for enterprise installations), modify the `GREPTILE_BASE_URL` environment variable:

```
GREPTILE_BASE_URL=https://greptile.your-company.com/api/v2
```

### Performance Tuning

For production deployments, consider these performance optimizations:

1. **Worker Configuration**: When using SSE transport with Uvicorn, configure appropriate worker count:
   ```bash
   # For CPU-bound applications: workers = 1-2 × CPU cores
   uvicorn src.main:app --workers 4
   ```

2. **Timeout Settings**: Adjust timeouts for large repositories:
   ```
   # Add to .env
   GREPTILE_TIMEOUT=120.0  # Default is 60.0 seconds
   ```

3. **Memory Optimization**: For large deployments, consider container resource limits:
   ```bash
   docker run --rm --env-file .env -p 8050:8050 --memory="1g" --cpus="1.0" greptile-mcp
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

For development, install additional dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Built with ❤️ by the [Greptile Team](https://github.com/greptileai) 