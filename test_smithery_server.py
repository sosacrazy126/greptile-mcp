#!/usr/bin/env python3
"""
Test script to verify the Smithery server handles initialize method
"""
import requests
import json

def test_initialize():
    """Test that the server can handle the initialize method"""
    url = "http://localhost:8088/mcp"
    
    try:
        # Test initialize method
        response = requests.post(url, json={
            "method": "initialize",
            "params": {},
            "id": 1
        })
        print(f"Initialize Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Initialize Response:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure it's running on http://localhost:8088")
    except Exception as e:
        print(f"Error: {e}")

def test_tool_listing():
    """Test tool listing endpoint"""
    url = "http://localhost:8088/mcp"
    
    try:
        response = requests.get(url)
        print(f"\nTool Listing Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Tool Listing Response:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing Greptile MCP Smithery server...")
    print("=" * 50)
    test_initialize()
    test_tool_listing()
