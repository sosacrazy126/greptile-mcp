# 🌐 HTTP/JSON-RPC Usage Guide

## 📋 Overview

The Greptile MCP server now supports **dual-mode operation**: traditional MCP protocol for direct client integration and HTTP/JSON-RPC 2.0 for web applications and REST clients.

## 🚀 Quick Start

### 1. Start HTTP Server

```bash
# Production mode
python -m src.main_http

# Development mode (with auto-reload)
python -m src.main_http --dev
```

### 2. Verify Server is Running

```bash
# Health check
curl http://localhost:8080/health

# API information
curl http://localhost:8080/

# Interactive documentation
open http://localhost:8080/docs
```

### 3. Your First Request

```bash
curl -X POST http://localhost:8080/json-rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "greptile_help",
    "id": "1"
  }'
```

## 🎯 Available Methods

| Method | Description | Required Parameters |
|--------|-------------|-------------------|
| `greptile_help` | Get help and available methods | None |
| `index_repository` | Index a repository for searching | `remote`, `repository`, `branch` |
| `query_repository` | Query repositories with natural language | `query`, `repositories` |
| `search_repository` | Search for relevant files | `query`, `repositories` |
| `get_repository_info` | Get repository indexing status | `remote`, `repository`, `branch` |

## 📚 Detailed Method Documentation

### `index_repository`

Indexes a repository to make it searchable.

**Parameters:**
- `remote` (string, required): "github" or "gitlab"
- `repository` (string, required): "owner/repo" format
- `branch` (string, required): Branch to index
- `reload` (boolean, optional): Force re-indexing, default: true
- `notify` (boolean, optional): Email notification, default: false

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "index_repository",
  "params": {
    "remote": "github",
    "repository": "facebook/react",
    "branch": "main",
    "reload": true
  },
  "id": "index-1"
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "message": "Indexing Job Submitted for: facebook/react",
    "statusEndpoint": "https://api.greptile.com/v2/repositories/..."
  },
  "id": "index-1"
}
```

### `query_repository`

Query repositories with natural language.

**Parameters:**
- `query` (string, required): Natural language question
- `repositories` (array, required): List of repository objects
- `session_id` (string, optional): For conversation continuity
- `genius` (boolean, optional): Enhanced mode, default: true
- `stream` (boolean, optional): Stream response, default: false

**Repository Object Format:**
```json
{
  "remote": "github",
  "repository": "owner/repo",
  "branch": "main"
}
```

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "query_repository",
  "params": {
    "query": "How does useState work in React?",
    "repositories": [
      {
        "remote": "github",
        "repository": "facebook/react",
        "branch": "main"
      }
    ],
    "genius": true
  },
  "id": "query-1"
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "message": "useState is a React Hook that lets you add state to functional components...",
    "sources": [
      {
        "repository": "facebook/react",
        "filepath": "packages/react/src/ReactHooks.js",
        "linestart": 45,
        "lineend": 67,
        "summary": "useState implementation"
      }
    ],
    "_session_id": "generated-uuid"
  },
  "id": "query-1"
}
```

### `search_repository`

Search for relevant files without generating a full answer.

**Parameters:**
- `query` (string, required): Search query
- `repositories` (array, required): List of repository objects
- `session_id` (string, optional): For conversation continuity
- `genius` (boolean, optional): Enhanced mode, default: true

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "search_repository",
  "params": {
    "query": "authentication middleware",
    "repositories": [
      {
        "remote": "github",
        "repository": "expressjs/express",
        "branch": "master"
      }
    ]
  },
  "id": "search-1"
}
```

### `get_repository_info`

Get information about an indexed repository.

**Parameters:**
- `remote` (string, required): "github" or "gitlab"
- `repository` (string, required): "owner/repo" format
- `branch` (string, required): Branch name

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_repository_info",
  "params": {
    "remote": "github",
    "repository": "facebook/react",
    "branch": "main"
  },
  "id": "info-1"
}
```

## 🔄 Session Management

For multi-turn conversations, use session IDs to maintain context:

### Basic Session Flow

