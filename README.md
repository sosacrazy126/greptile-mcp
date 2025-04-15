# Greptile MCP Server

An MCP server implementation that integrates with the Greptile API to provide code search and querying capabilities to AI agents.
greptile-mcp/
├── src/
│   ├── main.py             # Core MCP server with Greptile tool definitions
│   └── utils.py            # Greptile client configuration and helpers
├── .env.example            # Template for environment variables
├── pyproject.toml          # Dependencies
├── Dockerfile              # Container setup
└── README.md               # Usage instructions
## Features

The server provides four essential Greptile tools:

1. **`index_repository`**: Index a repository for code search and querying.
2. **`query_repository`**: Query repositories to get an answer with code references.
3. **`search_repository`**: Search repositories for relevant files without generating a full answer.
4. **`get_repository_info`**: Get information about an indexed repository.

## Prerequisites

- Python 3.12+
- Greptile API Key (from [https://app.greptile.com/settings/api](https://app.greptile.com/settings/api))
- GitHub or GitLab Personal Access Token (PAT) with `repo` (or equivalent read) permissions for the repositories you intend to index
- Docker (recommended for deployment)

## Installation

### Using pip (for development or local testing)

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/greptile-mcp.git
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

5. Configure your environment variables in the `.env` file (add your `GREPTILE_API_KEY` and `GITHUB_TOKEN`).

### Using Docker (Recommended for deployment)

1. Clone the repository (if not already done).
2. Create a `.env` file based on `.env.example` and configure your environment variables.
3. Build the Docker image:
   ```bash
   docker build -t greptile-mcp .
   ```

## Running the Server

### Using pip

* **SSE Transport (Default):**
  Ensure `TRANSPORT=sse` and `PORT=8050` (or your chosen port) are set in your `.env` file.
  ```bash
  python -m src.main
  ```
  The server will listen on `http://<HOST>:<PORT>/sse`.

* **Stdio Transport:**
  Set `TRANSPORT=stdio` in your `.env` file. With stdio, the MCP client typically spins up the MCP server process.

### Using Docker

* **SSE Transport (Default):**
  ```bash
  # Mounts the .env file for configuration and maps the port
  docker run --rm --env-file .env -p 8050:8050 greptile-mcp
  ```
  The server will listen on `http://localhost:8050/sse` (or the host IP if not localhost).

* **Stdio Transport:**
  Configure your MCP client to run the Docker container with `TRANSPORT=stdio`.

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

## Usage Examples (Agent Perspective)

Here's how an AI agent might use these tools via an MCP client:

### 1. Index a Repository

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

### 2. Query the Repository

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

### 3. Search for Specific Files

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

### 4. Check Repository Status

```javascript
// Tool Call: get_repository_info
{
  "remote": "github",
  "repository": "greptileai/greptile",
  "branch": "main"
}
```

## Key Implementation Notes

1. **Async Client:** Uses `httpx.AsyncClient` for non-blocking I/O, compatible with the `asyncio` environment of `FastMCP`.
2. **Lifespan Management:** The `greptile_lifespan` async context manager handles the creation and cleanup of the `GreptileClient`.
3. **Tool Pattern:** Each `@mcp.tool` function is `async`, accesses the client via context, and includes proper error handling.
4. **Transport Flexibility:** Supports both `sse` and `stdio` transports via the `TRANSPORT` environment variable.
5. **Configuration via Environment:** API keys, tokens, and server settings are managed via environment variables.
6. **Error Handling:** API call errors are caught within tools and returned as informative error strings. 