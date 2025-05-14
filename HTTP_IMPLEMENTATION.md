# HTTP Transport Implementation Plan

## Quick Steps to Add HTTP Support

### 1. Install Dependencies

```bash
pip install uvicorn fastapi
```

### 2. Add HTTP Handler

Create `src/http_transport.py`:

```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import base64
import json
import os

app = FastAPI()

@app.post("/mcp")
async def handle_mcp(request: Request):
    """Handle MCP requests for Smithery"""
    # Get config from query params
    config = request.query_params.get("config")
    
    if config:
        # Decode base64 config
        config_json = json.loads(base64.b64decode(config))
        # Set environment variables from config
        for key, value in config_json.items():
            os.environ[key] = value
    
    # Handle the MCP request
    body = await request.body()
    
    # Process with MCP server
    # This is where we'd integrate with the existing MCP server
    # For now, return a placeholder response
    
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 3. Update Main

```python
# Add to src/main.py
async def run_http():
    """Run with HTTP transport for Smithery"""
    import uvicorn
    from src.http_transport import app
    
    # Mount the MCP server to the FastAPI app
    app.mcp_server = mcp
    
    await uvicorn.run(app, host="0.0.0.0", port=8080)
```

### 4. Test Locally

```bash
# Set transport to HTTP
export TRANSPORT=http

# Run the server
python src/main.py
```

### 5. Deploy to Smithery

1. Push changes
2. Add server on Smithery
3. Deploy

## Timeline

- [ ] Implement HTTP transport (2 hours)
- [ ] Add lazy authentication (1 hour)
- [ ] Test locally (1 hour)
- [ ] Deploy to Smithery (30 min)

Total: ~4.5 hours
