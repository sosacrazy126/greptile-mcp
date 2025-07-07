import os
import json
import traceback
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.responses import Response
from starlette.requests import Request as StarletteRequest
import uvicorn
import asyncio

from src.main import mcp

class Context:
    """
    Minimal context object for MCP tools. Can be extended as needed.
    """
    def __init__(self, user_id=None):
        self.user_id = user_id

app = FastAPI()

@app.post("/json-rpc")
async def json_rpc_endpoint(request: Request):
    # Check env vars at the very start
    if not os.getenv("GREPTILE_API_KEY") or not os.getenv("GITHUB_TOKEN"):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32000,
                    "message": "Missing required environment variable(s): GREPTILE_API_KEY and/or GITHUB_TOKEN"
                },
                "id": None,
            },
        )
    try:
        req_data = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Invalid JSON in request"
                },
                "id": None
            },
        )
    method = req_data.get("method")
    params = req_data.get("params", {})
    req_id = req_data.get("id")
    # Require correct jsonrpc version field
    if req_data.get("jsonrpc") != "2.0":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32600, "message": "Invalid JSON-RPC version"},
                "id": req_id
            },
        )
    # Call the mcp tool dynamically
    try:
        # Provide a minimal context object for compatibility
        ctx = Context()
        # Await the MCP tool call
        result = await mcp.call_tool(method, **params, context=ctx)
        return JSONResponse(
            status_code=200,
            content={
                "jsonrpc": "2.0",
                "result": result,
                "id": req_id
            },
        )
    except Exception as exc:
        tb = traceback.format_exc()
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32001,
                    "message": f"{type(exc).__name__}: {str(exc)}",
                    "data": tb
                },
                "id": req_id
            },
        )

if __name__ == "__main__":
    # HTTP server runs on port 8080 by default for Smithery
    uvicorn.run("src.smithery_server:app", host="0.0.0.0", port=8080, reload=False)