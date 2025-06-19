# Greptile MCP - User Guide

## Introduction
Greptile MCP provides a powerful integration between the Mission Control Protocol (MCP) system and the Greptile code search service. This guide will help you get started with using the Greptile MCP tools for repository indexing, querying, and searching.

## Getting Started

### Prerequisites
- Python 3.8 or higher
- MCP server installed and running
- Greptile API credentials

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/grep-mcp.git
   cd grep-mcp
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your Greptile API credentials:
   - Create a `.env` file based on `.env.example`
   - Add your Greptile API key to the `.env` file

## Basic Usage

### Indexing a Repository
To make a repository searchable, you first need to index it:

```python
from mcp.client import MCPClient

client = MCPClient()
result = client.call("mcp_greptile-mcp_index_repository", {
    "remote": "github",
    "repository": "owner/repo",
    "branch": "main"
})
print(f"Indexing started: {result}")
```

### Querying a Repository
Once indexed, you can query a repository with natural language:

```python
response = client.call("mcp_greptile-mcp_query_repository", {
    "query": "How does the authentication system work?",
    "repositories": [{"remote": "github", "repository": "owner/repo", "branch": "main"}],
    "genius": True  # Enable enhanced answer quality
})
print(f"Answer: {response}")
```

### Searching for Relevant Files
To find relevant files without generating a full answer:

```python
files = client.call("mcp_greptile-mcp_search_repository", {
    "query": "authentication implementation",
    "repositories": [{"remote": "github", "repository": "owner/repo", "branch": "main"}]
})
print(f"Relevant files: {files}")
```

### Getting Repository Info
To check the status of an indexed repository:

```python
info = client.call("mcp_greptile-mcp_get_repository_info", {
    "remote": "github",
    "repository": "owner/repo",
    "branch": "main"
})
print(f"Repository status: {info}")
```

## Advanced Features

### Streaming Support
For long-running queries, enable streaming to get results as they become available:

```python
response = client.call("mcp_greptile-mcp_query_repository", {
    "query": "Explain the entire authentication flow",
    "repositories": [{"remote": "github", "repository": "owner/repo", "branch": "main"}],
    "stream": True,  # Enable streaming
    "genius": True
})

# Process streaming response
for chunk in response:
    print(chunk)
```

### Caching
The system automatically caches frequent API calls to improve performance. Cache configurations can be adjusted in the settings file.

### Multi-Turn Conversations
Maintain context across multiple queries:

```python
session_id = "my-session-123"
response1 = client.call("mcp_greptile-mcp_query_repository", {
    "query": "How does authentication work?",
    "repositories": [{"remote": "github", "repository": "owner/repo", "branch": "main"}],
    "session_id": session_id
})

# Follow-up question using the same session
response2 = client.call("mcp_greptile-mcp_query_repository", {
    "query": "What about password reset?",
    "repositories": [{"remote": "github", "repository": "owner/repo", "branch": "main"}],
    "session_id": session_id
})
```

## Troubleshooting

### Common Issues
- **Rate Limiting**: If you see rate limit errors, the system will automatically retry with exponential backoff. You can adjust rate limit settings in the configuration.
- **Indexing Failures**: Ensure the repository exists and is accessible with your credentials.
- **Query Timeout**: For large repositories, try using the streaming option for long-running queries.

### Getting Help
Refer to the detailed API documentation and error code guide for more information on specific issues.