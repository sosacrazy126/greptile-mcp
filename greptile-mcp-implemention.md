# Greptile MCP Implementation Documentation

## 1. System Overview

**Purpose**: MCP (Model Context Protocol) server that integrates with Greptile API to provide AI agents with advanced code search and querying capabilities.

**Key Features**:
- Repository indexing for code search
- Natural language code querying with context
- File search across multiple repositories  
- Repository information and status tracking
- Session management for conversation continuity
- Smithery deployment support

**Target Users**: AI agents, developers, and tools requiring code analysis capabilities

## 2. Architecture

**High-Level Design**: FastMCP-based server with async HTTP client architecture

**Key Components**:
- **FastMCP Server**: Core MCP protocol implementation
- **Greptile API Client**: HTTP client for Greptile service integration
- **Tool Handlers**: Four main tools (index, query, search, info)
- **Session Management**: UUID-based conversation tracking
- **Transport Layer**: Support for stdio and SSE transports

**Data Flow**:
1. Client requests via MCP protocol
2. Server validates and processes requests
3. Greptile API calls for code analysis
4. Response formatting and return to client

## 3. Technology Stack

**Backend Language/Framework**: Python 3.12+ with FastMCP 2.0

**Key Libraries/Dependencies**:
- `fastmcp` - MCP server implementation
- `httpx` - Async HTTP client for Greptile API
- `python-dotenv` - Environment variable management
- `uvicorn` - ASGI server for SSE transport

**Database**: None (stateless server, uses Greptile API)

**Deployment**: Docker containers with Smithery support

## 4. Implementation Details

**Core Tools**:

1. **`index_repository`**
   - Process repositories for searchability
   - Support for GitHub/GitLab integration
   - Configurable reload and notification options

2. **`query_repository`** 
   - Natural language code querying
   - Multi-repository support
   - Session-based conversation context
   - Streaming response capabilities

3. **`search_repository`**
   - File-focused search without full answers
   - Relevance-ranked results
   - Performance optimized for quick lookups

4. **`get_repository_info`**
   - Index status verification
   - Repository metadata retrieval
   - Progress tracking for indexing jobs

**API Design**: RESTful integration with Greptile API using async HTTP patterns

**Data Models**: Repository objects with remote, repository, and branch specifications

## 5. Setup and Deployment

**Local Development Setup**:
```bash
# Clone and setup
git clone https://github.com/sosacrazy126/greptile-mcp.git
cd greptile-mcp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Environment variables
export GREPTILE_API_KEY=your_api_key
export GITHUB_TOKEN=your_github_token

# Run server
python -m src.main
```

**Deployment Strategy**: 
- Docker containerization with multi-stage builds
- Smithery platform deployment support
- Environment-based configuration
- SSE transport for web integration

**Infrastructure**: 
- Container-based deployment
- HTTP/HTTPS endpoint exposure
- Environment variable configuration
- Health check endpoints

## 6. Current Implementation Status

**Completed Features**:
✅ FastMCP 2.0 migration complete
✅ Four core Greptile tools implemented
✅ Docker deployment ready
✅ Smithery integration configured
✅ Session management system
✅ Comprehensive documentation
✅ MIT license applied

**Recent Updates**:
- Production cleanup completed
- Docker registry submission prepared
- Test suite validation implemented
- Parameter mapping issues resolved

**Architecture Decisions**:
- **Decision**: FastMCP 2.0 as primary framework
- **Rationale**: Modern MCP implementation with better performance
- **Implication**: Improved async handling and client compatibility

- **Decision**: Stateless server design
- **Rationale**: Scalability and simplicity
- **Implication**: Session state managed by Greptile API

## 7. Integration Examples

**Claude Desktop Integration**:
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

**Smithery Deployment**:
```yaml
build:
  dockerfile: Dockerfile
startCommand:
  type: stdio
  configSchema:
    required: ["greptileApiKey", "githubToken"]
```

**Session Management Example**:
```python
import uuid
session_id = str(uuid.uuid4())
# Use same session_id for conversation continuity
```

---

**Last Updated**: Current as of latest repository state
**Repository**: https://github.com/sosacrazy126/greptile-mcp
**Documentation Status**: Implementation complete and production ready