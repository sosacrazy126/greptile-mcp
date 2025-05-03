# Greptile MCP Full Documentation

This document contains all detailed setup, installation, integration, usage, troubleshooting, and advanced configuration instructions for the Greptile MCP Server.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Server](#running-the-server)
- [Integration with MCP Clients](#integration-with-mcp-clients)
- [Agent Usage & Best Practices](#agent-usage--best-practices)
- [API Reference](#api-reference)
- [Integration Examples](#integration-examples)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)
- [Contributing](#contributing)
- [License](#license)
- [Smithery Deployment](#smithery-deployment)

---

**For AGENT-SPECIFIC instruction, see [../AGENT_USAGE.md](../AGENT_USAGE.md).**

---

# Features

The server provides four essential Greptile tools that enable AI agents to interact with codebases:

1. **index_repository**: Index a repository for code search and querying.
2. **query_repository**: Query repositories and get answers with code references.
3. **search_repository**: Search for relevant files without generating full answers.
4. **get_repository_info**: Get indexed repository metadata and status.

# Project Structure

```
greptile-mcp/
├── src/
│   ├── main.py             # Core MCP server with Greptile tool definitions
│   ├── utils.py            # Greptile client configuration and helpers
│   └── tests/              # Unit and integration tests
├── .env.example            # Template for environment variables
├── pyproject.toml          # Dependencies and project metadata
├── Dockerfile              # Container setup
└── README.md               # Minimal usage cheatsheet, this file for full docs
```

# Prerequisites

- **Python 3.12+**
- **Greptile API Key** (from https://app.greptile.com/settings/api)
- **GitHub/GitLab Personal Access Token** with read permissions
- **Docker** (optional, for deployment)
- **Smithery** (optional, for cloud deployment)

# Installation

## 1. Local/Python

```bash
git clone https://github.com/sosacrazy126/greptile-mcp.git
cd greptile-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
# edit .env and fill out GREPTILE_API_KEY and GITHUB_TOKEN
```

## 2. Docker

```bash
git clone https://github.com/sosacrazy126/greptile-mcp.git
cd greptile-mcp
cp .env.example .env
# Edit .env file to add credentials
docker build -t greptile-mcp .
docker run --rm --env-file .env -p 8050:8050 greptile-mcp
```

## 3. Smithery Cloud

```bash
npm install -g smithery
smithery deploy
# Provide greptileApiKey and githubToken as prompted
```

# Running the Server

For all options, ensure `.env` exists and you have added your GREPTILE_API_KEY and GITHUB_TOKEN.

### SSE Transport (default):

- `python -m src.main`
- or with Docker: `docker run --rm --env-file .env -p 8050:8050 greptile-mcp`
- or via Smithery: `smithery deploy`

### Stdio Transport:

- Set `TRANSPORT=stdio` in your `.env`.
- For dev/local, run: `TRANSPORT=stdio python -m src.main`
- In Docker: `docker run --rm -i --env-file .env -e TRANSPORT=stdio greptile-mcp`

# Integration with MCP Clients

Add server URL to your client's config as documented previously, e.g.:

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

For stdio, see example command/args in this repo and original README.

# Agent Usage & Best Practices

- Use unique session IDs for conversations
- Always re-use the session_id for follow-up queries
- See [../AGENT_USAGE.md](../AGENT_USAGE.md) for full agent guidance and API examples

# API Reference

**Full tool schemas, request/response examples, and detailed API documentation have been moved to [API_REFERENCE.md](API_REFERENCE.md)** (TODO: create if needed, or keep in this file if preferred).

# Integration Examples

- [Python integration, LLM chatbot, and CLI samples moved from README—see previous documentation or request examples in issues/discussions.]

# Troubleshooting / Advanced Usage

Common issues, troubleshooting, logging, and advanced environment variables/options previously in README are here.

# Contributing

See CONTRIBUTING section of the previous README.

# License

MIT License—see project root for license file.

---

For any details beyond this, see the commit history or raise an issue!