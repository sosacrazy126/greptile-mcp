#!/usr/bin/env python3
"""
Test a specific tool execution to see the exact error
"""
import requests
import json
import base64
import os

def test_get_repository_info():
    """Test get_repository_info with proper auth"""
    
    # Use real API keys from environment
    config = {
        "GREPTILE_API_KEY": os.getenv("GREPTILE_API_KEY", "fake_key"),
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", "fake_token")
    }
    config_json = json.dumps(config)
    config_b64 = base64.b64encode(config_json.encode()).decode()
    
    url = f"http://localhost:8088/mcp?config={config_b64}"
    
    # First, let's test a simple tool
    print("Testing greptile_help first...")
    response = requests.post(url, json={
        "method": "tools/call",
        "params": {
            "name": "greptile_help",
            "arguments": {}
        },
        "id": 1
    })
    
    print(f"Help response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if "result" in data:
            print("✓ Help tool works")
            # Print just the first 100 chars of the result
            result_text = str(data["result"])[:100] + "..."
            print(f"  Result preview: {result_text}")
    else:
        print(f"Error: {response.text}")
    
    print("\nNow testing get_repository_info...")
    response = requests.post(url, json={
        "method": "tools/call",
        "params": {
            "name": "get_repository_info",
            "arguments": {
                "remote": "github",
                "repository": "facebook/react",
                "branch": "main"
            }
        },
        "id": 2
    })
    
    print(f"Repository info response: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_get_repository_info()
