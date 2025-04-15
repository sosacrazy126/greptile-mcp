# Greptile MCP Implementation

## Implementation Status

The Greptile MCP project has been successfully implemented with all core functionality. This implementation provides an MCP server that integrates with the Greptile API for code search and repository analysis.

### Completed Components

1. **Core MCP Server (`src/main.py`)**
   - Implemented a FastMCP server with four essential tools:
     - `index_repository`: For indexing repositories
     - `query_repository`: For querying repositories with natural language
     - `search_repository`: For finding relevant files without generating answers
     - `get_repository_info`: For retrieving repository metadata
   - Support for both SSE and stdio transport methods

2. **Greptile Client (`src/utils.py`)**
   - Implemented an async HTTP client using httpx
   - Methods for all Greptile API operations
   - Proper error handling and logging
   - Environment variable configuration

3. **Project Infrastructure**
   - `.env.example` template for environment variables
   - `pyproject.toml` for dependency management
   - `Dockerfile` for containerization
   - `README.md` with comprehensive usage instructions

4. **Testing Framework**
   - Unit tests for the Greptile client
   - Integration tests for MCP tools
   - Test fixtures and mocks for testing without actual API calls

### Project Structure

```
greptile-mcp/
├── src/
│   ├── __init__.py        # Make src a package
│   ├── main.py            # Core MCP server with Greptile tool definitions
│   ├── utils.py           # Greptile client configuration and helpers
│   └── tests/             # Test suite
│       ├── __init__.py
│       ├── test_client.py # Tests for the Greptile client
│       └── test_server.py # Tests for the MCP server tools
├── .env.example           # Template for environment variables
├── pyproject.toml         # Dependencies and project metadata
├── Dockerfile             # Container setup
└── README.md              # Usage instructions
```

### Next Steps

1. **Enhanced Testing**
   - Add more comprehensive test cases
   - Implement integration tests with actual API calls (using credentials)

2. **Deployment Improvements**
   - Add CI/CD configuration
   - Implement more robust error handling
   - Add monitoring and logging enhancements

3. **Documentation Expansion**
   - API reference documentation
   - More usage examples
   - Troubleshooting guide

## Usage Instructions

Please refer to the README.md for detailed setup and usage instructions. The implementation follows the specifications outlined in the memory bank files and provides all the required functionality for the Greptile MCP system.

Here is the complete `greptile-mcp` project structure and content based on your specifications:

**1. Project Structure:**

```
greptile-mcp/
├── src/
│   ├── __init__.py         # Make src a package (optional but good practice)
│   ├── main.py             # Core MCP server with Greptile tool definitions
│   └── utils.py            # Greptile client configuration and helpers
├── .env.example            # Template for environment variables
├── pyproject.toml          # Dependencies
├── Dockerfile              # Container setup
└── README.md               # Usage instructions
```

**2. File Contents:**

**`greptile-mcp/src/__init__.py`** (Empty file)

```
# This file makes the src directory a Python package.
```

**`greptile-mcp/src/main.py`**

