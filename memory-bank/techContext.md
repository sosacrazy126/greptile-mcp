# Greptile MCP Technical Context

## Technology Stack

### Core Technologies
- **Python**: Primary programming language
- **FastMCP**: MCP server framework for creating MCP-compatible tools
- **HTTPX**: Async HTTP client for Greptile API communication
- **JSON**: Data interchange format for API requests and responses
- **Python-dotenv**: Environment variable management

### External Services
- **Greptile API**: Code search and analysis service
- **GitHub/GitLab API**: Source for repository data (via Greptile)

## Development Environment

### Requirements
- Python 3.9+
- Poetry or pip for dependency management
- Access to Greptile API (requires API key)
- GitHub/GitLab personal access token

### Local Setup
1. Clone the repository
2. Install dependencies using Poetry or pip
3. Create `.env` file with required environment variables
4. Run the server using `python -m src.main`

## Environment Variables
- `GREPTILE_API_KEY`: Authentication key for Greptile API
- `GITHUB_TOKEN`: Personal access token for GitHub/GitLab
- `HOST`: Host address to bind the server (default: 0.0.0.0)
- `PORT`: Port to run the server on (default: 8050)
- `TRANSPORT`: Transport method, either "sse" or "stdio" (default: sse)

## Dependencies

### Production Dependencies
- `mcp-server`: Core MCP server implementation
- `httpx`: Async HTTP client
- `python-dotenv`: Environment variable loading

### Development Dependencies
- `pytest`: Testing framework
- `pytest-asyncio`: Async testing support
- `black`: Code formatting
- `isort`: Import sorting
- `mypy`: Type checking

## API Integration

### Greptile API Endpoints
- `/v2/repositories`: For indexing repositories
- `/v2/query`: For querying indexed repositories
- `/v2/search`: For searching indexed repositories
- `/v2/repository/{repository_id}`: For repository metadata

### Authentication
- Bearer token authentication with Greptile API
- GitHub/GitLab token passed via X-GitHub-Token header

## Deployment Options

### Docker Container
- Containerized deployment with environment variables
- Exposed port based on configuration
- Volume mounting for persistent data (if needed)

### Direct Hosting
- Can be deployed directly on a server with Python installed
- Systemd service for process management
- Nginx or similar for proxying if using SSE transport 