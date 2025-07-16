# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Greptile MCP (Model Context Protocol) server that provides AI-powered code search and querying capabilities. It's designed to integrate with the Greptile API to index repositories and answer natural language questions about codebases.

## Build and Development Commands

### Installation
```bash
# Local development setup
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .

# Create environment file
cp .env.example .env
# Edit .env with your GREPTILE_API_KEY and GITHUB_TOKEN
```

### Running the Server
```bash
# Run locally (SSE transport - default)
python -m src.main

# Run with stdio transport (for MCP client integration)
TRANSPORT=stdio python -m src.main

# Run with Docker
docker build -t greptile-mcp .
docker run --rm --env-file .env -p 8080:8080 greptile-mcp
```

### Testing
```bash
# Run tests (if test framework is available)
python -m pytest src/tests/

# Test individual components
python -m pytest src/tests/test_server.py
python -m pytest src/tests/test_client.py
```

### Code Quality
```bash
# Code formatting and linting (using ruff)
ruff check src/
ruff format src/
```

## Architecture

### Core Components

1. **`src/main.py`** - Main MCP server implementation using FastMCP (Refactored Architecture)
   - Defines 5 main tools: `greptile_help`, `index_repository`, `query_repository`, `search_repository`, `get_repository_info`
   - Uses modular service and handler architecture for better maintainability
   - Maintains full backward compatibility with original implementation

2. **`src/services/`** - Service layer for business logic
   - `greptile_service.py` - Greptile API client management and operations
   - `session_service.py` - Session and conversation context management

3. **`src/handlers/`** - Handler layer for tool implementations
   - `index_handler.py` - Repository indexing operations
   - `query_handler.py` - Natural language query processing
   - `search_handler.py` - File search operations
   - `info_handler.py` - Repository information retrieval

4. **`src/models/`** - Data models and type definitions
   - `requests.py` - Request model definitions
   - `responses.py` - Response model definitions including GreptileContext

5. **`src/utils.py`** - Utility functions and legacy compatibility
   - `GreptileClient` class for async HTTP communication with Greptile API
   - `SessionManager` for in-memory conversation context management
   - Helper utilities for JSON parsing and client configuration

### Key Design Patterns

- **Modular Architecture**: Clean separation of concerns with dedicated service and handler layers
- **Dependency Injection**: Services are injected into handlers for better testability and maintainability
- **Backward Compatibility**: Full compatibility with original tool interfaces while using improved internal structure
- **Async/Await**: All API calls are asynchronous using httpx for better concurrency
- **Session Management**: Conversation context is maintained via session IDs for multi-turn queries
- **Error Handling**: Comprehensive error handling with structured JSON error responses
- **Transport Flexibility**: Supports both SSE (Server-Sent Events) and stdio transports for different deployment scenarios

### Tool Functions

Each tool function follows the refactored pattern:
1. Validate handler initialization 
2. Delegate to appropriate handler with parsed parameters
3. Handler manages service interactions and error handling
4. Return JSON-serialized response with proper error handling

### Available Tools

1. **`greptile_help`** - Comprehensive guide and documentation for using all Greptile MCP features
2. **`index_repository`** - Index a repository to make it searchable (required first step)
3. **`query_repository`** - Query repositories using natural language
4. **`search_repository`** - Search for relevant files without generating full answers
5. **`get_repository_info`** - Get information about indexed repositories

### Environment Configuration

Required environment variables:
- `GREPTILE_API_KEY` - API key for Greptile service
- `GITHUB_TOKEN` - GitHub personal access token for repository access
- `GREPTILE_BASE_URL` - Base URL for Greptile API (defaults to https://api.greptile.com/v2)
- `TRANSPORT` - Transport method (sse or stdio)
- `HOST` - Host binding for SSE transport (default: 0.0.0.0)
- `PORT` - Port for SSE transport (default: 8080)

### Deployment Options

1. **Local Development**: Direct Python execution with virtual environment
2. **Docker**: Containerized deployment using included Dockerfile
3. **Smithery**: Cloud deployment using smithery.yaml configuration
4. **MCP Client Integration**: Stdio transport for integration with MCP-compatible clients

## Development Notes

- The codebase uses Python 3.12+ features and modern async patterns with a refactored modular architecture
- FastMCP handles the MCP protocol details, allowing focus on business logic in services and handlers
- Repository indexing is asynchronous - use `get_repository_info` to check status
- Session IDs are auto-generated if not provided but should be maintained by clients for conversation continuity
- **Enhanced Streaming Support**: Real-time Server-Sent Events (SSE) processing with structured chunk handling
- **Streaming Features**: Live text chunks, real-time citations, session management, and performance metadata
- The refactored architecture maintains full backward compatibility while improving maintainability and testability
- Use `greptile_help` tool to get comprehensive usage documentation and examples

## Ongoing Development Features

- Add these new features