```python
from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dotenv import load_dotenv
import asyncio
import json
import os

# Import the async client and helper
from .utils import GreptileClient, get_greptile_client

load_dotenv()

# Create a dataclass for our application context
@dataclass
class GreptileContext:
    """Context for the Greptile MCP server."""
    greptile_client: GreptileClient  # Use the specific client type

@asynccontextmanager
async def greptile_lifespan(server: FastMCP) -> AsyncIterator[GreptileContext]:
    """
    Manages the Greptile client lifecycle.

    Args:
        server: The FastMCP server instance

    Yields:
        GreptileContext: The context containing the Greptile client
    """
    # Create and return the Greptile client with the helper function in utils.py
    greptile_client = get_greptile_client()

    try:
        yield GreptileContext(greptile_client=greptile_client)
    finally:
        # Clean up the async client session
        await greptile_client.aclose()
        print("Greptile client closed.")

# Initialize FastMCP server with the Greptile client as context
mcp = FastMCP(
    "mcp-greptile",
    description="MCP server for code search and querying with Greptile API",
    lifespan=greptile_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8050")) # Ensure port is an integer
)

@mcp.tool()
async def index_repository(ctx: Context, remote: str, repository: str, branch: str, reload: bool = False, notify: bool = False) -> str:
    """Index a repository for code search and querying.

    This tool initiates the processing of a repository, making it available for future queries.
    A repository must be indexed before it can be queried or searched.

    Args:
        ctx: The MCP server provided context which includes the Greptile client
        remote: The repository host, either "github" or "gitlab"
        repository: The repository in owner/repo format (e.g., "greptileai/greptile")
        branch: The branch to index (e.g., "main")
        reload: Whether to force reprocessing of the repository (default: False)
        notify: Whether to send an email notification when indexing is complete (default: False)
    """
    try:
        greptile_client: GreptileClient = ctx.request_context.lifespan_context.greptile_client
        result = await greptile_client.index_repository(remote, repository, branch, reload, notify)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error indexing repository: {str(e)}"

@mcp.tool()
async def query_repository(ctx: Context, query: str, repositories: list, session_id: str = None, stream: bool = False, genius: bool = True) -> str:
    """Query repositories to get an answer with code references.

    This tool submits a natural language query to get an answer with relevant code references
    from the specified repositories. The repositories must have been indexed first.

    Args:
        ctx: The MCP server provided context which includes the Greptile client
        query: The natural language query about the codebase
        repositories: List of repositories to query, each with format {"remote": "github", "repository": "owner/repo", "branch": "main"}
        session_id: Optional session ID for continuing a conversation
        stream: Whether to stream the response (default: False). Note: Streaming is not fully supported via simple JSON return; this flag is passed to Greptile but the MCP tool will return the complete result once finished.
        genius: Whether to use the enhanced query capabilities (default: True)
    """
    try:
        greptile_client: GreptileClient = ctx.request_context.lifespan_context.greptile_client
        # Greptile expects messages in a specific format
        messages = [{"role": "user", "content": query}]
        result = await greptile_client.query_repositories(messages, repositories, session_id, stream, genius)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error querying repositories: {str(e)}"

@mcp.tool()
async def search_repository(ctx: Context, query: str, repositories: list, session_id: str = None, genius: bool = True) -> str:
    """Search repositories for relevant files without generating a full answer.

    This tool returns a list of relevant files based on a query without generating
    a complete answer. The repositories must have been indexed first.

    Args:
        ctx: The MCP server provided context which includes the Greptile client
        query: The natural language query about the codebase
        repositories: List of repositories to search, each with format {"remote": "github", "repository": "owner/repo", "branch": "main"}
        session_id: Optional session ID for continuing a conversation
        genius: Whether to use the enhanced search capabilities (default: True)
    """
    try:
        greptile_client: GreptileClient = ctx.request_context.lifespan_context.greptile_client
        # Greptile expects messages in a specific format
        messages = [{"role": "user", "content": query}]
        result = await greptile_client.search_repositories(messages, repositories, session_id, genius)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error searching repositories: {str(e)}"

@mcp.tool()
async def get_repository_info(ctx: Context, remote: str, repository: str, branch: str) -> str:
    """Get information about an indexed repository.

    This tool retrieves information about a specific repository that has been indexed,
    including its status and other metadata.

    Args:
        ctx: The MCP server provided context which includes the Greptile client
        remote: The repository host, either "github" or "gitlab"
        repository: The repository in owner/repo format (e.g., "greptileai/greptile")
        branch: The branch that was indexed (e.g., "main")
    """
    try:
        greptile_client: GreptileClient = ctx.request_context.lifespan_context.greptile_client
        # Construct the repository ID as expected by the Greptile API client method
        repository_id = f"{remote}:{branch}:{repository}"
        result = await greptile_client.get_repository_info(repository_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting repository info: {str(e)}"

async def main():
    transport = os.getenv("TRANSPORT", "sse").lower()
    if transport == 'sse':
        print(f"Starting MCP server with SSE transport on {mcp.host}:{mcp.port}")
        # Run the MCP server with sse transport
        await mcp.run_sse_async()
    elif transport == 'stdio':
        print("Starting MCP server with stdio transport")
        # Run the MCP server with stdio transport
        await mcp.run_stdio_async()
    else:
        print(f"Error: Unknown transport '{transport}'. Use 'sse' or 'stdio'.")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

**`greptile-mcp/src/utils.py`** (Using `httpx.AsyncClient` for async operations)

```
import httpx
import os
import urllib.parse

