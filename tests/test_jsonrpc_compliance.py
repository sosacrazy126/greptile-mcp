#!/usr/bin/env python3
"""
Test all response formats are JSON-RPC compliant
"""
import requests
import json

print("Testing JSON-RPC compliance for all endpoints...")

tests = [
    ("GET /mcp", "get", "http://localhost:8088/mcp", None),
    ("GET /mcp?id=123", "get", "http://localhost:8088/mcp?id=123", None),
    ("POST /mcp (empty)", "post", "http://localhost:8088/mcp", {}),
    ("POST /mcp (no method)", "post", "http://localhost:8088/mcp", {"id": 1}),
    ("POST /mcp (initialize)", "post", "http://localhost:8088/mcp", {
        "method": "initialize",
        "params": {},
        "id": 2
    }),
    ("POST /mcp (tools/list)", "post", "http://localhost:8088/mcp", {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 3
    }),
]

for name, method, url, data in tests:
    print(f"\n{name}")
    try:
        if method == "get":
            response = requests.get(url)
        else:
            response = requests.post(url, json=data)
        
        print(f"Status: {response.status_code}")
        resp_data = response.json()
        
        # Check for jsonrpc field
        has_jsonrpc = "jsonrpc" in resp_data
        jsonrpc_value = resp_data.get("jsonrpc")
        has_result_or_error = "result" in resp_data or "error" in resp_data
        
        print(f"Has jsonrpc: {has_jsonrpc} (value: {jsonrpc_value})")
        print(f"Has result or error: {has_result_or_error}")
        
        if not has_jsonrpc or jsonrpc_value != "2.0":
            print("❌ NOT JSON-RPC compliant!")
        else:
            print("✓ JSON-RPC compliant")
            
    except Exception as e:
        print(f"Error: {e}")
