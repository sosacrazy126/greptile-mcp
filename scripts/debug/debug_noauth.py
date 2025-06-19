#!/usr/bin/env python3
"""
Debug tool execution without auth
"""
import requests
import json

response = requests.post("http://localhost:8088/mcp", json={
    "method": "tools/call",
    "params": {
        "name": "index_repository",
        "arguments": {
            "remote": "github",
            "repository": "test/test",
            "branch": "main"
        }
    },
    "id": 1
})

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
