#!/usr/bin/env python3
"""
Test what Smithery might be sending when scanning for tools
"""
import requests
import json

print("Testing various ways Smithery might scan for tools...")

# 1. Simple GET request
print("\n1. GET /mcp")
response = requests.get("http://localhost:8088/mcp")
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}...")

# 2. POST with no method (might be testing connection)
print("\n2. POST /mcp with empty body")
try:
    response = requests.post("http://localhost:8088/mcp", json={})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
except Exception as e:
    print(f"Error: {e}")

# 3. POST with tools/list method
print("\n3. POST /mcp with tools/list")
response = requests.post("http://localhost:8088/mcp", json={
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
})
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}...")

# 4. POST with no jsonrpc field (what error suggests)
print("\n4. POST /mcp without jsonrpc field")
response = requests.post("http://localhost:8088/mcp", json={
    "method": "tools/list",
    "id": 1
})
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}...")

# 5. POST with initialize but no jsonrpc
print("\n5. POST /mcp initialize without jsonrpc")
response = requests.post("http://localhost:8088/mcp", json={
    "method": "initialize",
    "params": {},
    "id": 1
})
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}...")
