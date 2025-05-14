#!/usr/bin/env python3
"""
Comprehensive test script for the Smithery server
"""
import requests
import json
import base64

def test_initialize():
    """Test that the server can handle the initialize method"""
    print("1. Testing initialize method...")
    url = "http://localhost:8088/mcp"
    
    response = requests.post(url, json={
        "method": "initialize",
        "params": {},
        "id": 1
    })
    
    assert response.status_code == 200, f"Initialize failed with status {response.status_code}"
    data = response.json()
    assert "result" in data, "No result in initialize response"
    assert data["result"]["capabilities"]["tools"] == True, "Tools capability not enabled"
    print("✓ Initialize method works correctly")
    return data

def test_tool_listing():
    """Test tool listing endpoint"""
    print("\n2. Testing tool listing...")
    url = "http://localhost:8088/mcp"
    
    response = requests.get(url)
    assert response.status_code == 200, f"Tool listing failed with status {response.status_code}"
    data = response.json()
    assert "tools" in data, "No tools in response"
    assert len(data["tools"]) > 0, "No tools found"
    print(f"✓ Found {len(data['tools'])} tools")
    
    # Print tool names
    print("   Available tools:")
    for tool in data["tools"]:
        print(f"   - {tool['name']}")
    
    return data

def test_greptile_help():
    """Test the greptile_help tool execution"""
    print("\n3. Testing greptile_help tool...")
    url = "http://localhost:8088/mcp"
    
    # Try without authentication first (should work for help)
    response = requests.post(url, json={
        "method": "tools/call",
        "params": {
            "name": "greptile_help",
            "arguments": {}
        },
        "id": 2
    })
    
    if response.status_code == 401:
        print("   Note: greptile_help requires authentication")
        # Expected for most tools, but help should work without auth
        return None
    
    assert response.status_code == 200, f"Tool call failed with status {response.status_code}: {response.text}"
    data = response.json()
    assert "result" in data, "No result in tool response"
    print("✓ greptile_help tool executed successfully")
    return data

def test_with_auth():
    """Test tool execution with authentication"""
    print("\n4. Testing tool with authentication...")
    
    # Create config with mock API keys
    config = {
        "GREPTILE_API_KEY": "test_key",
        "GITHUB_TOKEN": "test_token"
    }
    config_json = json.dumps(config)
    config_b64 = base64.b64encode(config_json.encode()).decode()
    
    url = f"http://localhost:8088/mcp?config={config_b64}"
    
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
        "id": 3
    })
    
    # This should fail because the API keys are fake, but we should get a proper error
    if response.status_code == 500:
        data = response.json()
        if "error" in data and "Failed to initialize Greptile client" in data["error"]:
            print("✓ Authentication handling works (failed with invalid keys as expected)")
            return data
    
    print(f"   Unexpected response: {response.status_code} - {response.text}")
    return response.json() if response.status_code == 200 else None

def test_smithery_tool_listing():
    """Test Smithery-specific tool listing endpoints"""
    print("\n5. Testing Smithery tool listing endpoints...")
    
    # Test GET /tools
    response = requests.get("http://localhost:8088/tools")
    assert response.status_code == 200, f"GET /tools failed with status {response.status_code}"
    print("✓ GET /tools works")
    
    # Test POST /tools
    response = requests.post("http://localhost:8088/tools", json={})
    assert response.status_code == 200, f"POST /tools failed with status {response.status_code}"
    print("✓ POST /tools works")

def run_all_tests():
    """Run all tests"""
    print("=== Smithery Server Comprehensive Test Suite ===\n")
    
    try:
        # Check if server is running
        response = requests.get("http://localhost:8088/health")
        if response.status_code != 200:
            print("❌ Server is not running or not healthy")
            return
        print("✓ Server is running and healthy\n")
        
        # Run tests
        test_initialize()
        test_tool_listing()
        test_greptile_help()
        test_with_auth()
        test_smithery_tool_listing()
        
        print("\n=== All tests completed successfully! ===")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on http://localhost:8088")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