```javascript
// 1. Initial query (no session_id)
const response1 = await fetch('http://localhost:8080/json-rpc', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'query_repository',
    params: {
      query: 'How does authentication work?',
      repositories: [/* repositories */]
    },
    id: '1'
  })
});

const result1 = await response1.json();
const sessionId = result1.result._session_id;

// 2. Follow-up query (use session_id)
const response2 = await fetch('http://localhost:8080/json-rpc', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'query_repository',
    params: {
      query: 'What about password reset?',
      repositories: [/* same repositories */],
      session_id: sessionId  // Maintains context
    },
    id: '2'
  })
});
```

## 🛡️ Security & Rate Limiting

### Rate Limiting

- **Limit**: 100 requests per hour per IP address
- **Window**: 1 hour rolling window
- **Response**: HTTP 429 when exceeded

### Authentication (Optional)

The server supports optional API key authentication:

```bash
curl -X POST http://localhost:8080/json-rpc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{"jsonrpc": "2.0", "method": "greptile_help", "id": "1"}'
```

## 🔧 Error Handling

### JSON-RPC Error Codes

| Code | Name | Description |
|------|------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid Request | Invalid JSON-RPC |
| -32601 | Method not found | Method doesn't exist |
| -32602 | Invalid params | Invalid parameters |
| -32603 | Internal error | Server error |
| -32001 | Rate limit exceeded | Too many requests |

### Error Response Format

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": "Missing required parameter: repository"
  },
  "id": "1"
}
```

### Common Error Scenarios

#### Missing Required Parameters
```json
{
  "jsonrpc": "2.0",
  "method": "index_repository",
  "params": {
    "remote": "github"
    // Missing 'repository' and 'branch'
  },
  "id": "1"
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": "Missing required parameter: repository"
  },
  "id": "1"
}
```

#### Invalid Repository Format
```json
{
  "jsonrpc": "2.0",
  "method": "query_repository",
  "params": {
    "query": "test",
    "repositories": "not-an-array"  // Should be array
  },
  "id": "1"
}
```

## 🌍 Integration Examples

### React/Next.js Application

```jsx
// hooks/useGreptile.js
import { useState, useCallback } from 'react';

const GREPTILE_API_URL = 'http://localhost:8080/json-rpc';

export function useGreptile() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const callMethod = useCallback(async (method, params) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(GREPTILE_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method,
          params,
          id: Date.now().toString(),
        }),
      });

      const result = await response.json();

      if (result.error) {
        throw new Error(result.error.message);
      }

      return result.result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { callMethod, loading, error };
}

