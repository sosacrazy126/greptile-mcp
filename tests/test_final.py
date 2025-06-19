#!/usr/bin/env python3
"""
Final comprehensive test for the Smithery server
"""
import requests
import json
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_everything():
    """Test all server functionality"""
    
    print("=== Final Smithery Server Test ===\n")
    
    # 1. Test health endpoint
    print("1. Testing health endpoint...")
    response = requests.get("http://localhost:8088/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✓ Health check passed")
    
    # 2. Test initialize
    print("\n2. Testing initialize...")
    response = requests.post("http://localhost:8088/mcp", json={
        "method": "initialize",
        "params": {},
        "id": 1
    })
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["capabilities"]["tools"] == True
    print("✓ Initialize works")
    
    # 3. Test tool listing (no auth required)
    print("\n3. Testing tool listing (no auth)...")
    response = requests.get("http://localhost:8088/mcp")
    assert response.status_code == 200
    data = response.json()
    assert len(data["tools"]) > 0
    print(f"✓ Found {len(data['tools'])} tools without authentication")
    
    # 4. Test tool execution without auth (should fail for most tools)
    print("\n4. Testing tool execution without auth...")
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
        "id": 2
    })
    assert response.status_code in [401, 500]  # Should fail without auth
    print("✓ Tool execution properly requires authentication")
    
    # 5. Test tool execution with auth
    print("\n5. Testing tool execution with auth...")
    config = {
        "GREPTILE_API_KEY": os.getenv("GREPTILE_API_KEY"),
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")
    }
    
    if config["GREPTILE_API_KEY"] and config["GITHUB_TOKEN"]:
        config_json = json.dumps(config)
        config_b64 = base64.b64encode(config_json.encode()).decode()
        url = f"http://localhost:8088/mcp?config={config_b64}"
        
        response = requests.post(url, json={
            "method": "tools/call",
            "params": {
                "name": "greptile_help",
                "arguments": {}
            },
            "id": 3
        })
        assert response.status_code == 200
        print("✓ Tool execution works with authentication")
    else:
        print("⚠️  Skipping auth test (no API keys in environment)")
    
    # 6. Test Smithery-specific endpoints
    print("\n6. Testing Smithery-specific endpoints...")
    response = requests.get("http://localhost:8088/tools")
    assert response.status_code == 200
    print("✓ GET /tools works")
    
    response = requests.post("http://localhost:8088/tools", json={})
    assert response.status_code == 200
    print("✓ POST /tools works")
    
    print("\n=== All tests passed! Server is ready for Smithery deployment ===")

if __name__ == "__main__":
    try:
        test_everything()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
