# System Patterns - Greptile MCP Server

## Architecture Overview

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │  Greptile MCP   │    │  Greptile API   │
│  (AI Assistant) │◄──►│     Server      │◄──►│   (External)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ GitHub/GitLab   │
                       │   Repository    │
                       └─────────────────┘
```

### Component Architecture
```
FastMCP 2.0 Server
├── MCP Tools (4 core functions)
│   ├── index_repository
│   ├── query_repository  
│   ├── search_repository
│   └── get_repository_info
├── GreptileClient (API wrapper)
│   ├── HTTP client management
│   ├── Authentication handling
│   └── Response processing
└── Session Management
    ├── UUID generation
    ├── Context preservation
    └── Conversation history
```

## Key Design Patterns

### 1. Simplified Parameter Pattern
**Problem**: FastMCP 2.0 couldn't handle complex nested types like `List[Dict[str, str]]`
**Solution**: Use JSON string parameters with runtime parsing

```python
# Before (caused MCP validation errors)
async def query_repository(repositories: List[Dict[str, str]]) -> Dict[str, Any]:

# After (FastMCP compatible)
async def query_repository(repositories: str) -> str:
    repositories_list = json.loads(repositories)  # Parse at runtime
    result = await client.query_repositories(...)
    return json.dumps(result)  # Serialize response
```

### 2. Parameter Mapping Pattern
**Problem**: MCP tool interface differs from Greptile API interface
**Solution**: Convert between interfaces transparently

```python
# MCP Tool Interface (user-friendly)
async def query_repository(query: str, repositories: str):
    # Convert to Greptile API format
    messages = [{"role": "user", "content": query}]
    repositories_list = json.loads(repositories)
    
    # Call Greptile API with correct parameters
    result = await client.query_repositories(
        messages=messages,  # Not 'query'
        repositories=repositories_list
    )
```

### 3. Error Boundary Pattern
**Problem**: API failures should not crash the MCP server
**Solution**: Comprehensive error handling with structured responses

```python
try:
    result = await client.query_repositories(...)
    return json.dumps(result)
except Exception as e:
    return json.dumps({
        "error": str(e),
        "type": type(e).__name__,
        "session_id": session_id
    })
```

### 4. Session Context Pattern
**Problem**: Maintain conversation context across multiple queries
**Solution**: Session ID management with message history

```python
# Generate session ID if not provided
if session_id is None:
    session_id = str(uuid.uuid4())

# Merge conversation history
if previous_messages_list:
    messages = previous_messages_list + messages

# Include session ID in response
result["session_id"] = session_id
```

## Technical Decisions

### Framework Choice: FastMCP 2.0
**Why**: Modern, simplified MCP server framework
**Benefits**:
- 90% less boilerplate code than legacy MCP implementations
- Automatic schema generation and validation
- Built-in async support and error handling
- Decorator-based tool registration

### API Client Pattern: Singleton with Lazy Loading
**Why**: Efficient resource management
**Implementation**:
```python
_greptile_client: Optional[GreptileClient] = None

async def get_greptile_client() -> GreptileClient:
    global _greptile_client
    if _greptile_client is None:
        _greptile_client = GreptileClient(...)
    return _greptile_client
```

### Response Format: JSON Strings
**Why**: MCP protocol compatibility and type safety
**Pattern**: All responses are JSON strings, parsed by clients as needed

### Environment Configuration: Fail-Fast Validation
**Why**: Clear error messages for missing configuration
**Pattern**:
```python
api_key = os.getenv("GREPTILE_API_KEY")
if not api_key:
    raise ValueError("GREPTILE_API_KEY environment variable is required")
```

## Component Relationships

### MCP Tools → GreptileClient Flow
1. **MCP Tool** receives request with simplified parameters
2. **Parameter Conversion** transforms MCP format to Greptile API format
3. **GreptileClient** makes HTTP request to Greptile API
4. **Response Processing** converts API response to MCP format
5. **Error Handling** ensures graceful failure with structured errors

### Session Management Flow
1. **Session Creation** generates UUID if not provided
2. **Context Preservation** maintains conversation history
3. **Response Augmentation** includes session ID in all responses
4. **Client Continuity** enables follow-up queries with context

### Deployment Architecture
```
Docker Container
├── Python 3.12 Runtime
├── FastMCP 2.0 Dependencies
├── Application Code
│   ├── src/main.py (MCP server)
│   └── src/utils.py (Greptile client)
├── Environment Variables
│   ├── GREPTILE_API_KEY
│   └── GITHUB_TOKEN
└── Health Check
    └── Server initialization validation
```

## Evolution Patterns

### Modernization Journey
1. **Legacy MCP** (May 2024) → **FastMCP 2.0** (Current)
2. **Complex Types** → **JSON String Parameters**
3. **Manual Validation** → **Automatic Schema Generation**
4. **Boilerplate Heavy** → **Decorator Driven**

### Lessons Learned
- Start with simple parameter types for MCP compatibility
- Validate environment configuration early
- Use JSON for complex data structures
- Implement comprehensive error handling
- Test with actual deployment platforms (Smithery)
- Avoid adding large test suites that can break deployment builds
- Keep Docker context minimal for faster builds
