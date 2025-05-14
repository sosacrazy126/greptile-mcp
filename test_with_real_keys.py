#!/usr/bin/env python3
"""
Test with real API keys from .env file
"""
import requests
import json
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_with_real_keys():
    """Test with real API keys"""
    
    # Use real API keys from environment
    config = {
        "GREPTILE_API_KEY": os.getenv("GREPTILE_API_KEY"),
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")
    }
    
    if not config["GREPTILE_API_KEY"] or not config["GITHUB_TOKEN"]:
        print("Error: API keys not found in environment")
        return
    
    config_json = json.dumps(config)
    config_b64 = base64.b64encode(config_json.encode()).decode()
    
    url = f"http://localhost:8088/mcp?config={config_b64}"
    
    print("Testing get_repository_info with real keys...")
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
        "id": 1
    })
    
    print(f"Response status: {response.status_code}")
    data = response.json()
    
    if response.status_code == 200:
        result = data.get("result", [])
        if isinstance(result, list) and len(result) > 0:
            text = result[0].get("text", "")
            if "Error" in text:
                print(f"Error in result: {text}")
            else:
                print("✓ Successfully got repository info!")
                print(f"Result: {text[:200]}...")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_with_real_keys()
