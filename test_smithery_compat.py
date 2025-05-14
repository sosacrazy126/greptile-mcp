#!/usr/bin/env python3
"""
Test Smithery compatibility
"""
import requests
import json

# 1. Test with no JSON-RPC fields (HTTP interface)
print("1. Testing HTTP interface compatibility...")
response = requests.get("http://localhost:8088/mcp")
print(f"GET /mcp status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Found {len(data.get('tools', []))} tools")
else:
    print(f"Error: {response.text}")

# 2. Test JSON-RPC initialize
print("\n2. Testing JSON-RPC initialize...")
response = requests.post("http://localhost:8088/mcp", json={
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {},
    "id": 1
})
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# 3. Test JSON-RPC tools/list
print("\n3. Testing JSON-RPC tools/list...")
response = requests.post("http://localhost:8088/mcp", json={
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 2
})
print(f"Status: {response.status_code}")
data = response.json()
print(f"Response format: jsonrpc={data.get('jsonrpc')}, has_id={('id' in data)}, has_result={('result' in data)}")
if 'result' in data and 'tools' in data['result']:
    print(f"Found {len(data['result']['tools'])} tools")
