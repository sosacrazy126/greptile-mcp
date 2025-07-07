# LOCAL USAGE GUIDE

This server supports both event-stream and HTTP/JSON-RPC modes.

## HTTP Mode (Smithery/FastAPI)

- The HTTP JSON-RPC endpoint is available at: `http://localhost:8080/json-rpc`
- Default port: **8080**
- Example cURL usage:

```bash
curl -X POST http://localhost:8080/json-rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"query_repository","params":{"query":"How is authentication handled?","repositories":"[{\"remote\":\"github\",\"repository\":\"owner/repo\",\"branch\":\"main\"}]"}}'
```

## Event-Stream Mode

- Old event-stream (SSE) endpoint defaults to port: **8050**
- Example: `python -m src.main` or via Docker as described in README.

## Environment Variables

Make sure to set:
- `GREPTILE_API_KEY`
- `GITHUB_TOKEN`

## Docker

To run HTTP mode in Docker:
```bash
docker build -f Dockerfile.smithery -t greptile-mcp-http .
docker run --rm -e GREPTILE_API_KEY=your_key -e GITHUB_TOKEN=your_token -p 8080:8080 greptile-mcp-http
```