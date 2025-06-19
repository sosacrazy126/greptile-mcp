# Greptile MCP Server

A Model Context Protocol (MCP) server that integrates with the Greptile API to provide intelligent code search and querying capabilities for AI agents.

[![smithery badge](https://smithery.ai/badge/@sosacrazy126/greptile-mcp)](https://smithery.ai/server/@sosacrazy126/greptile-mcp)

## Quick Start

| Environment | Setup & Install | Run Command |
|-------------|----------------|-------------|
| **Local** | `python -m venv .venv && source .venv/bin/activate && pip install -e .` | `python -m src.main` |
| **Docker** | `docker build -t greptile-mcp .` | `docker run --rm --env-file .env -p 8050:8050 greptile-mcp` |
| **Smithery** | `npm install -g smithery` | `smithery deploy` |

> Set your `GREPTILE_API_KEY` and `GITHUB_TOKEN` in `.env` before running.

## Features

### Core Tools

1. **`index_repository`** - Index repositories for search
2. **`query_repository`** - Query code with natural language
3. **`search_repository`** - Find relevant files quickly
4. **`get_repository_info`** - Check indexing status

### Key Capabilities

- 🔍 **Semantic Code Search** - Ask questions about any codebase in natural language
- 📖 **Multi-Repository Analysis** - Query across multiple repositories simultaneously
- 💬 **Conversation Context** - Maintain context across follow-up questions with session management
- 🚀 **Multiple Transports** - Support for both SSE and stdio transport protocols
- 📦 **Easy Deployment** - Docker and Smithery deployment options

## Prerequisites

- **Python 3.12+**
- **Greptile API Key** from [app.greptile.com](https://app.greptile.com/settings/api)
- **GitHub/GitLab Token** with repository access permissions

## Installation

### Local Development

```bash
git clone https://github.com/sosacrazy126/greptile-mcp.git
cd greptile-mcp
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env
# Edit .env with your API keys
```

### Docker

```bash
git clone https://github.com/sosacrazy126/greptile-mcp.git
cd greptile-mcp
# Edit .env with your API keys
docker build -t greptile-mcp .
docker run --rm --env-file .env -p 8050:8050 greptile-mcp
```

## Configuration

### MCP Client Setup (SSE)

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

### MCP Client Setup (Stdio)

```json
{
  "mcpServers": {
    "greptile": {
      "transport": "stdio",
      "command": "/path/to/.venv/bin/python",
      "args": ["-m", "src.main"],
      "env": {
        "TRANSPORT": "stdio",
        "GREPTILE_API_KEY": "your_key",
        "GITHUB_TOKEN": "your_token"
      }
    }
  }
}
```

## Usage Examples

### Basic Workflow

1. **Index a repository:**
   ```python
   index_repository("github", "facebook/react", "main")
   ```

2. **Query the codebase:**
   ```python
   query_repository(
       "How does React handle state updates?",
       [{"remote": "github", "repository": "facebook/react", "branch": "main"}]
   )
   ```

3. **Search for specific files:**
   ```python
   search_repository(
       "authentication middleware",
       [{"remote": "github", "repository": "myorg/myapp", "branch": "main"}]
   )
   ```

### Session Management for Follow-ups

```python
# Initial query (no session_id needed)
response1 = query_repository(
    "How does authentication work?",
    repositories
)

# Extract session ID from response
session_id = json.loads(response1)["_session_id"]

# Follow-up query (use same session_id)
response2 = query_repository(
    "Can you show me the JWT validation code?",
    repositories,
    session_id=session_id
)
```

## Documentation

- **[Setup Guide](docs/setup/)** - Installation and configuration
- **[User Guide](docs/USER_GUIDE.md)** - Detailed usage instructions
- **[API Documentation](docs/api/)** - Complete API reference
- **[Examples](examples/)** - Code examples and integrations

## Smithery Deployment

Deploy to Smithery for cloud hosting:

```bash
npm install -g smithery
smithery deploy
```

The server will be available at your Smithery endpoint with automatic scaling and monitoring.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GREPTILE_API_KEY` | Your Greptile API key | (required) |
| `GITHUB_TOKEN` | GitHub/GitLab access token | (required) |
| `TRANSPORT` | Transport method (`sse` or `stdio`) | `sse` |
| `PORT` | Server port for SSE transport | `8050` |
| `HOST` | Server host for SSE transport | `0.0.0.0` |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with ❤️ for the MCP ecosystem