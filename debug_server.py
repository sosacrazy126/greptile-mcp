#!/usr/bin/env python3
"""
Create a test server to see what Smithery CLI actually sends
"""
from fastapi import FastAPI, Request
import uvicorn
import json

app = FastAPI()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def catch_all(request: Request, path: str):
    """Catch all routes to see what Smithery sends"""
    
    # Get request details
    method = request.method
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    
    # Get body if present
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except:
            body = await request.body()
            if body:
                body = body.decode()
    
    # Log the request
    print(f"\n=== Request to: {method} /{path} ===")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Query params: {json.dumps(query_params, indent=2)}")
    if body:
        print(f"Body: {json.dumps(body, indent=2) if isinstance(body, dict) else body}")
    print("=" * 40)
    
    # Return a mock response based on the path
    if path == "mcp" and method == "POST":
        if body and body.get("method") == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {
                    "protocolVersion": "0.1.0",
                    "capabilities": {
                        "tools": True,
                        "resources": False
                    },
                    "serverInfo": {
                        "name": "test-mcp",
                        "version": "1.0.0"
                    }
                }
            }
    
    return {"status": "ok", "path": path, "method": method}

if __name__ == "__main__":
    print("Starting debug server on port 8089...")
    uvicorn.run(app, host="0.0.0.0", port=8089)