class GreptileClient:
    """Async client for interacting with the Greptile API."""

    def __init__(self, api_key: str, github_token: str, base_url: str = "https://api.greptile.com/v2"):
        """
        Initialize the Greptile API client.

        Args:
            api_key: Greptile API key
            github_token: GitHub/GitLab personal access token
            base_url: Base URL for the Greptile API
        """
        if not api_key:
            raise ValueError("GREPTILE_API_KEY is required")
        if not github_token:
            raise ValueError("GITHUB_TOKEN is required")

        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "X-GitHub-Token": github_token, # Note: Greptile uses this header for auth
            "Content-Type": "application/json"
        }
        # Use AsyncClient for compatibility with async MCP tools
        self.client = httpx.AsyncClient(timeout=60.0, headers=self.headers) # Longer timeout for indexing

    async def aclose(self):
        """Close the underlying HTTPX client."""
        await self.client.aclose()

    async def index_repository(self, remote: str, repository: str, branch: str, reload: bool = False, notify: bool = False) -> dict:
        """
        Index a repository for code search and querying.

        Args:
            remote: The repository host, either "github" or "gitlab"
            repository: The repository in owner/repo format
            branch: The branch to index
            reload: Whether to force reprocessing
            notify: Whether to send an email notification

        Returns:
            The API response as a dictionary
        """
        url = f"{self.base_url}/repositories"
        payload = {
            "remote": remote,
            "repository": repository,
            "branch": branch,
            "reload": reload,
            "notify": notify
        }

        response = await self.client.post(url, json=payload)
        response.raise_for_status() # Raise HTTPStatusError for bad responses (4xx or 5xx)
        return response.json()

    async def query_repositories(self, messages: list, repositories: list, session_id: str = None, stream: bool = False, genius: bool = True) -> dict:
        """
        Query repositories to get an answer with code references.

        Args:
            messages: List of message objects with role and content
            repositories: List of repository objects
            session_id: Optional session ID for continuing a conversation
            stream: Whether to stream the response
            genius: Whether to use enhanced query capabilities

        Returns:
            The API response as a dictionary
        """
        url = f"{self.base_url}/query"
        payload = {
            "messages": messages,
            "repositories": repositories,
            "stream": stream,
            "genius": genius
        }

        if session_id:
            payload["sessionId"] = session_id # Match Greptile's expected casing

        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def search_repositories(self, messages: list, repositories: list, session_id: str = None, genius: bool = True) -> dict:
        """
        Search repositories for relevant files without generating a full answer.

        Args:
            messages: List of message objects with role and content
            repositories: List of repository objects
            session_id: Optional session ID for continuing a conversation
            genius: Whether to use enhanced search capabilities

        Returns:
            The API response as a dictionary
        """
        url = f"{self.base_url}/search"
        payload = {
            "messages": messages,
            "repositories": repositories,
            "genius": genius
        }

        if session_id:
            payload["sessionId"] = session_id # Match Greptile's expected casing

        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def get_repository_info(self, repository_id: str) -> dict:
        """
        Get information about an indexed repository.

        Args:
            repository_id: Repository ID in the format "remote:branch:owner/repository"

        Returns:
            The API response as a dictionary
        """
        # URL encode the repository ID as it contains special characters like ':' and '/'
        encoded_id = urllib.parse.quote(repository_id, safe='')
        url = f"{self.base_url}/repositories/{encoded_id}"

        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

