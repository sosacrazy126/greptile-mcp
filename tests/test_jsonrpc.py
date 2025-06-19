#!/usr/bin/env python3
"""
Test JSON-RPC 2.0 format for Smithery
"""
import requests
import json
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_jsonrpc_format():
    """Test that all responses follow JSON-RPC 2.0 format"""
    
    print("=== Testing JSON-RPC 2.0 Format ===\n")
    
    # 1. Test initialize
    print("1. Testing initialize...")
    response = requests.post("http://localhost:8088/mcp", json={
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {},
        "id": 1
    })
    data = response.json()
    assert data.get("jsonrpc") == "2.0", "Missing jsonrpc version"
    assert "id" in data, "Missing id field"
    assert "result" in data, "Missing result field"
    print("✓ Initialize returns proper JSON-RPC format")
    
    # 2. Test tools/list
    print("\n2. Testing tools/list...")
    response = requests.post("http://localhost:8088/mcp", json={
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    })
    data = response.json()
    assert data.get("jsonrpc") == "2.0", "Missing jsonrpc version"
    assert data.get("id") == 2, "Wrong id"
    assert "result" in data, "Missing result field"
    print("✓ tools/list returns proper JSON-RPC format")
    
    # 3. Test error format (unsupported method)
    print("\n3. Testing error format...")
    response = requests.post("http://localhost:8088/mcp", json={
        "jsonrpc": "2.0",
        "method": "unsupported/method",
        "params": {},
        "id": 3
    })
    data = response.json()
    assert data.get("jsonrpc") == "2.0", "Missing jsonrpc version"
    assert data.get("id") == 3, "Wrong id"
    assert "error" in data, "Missing error field"
    assert "code" in data["error"], "Missing error code"
    assert "message" in data["error"], "Missing error message"
    print("✓ Error returns proper JSON-RPC format")
    
    # 4. Test tool execution error (no auth)
    print("\n4. Testing tool execution error...")
    response = requests.post("http://localhost:8088/mcp", json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "index_repository",
            "arguments": {
                "remote": "github",
                "repository": "test/test",
                "branch": "main"
            }
        },
        "id": 4
    })
    data = response.json()
    assert data.get("jsonrpc") == "2.0", "Missing jsonrpc version"
    assert data.get("id") == 4, "Wrong id"
    # Should have either result with error text or error field
    assert "result" in data or "error" in data, "Missing result or error"
    print("✓ Tool execution error returns proper JSON-RPC format")
    
    # 5. Test successful tool call (with auth)
    print("\n5. Testing successful tool call...")
    config = {
        "GREPTILE_API_KEY": os.getenv("GREPTILE_API_KEY"),
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")
    }
    
    if config["GREPTILE_API_KEY"] and config["GITHUB_TOKEN"]:
        config_json = json.dumps(config)
        config_b64 = base64.b64encode(config_json.encode()).decode()
        url = f"http://localhost:8088/mcp?config={config_b64}"
        
        response = requests.post(url, json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "greptile_help",
                "arguments": {}
            },
            "id": 5
        })
        data = response.json()
        assert data.get("jsonrpc") == "2.0", "Missing jsonrpc version"
        assert data.get("id") == 5, "Wrong id"
        assert "result" in data, "Missing result field"
        print("✓ Successful tool call returns proper JSON-RPC format")
    else:
        print("⚠️  Skipping auth test (no API keys in environment)")
    
    print("\n=== All JSON-RPC tests passed! ===")

if __name__ == "__main__":
    test_jsonrpc_format()
