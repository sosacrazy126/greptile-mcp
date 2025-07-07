# Technical Context - Greptile MCP Server

## Technology Stack

### Core Technologies
- **Python 3.12**: Latest stable Python with modern async features
- **FastMCP 2.0**: Modern MCP server framework (≥2.10.0)
- **httpx**: Async HTTP client for Greptile API integration (≥0.27.0)
- **python-dotenv**: Environment variable management (≥1.0.0)
- **uvloop**: High-performance event loop (≥0.19.0)

### Development Environment
- **Docker**: Containerization for consistent deployment
- **Git**: Version control with GitHub integration
- **VS Code**: Primary development environment
- **Python Virtual Environment**: Isolated dependency management

### External Dependencies
- **Greptile API**: AI-powered code analysis service
- **GitHub API**: Repository access and authentication
- **MCP Protocol**: Model Context Protocol 2024-11-05 specification

## Development Setup

### Prerequisites
```bash
# Required software
- Python 3.12+
- Docker Desktop
- Git
- VS Code (recommended)

# Required accounts/tokens
- Greptile API account and API key
- GitHub Personal Access Token
- Docker Hub account (for registry submission)
```

### Local Development
```bash
# Clone repository
git clone https://github.com/sosacrazy126/greptile-mcp
cd greptile-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GREPTILE_API_KEY="your_greptile_api_key"
export GITHUB_TOKEN="your_github_token"

# Run server
python -m src.main
```

### Docker Development
```bash
# Build image
docker build -t greptile-mcp .

# Run container
docker run --rm \
  -e GREPTILE_API_KEY="your_api_key" \
  -e GITHUB_TOKEN="your_token" \
  greptile-mcp
```

## Technical Constraints

### API Rate Limits
- **Greptile API**: Varies by plan, typically 100-1000 requests/hour
- **GitHub API**: 5000 requests/hour for authenticated users
- **Mitigation**: Implement request queuing and caching where appropriate

### Memory Constraints
- **Repository Size**: Large repositories may require significant memory for indexing
- **Concurrent Sessions**: Each session maintains conversation context
- **Docker Limits**: Container memory limits in deployment environments

### Network Requirements
- **Outbound HTTPS**: Required for Greptile and GitHub API access
- **Firewall Rules**: Ensure ports 443 (HTTPS) and 80 (HTTP) are accessible
- **DNS Resolution**: Reliable DNS for api.greptile.com and api.github.com

### Security Considerations
- **API Key Management**: Never commit API keys to version control
- **Environment Variables**: Use secure environment variable injection
- **Token Rotation**: Support for rotating GitHub tokens
- **Input Validation**: Sanitize all user inputs before API calls

## Deployment Architectures

### Smithery Deployment
```yaml
# smithery.yaml configuration
name: greptile-mcp
version: 1.0.0
description: AI-powered code analysis MCP server
runtime: docker
environment:
  - GREPTILE_API_KEY
  - GITHUB_TOKEN
```

### Docker Registry Deployment
```yaml
# Expected Docker Hub configuration
name: mcp/greptile-mcp
category: code-analysis
tags:
  - code-search
  - repository-analysis
  - ai-powered
  - greptile
```

### Self-Hosted Deployment
```bash
# Production deployment example
docker run -d \
  --name greptile-mcp \
  --restart unless-stopped \
  -e GREPTILE_API_KEY="$GREPTILE_API_KEY" \
  -e GITHUB_TOKEN="$GITHUB_TOKEN" \
  -p 8080:8080 \
  greptile-mcp:latest
```

## Performance Characteristics

### Startup Performance
- **Cold Start**: ~2-3 seconds (FastMCP 2.0 optimization)
- **Warm Start**: ~1 second (cached dependencies)
- **Memory Usage**: ~50-100MB baseline

### Runtime Performance
- **Query Response**: 1-5 seconds (depends on repository size)
- **Indexing Time**: 30 seconds - 5 minutes (varies by repository)
- **Concurrent Users**: Supports 10-50 concurrent sessions

### Optimization Strategies
- **Connection Pooling**: Reuse HTTP connections to Greptile API
- **Response Caching**: Cache repository information for repeated queries
- **Async Processing**: Non-blocking I/O for all external API calls
- **Memory Management**: Efficient session cleanup and garbage collection

## Integration Patterns

### MCP Client Integration
```python
# Example MCP client usage
client = MCPClient("greptile-mcp")
await client.call_tool("query_repository", {
    "query": "How does authentication work?",
    "repositories": '[{"remote": "github", "repository": "myorg/myapp", "branch": "main"}]'
})
```

### Environment Configuration
```bash
# Required environment variables
GREPTILE_API_KEY=gpt_xxx...        # Greptile API authentication
GITHUB_TOKEN=ghp_xxx...            # GitHub repository access

# Optional environment variables
TRANSPORT=stdio                    # MCP transport method
HOST=0.0.0.0                      # Server host (for HTTP transport)
PORT=8080                         # Server port (for HTTP transport)
```

### Error Handling Strategy
```python
# Structured error responses
{
    "error": "Human-readable error message",
    "type": "ErrorClassName",
    "session_id": "uuid-string",
    "timestamp": "ISO-8601-timestamp"
}
```

## Development Workflow

### Code Organization
```
greptile-mcp/
├── src/
│   ├── main.py          # FastMCP server and MCP tools
│   ├── utils.py         # Greptile API client
│   └── __init__.py      # Package initialization
├── memory-bank/         # Project documentation
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
├── smithery.yaml       # Smithery deployment config
├── .dockerignore       # Docker build exclusions
└── README.md           # Project documentation
```

### Testing Strategy
- **Unit Tests**: Mock Greptile API responses for isolated testing
- **Integration Tests**: Test with real API calls using test repositories
- **Docker Tests**: Validate container builds and deployments
- **Smithery Tests**: Verify deployment compatibility

### Version Management
- **Semantic Versioning**: Major.Minor.Patch format
- **Git Tags**: Tag releases for deployment tracking
- **Dependency Pinning**: Use minimum version constraints (≥) for flexibility
- **Security Updates**: Regular dependency updates for security patches