def get_greptile_client() -> GreptileClient:
    """
    Create and configure a Greptile API client based on environment variables.

    Returns:
        GreptileClient: Configured Greptile API client

    Raises:
        ValueError: If required environment variables are missing.
    """
    api_key = os.getenv("GREPTILE_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN") # Used for X-GitHub-Token header
    base_url = os.getenv("GREPTILE_BASE_URL", "https://api.greptile.com/v2")

    # Check for required variables here for early failure
    if not api_key:
        raise ValueError("GREPTILE_API_KEY environment variable is required")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required (for X-GitHub-Token header)")

    return GreptileClient(api_key=api_key, github_token=github_token, base_url=base_url)

```

**`greptile-mcp/.env.example`**

```
# The transport for the MCP server - either 'sse' or 'stdio' (defaults to sse if left empty)
TRANSPORT=sse

# Host to bind to if using sse as the transport (leave empty or use 0.0.0.0 for all interfaces)
HOST=0.0.0.0

# Port to listen on if using sse as the transport (leave empty if using stdio)
PORT=8050

# --- Greptile API configuration ---
# Get your API key from https://app.greptile.com/settings/api
GREPTILE_API_KEY=YOUR_GREPTILE_API_KEY_HERE

# GitHub/GitLab personal access token with read permissions for the repositories you want to index.
# Greptile uses this token to clone the repositories.
# See: https://docs.greptile.com/introduction/authentication#github-token
GITHUB_TOKEN=YOUR_GITHUB_OR_GITLAB_PAT_HERE

# Base URL for the Greptile API (default is https://api.greptile.com/v2)
# Only change this if you have a specific reason (e.g., enterprise endpoint)
GREPTILE_BASE_URL=https://api.greptile.com/v2