// components/CodeQuery.jsx
export function CodeQuery() {
  const { callMethod, loading, error } = useGreptile();
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);

  const handleQuery = async () => {
    try {
      const result = await callMethod('query_repository', {
        query,
        repositories: [
          {
            remote: 'github',
            repository: 'facebook/react',
            branch: 'main'
          }
        ]
      });
      setResult(result);
    } catch (err) {
      console.error('Query failed:', err);
    }
  };

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask about the code..."
      />
      <button onClick={handleQuery} disabled={loading}>
        {loading ? 'Querying...' : 'Query'}
      </button>
      {error && <div>Error: {error}</div>}
      {result && (
        <div>
          <h3>Result:</h3>
          <p>{result.message}</p>
          {result.sources && (
            <div>
              <h4>Sources:</h4>
              {result.sources.map((source, i) => (
                <div key={i}>
                  {source.filepath}:{source.linestart}-{source.lineend}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

### Express.js Middleware

```javascript
// middleware/greptile.js
const axios = require('axios');

const GREPTILE_API_URL = 'http://localhost:8080/json-rpc';

class GreptileClient {
  async callMethod(method, params) {
    try {
      const response = await axios.post(GREPTILE_API_URL, {
        jsonrpc: '2.0',
        method,
        params,
        id: Date.now().toString(),
      });

      if (response.data.error) {
        throw new Error(response.data.error.message);
      }

      return response.data.result;
    } catch (error) {
      console.error('Greptile API error:', error);
      throw error;
    }
  }

  async indexRepository(remote, repository, branch, options = {}) {
    return this.callMethod('index_repository', {
      remote,
      repository,
      branch,
      ...options
    });
  }

  async queryRepository(query, repositories, options = {}) {
    return this.callMethod('query_repository', {
      query,
      repositories,
      ...options
    });
  }
}

module.exports = new GreptileClient();

// routes/api.js
const express = require('express');
const greptile = require('../middleware/greptile');

const router = express.Router();

router.post('/code/query', async (req, res) => {
  try {
    const { query, repositories } = req.body;
    
    const result = await greptile.queryRepository(query, repositories);
    
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ 
      success: false, 
      error: error.message 
    });
  }
});

module.exports = router;
```

## 📊 Monitoring & Debugging

### Health Check

```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "service": "greptile-mcp-http",
  "version": "1.0.0",
  "timestamp": 1704067200
}
```

### API Documentation

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **Method docs**: http://localhost:8080/api/methods

### Logging

The server provides detailed logs for debugging:

```
📨 JSON-RPC request: query_repository from 127.0.0.1
✅ JSON-RPC response: query_repository completed in 2.34s
```

## 🔄 Migration from MCP Mode

### Dual Mode Operation

You can run both modes simultaneously on different ports:

```bash
# Terminal 1: MCP mode
python -m src.main

# Terminal 2: HTTP mode  
python -m src.main_http
```

### Choosing the Right Mode

| Use Case | Recommended Mode |
|----------|------------------|
| Claude Desktop, Cursor | MCP Mode |
| Web applications | HTTP Mode |
| REST API integration | HTTP Mode |
| Mobile applications | HTTP Mode |
| Scripting/automation | Either mode |

### Configuration Comparison

| Aspect | MCP Mode | HTTP Mode |
|--------|----------|-----------|
| Port | 8050 | 8080 |
| Protocol | stdio/SSE | HTTP/JSON-RPC |
| Authentication | Environment | Optional API key |
| Documentation | None | Swagger/ReDoc |
| Rate limiting | None | 100/hour |
| CORS | N/A | Enabled |

## 🚀 Production Deployment

### Docker Deployment

```dockerfile
# Dockerfile.http
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY .env .env

EXPOSE 8080

CMD ["python", "-m", "src.main_http"]
```

```bash
# Build and run
docker build -f Dockerfile.http -t greptile-mcp-http .
docker run -p 8080:8080 \
  -e GREPTILE_API_KEY=your_key \
  -e GITHUB_TOKEN=your_token \
  greptile-mcp-http
```

### Load Balancing

For high availability, deploy multiple instances behind a load balancer:

```yaml
# docker-compose.yml
version: '3.8'
services:
  greptile-http-1:
    build:
      context: .
      dockerfile: Dockerfile.http
    environment:
      - GREPTILE_API_KEY=${GREPTILE_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - PORT=8080
    ports:
      - "8081:8080"

  greptile-http-2:
    build:
      context: .
      dockerfile: Dockerfile.http
    environment:
      - GREPTILE_API_KEY=${GREPTILE_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - PORT=8080
    ports:
      - "8082:8080"

  nginx:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

## 📋 Best Practices

### 1. Session Management
- Generate unique session IDs for each conversation
- Reuse session IDs for follow-up questions
- Clear sessions when conversations end

### 2. Error Handling
- Always check for JSON-RPC errors in responses
- Implement exponential backoff for rate limiting
- Log errors for debugging

### 3. Performance
- Index repositories once, query many times
- Use specific queries for better results
- Monitor response times and optimize

### 4. Security
- Use HTTPS in production
- Implement proper API key validation
- Configure CORS appropriately
- Monitor rate limiting logs

## 🎉 Conclusion

The HTTP/JSON-RPC mode provides a modern, web-friendly interface to Greptile MCP tools while maintaining full compatibility with the existing MCP protocol. This dual-mode approach ensures flexibility for various integration scenarios while preserving backward compatibility.

For questions or issues, please refer to the main documentation or create an issue in the repository.