```

**`greptile-mcp/pyproject.toml`**

```
[project]
name = "greptile-mcp"
version = "0.1.0"
description = "MCP server for code search and querying with Greptile API"
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" } # Optional: Add a license
authors = [
    { name = "Your Name", email = "your.email@example.com" }, # Optional: Add author info
]
dependencies = [
    "httpx>=0.27.0,<0.28.0", # Pinned minor version for stability, allow patches
    "mcp[cli]>=1.3.0,<1.4.0", # Pinned minor version, include CLI extras
    "python-dotenv>=1.0.0,<2.0.0"
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

# Optional: Tool configuration for linters/formatters like Ruff
# [tool.ruff]
# line-length = 88
# select = ["E", "W", "F", "I", "UP", "ASYNC"] # Example selection
```

**`greptile-mcp/Dockerfile`**

```
# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    # Set default transport and port, can be overridden by --env-file or -e flags in docker run
    TRANSPORT=sse \
    PORT=8050 \
    # Set default Greptile URL, can be overridden
    GREPTILE_BASE_URL=https://api.greptile.com/v2

# Argument for build-time port configuration (optional, ENV PORT is usually sufficient)
ARG PORT=8050

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY pyproject.toml ./

# Install dependencies using pip and the pyproject.toml file
# Using --no-cache-dir reduces image size
RUN pip install --no-cache-dir -e .

# Copy the rest of the application code into the container
COPY ./src ./src

# Make port ${PORT} available to the world outside this container
EXPOSE ${PORT}

# Define the command to run your application
# Uses the environment variables set above or overridden at runtime
CMD ["python", "src/main.py"]
```

**`greptile-mcp/README.md`**

```
# Greptile MCP Server

An MCP server implementation that integrates with the Greptile API to provide code search and querying capabilities to AI agents, following the `mcp-mem0` architectural pattern.

## Features

The server provides four essential Greptile tools:

1.  **`index_repository`**: Index a repository for code search and querying.
2.  **`query_repository`**: Query repositories to get an answer with code references.
3.  **`search_repository`**: Search repositories for relevant files without generating a full answer.
4.  **`get_repository_info`**: Get information about an indexed repository.

## Prerequisites

-   Python 3.12+
-   Greptile API Key (from [https://app.greptile.com/settings/api](https://app.greptile.com/settings/api))
-   GitHub or GitLab Personal Access Token (PAT) with `repo` (or equivalent read) permissions for the repositories you intend to index. Greptile uses this to clone the code.
-   Docker (Recommended for running the server)

## Installation

### Using pip (for development or local testing)

1.  Clone this repository:
    ```bash
    git clone https://github.com/yourusername/greptile-mcp.git # Replace with your repo URL
    cd greptile-mcp
    ```

2.  Create a virtual environment (recommended):
    ```bash
    python -m venv .venv
    source .venv/bin/activate # On Windows use `.venv\Scripts\activate`
    ```

3.  Install dependencies:
    ```bash
    pip install -e .
    ```

4.  Create a `.env` file based on `.env.example`:
    ```bash
    cp .env.example .env
    ```

5.  Configure your environment variables in the `.env` file (add your `GREPTILE_API_KEY` and `GITHUB_TOKEN`).

### Using Docker (Recommended for deployment)

1.  Clone the repository (if not already done).
2.  Create a `.env` file based on `.env.example` and configure your environment variables (`GREPTILE_API_KEY`, `GITHUB_TOKEN`).
3.  Build the Docker image:
    ```bash
    # You can customize the image tag and build-time port if needed
    docker build -t mcp/greptile --build-arg PORT=8050 .
    ```

## Running the Server

### Using pip

*   **SSE Transport (Default):**
    Ensure `TRANSPORT=sse` and `PORT=8050` (or your chosen port) are set in your `.env` file.
    ```bash
    python src/main.py
    ```
    The server will listen on `http://<HOST>:<PORT>/sse`.

*   **Stdio Transport:**
    Set `TRANSPORT=stdio` in your `.env` file. With stdio, the MCP client itself typically spins up the MCP server process, so you don't run this command directly. Instead, configure your MCP client to execute the Python script (see Stdio configuration examples below).

### Using Docker

*   **SSE Transport (Default):**
    ```bash
    # Mounts the .env file for configuration and maps the port
    docker run --rm --env-file .env -p 8050:8050 mcp/greptile
    ```
    The server will listen on `http://localhost:8050/sse` (or the host IP if not localhost).

*   **Stdio Transport:**
    You configure your MCP client to run the Docker container with `TRANSPORT=stdio`. See the Docker Stdio configuration example below.

## Integration with MCP Clients

### SSE Configuration Example

Add this to your MCP client's configuration (e.g., `mcp_config.json`):

```json
{
  "mcpServers": {
    "greptile": {
      "transport": "sse",
      "url": "http://localhost:8050/sse" // Adjust host/port if needed
    }
  }
}
```

### Python with Stdio Configuration Example

Ensure `TRANSPORT=stdio` is set in the environment where the command runs, or pass it via the `env` block.

```
{
  "mcpServers": {
    "greptile": {
      "transport": "stdio",
      // Adjust paths to your virtual environment python and the script
      "command": "/path/to/your/greptile-mcp/.venv/bin/python",
      "args": ["/path/to/your/greptile-mcp/src/main.py"],
      "env": {
        "TRANSPORT": "stdio",
        "GREPTILE_API_KEY": "YOUR-GREPTILE-API-KEY", // Replace or load from secure source
        "GITHUB_TOKEN": "YOUR-GITHUB-TOKEN",       // Replace or load from secure source
        "GREPTILE_BASE_URL": "https://api.greptile.com/v2" // Optional override
      }
    }
  }
}
```

_(Note: On Windows, the python executable path would be like `C:/path/to/greptile-mcp/.venv/Scripts/python.exe`)_

### Docker with Stdio Configuration Example

This configuration tells the MCP client to run the `docker` command to start the server in stdio mode.

```
{
  "mcpServers": {
    "greptile": {
      "transport": "stdio",
      "command": "docker",
      "args": [
        "run", "--rm", "-i", // -i is crucial for stdio
        "-e", "TRANSPORT=stdio", // Set transport inside the container
        "-e", "GREPTILE_API_KEY", // Pass API key from client's env
        "-e", "GITHUB_TOKEN",     // Pass GitHub token from client's env
        "-e", "GREPTILE_BASE_URL", // Pass Base URL from client's env (optional)
        "mcp/greptile" // The image name built earlier
       ],
      "env": {
        // These env vars are for the *client* environment where 'docker run' is executed
        // They are passed into the container via the '-e' flags above.
        "GREPTILE_API_KEY": "YOUR-GREPTILE-API-KEY",
        "GITHUB_TOKEN": "YOUR-GITHUB-TOKEN",
        "GREPTILE_BASE_URL": "https://api.greptile.com/v2" // Optional override
      }
    }
  }
}
```

_(Ensure the environment variables `GREPTILE_API_KEY`, `GITHUB_TOKEN`, etc., are available in the environment where the MCP client runs this configuration.)_

## Usage Examples (Agent Perspective)

Here's how an AI agent might use these tools via an MCP client:

**Scenario:** Understand authentication in the `greptileai/greptile` repository.

1. **Index the Repository:**
    
    - _Agent Thought:_ "First, I need to make sure the repository is indexed by Greptile."
    - _Tool Call:_ `index_repository`
    - _Parameters:_
        
        ```
        {
          "remote": "github",
          "repository": "greptileai/greptile",
          "branch": "main",
          "reload": false,
          "notify": false
        }
        ```
        
    - _Expected Result:_ JSON confirming the indexing job started (e.g., `{"id": "...", "status": "queued"}`).
2. **Query the Repository:**
    
    - _Agent Thought:_ "Now that it's likely indexed or indexing, I can ask my question."
    - _Tool Call:_ `query_repository`
    - _Parameters:_
        
        ```
        {
          "query": "How is user authentication handled in this codebase?",
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
        
    - _Expected Result:_ JSON containing Greptile's answer with code snippets and references.
3. **Search for Specific Files:**
    
    - _Agent Thought:_ "Let me find the core authentication middleware or configuration files."
    - _Tool Call:_ `search_repository`
    - _Parameters:_
        
        ```
        {
          "query": "Find files related to authentication middleware or JWT handling",
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
        
    - _Expected Result:_ JSON listing relevant file paths found by Greptile search.
4. **Check Repository Status:**
    
    - _Agent Thought:_ "I should verify the indexing status for this repository branch."
    - _Tool Call:_ `get_repository_info`
    - _Parameters:_
        
        ```
        {
          "remote": "github",
          "repository": "greptileai/greptile",
          "branch": "main"
        }
        ```
        
    - _Expected Result:_ JSON containing metadata about the indexed repository, including its processing status (e.g., `{"id": "...", "status": "completed", ...}`).

## Key Implementation Notes

1. **Async Client:** Uses `httpx.AsyncClient` in `src/utils.py` for non-blocking I/O, suitable for the `asyncio` environment of `FastMCP`.
2. **Lifespan Management:** The `greptile_lifespan` async context manager in `src/main.py` handles the creation and cleanup (closing the `httpx` session) of the `GreptileClient`, making it available via `ctx`.
3. **Tool Pattern:** Each `@mcp.tool` function is `async`, accesses the client via `ctx`, calls the relevant `GreptileClient` method, formats the result as JSON, and includes error handling.
4. **Transport Flexibility:** Supports `sse` and `stdio` transports via the `TRANSPORT` environment variable.
5. **Configuration via Environment:** API keys, tokens, and server settings are managed via `.env` file or environment variables, keeping secrets out of the code.
6. **Error Handling:** API call errors (`httpx.HTTPStatusError`) are caught within tools and returned as informative error strings to the MCP client. Missing environment variables raise errors on startup.
7. **Documentation:** Tool docstrings are detailed, providing necessary information for AI agents (or developers) to understand and use them effectively. The README covers setup, execution, and integration.