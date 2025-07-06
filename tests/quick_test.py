#!/usr/bin/env python3
"""
Quick Test Runner - Validate Core Fixes
Tests the most critical fixes to ensure Smithery compatibility.
"""

import sys
import os
import json

# Change to project root and add to path
project_root = os.path.join(os.path.dirname(__file__), '..')
os.chdir(project_root)
sys.path.insert(0, '.')

def test_imports():
    """Test that all imports work correctly."""
    try:
        from src.main import mcp, query_repository, search_repository, index_repository, get_repository_info
        from src.utils import GreptileClient
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_parameter_types():
    """Test that parameter types are simplified."""
    try:
        import inspect
        from src.main import query_repository, search_repository

        # FastMCP 2.0 creates FunctionTool objects, get the actual function
        if hasattr(query_repository, 'fn'):
            actual_func = query_repository.fn
        else:
            actual_func = query_repository

        # Check query_repository parameters
        sig = inspect.signature(actual_func)
        params = sig.parameters

        # Verify simplified types
        assert params['query'].annotation == str
        assert params['repositories'].annotation == str
        assert sig.return_annotation == str

        print("✅ Parameter types are simplified (FastMCP compatible)")
        return True
    except Exception as e:
        print(f"❌ Parameter type test failed: {e}")
        return False

def test_json_handling():
    """Test JSON parameter handling."""
    try:
        # Test valid JSON parsing
        repositories_json = '[{"remote": "github", "repository": "test/repo", "branch": "main"}]'
        repositories = json.loads(repositories_json)
        assert isinstance(repositories, list)
        assert len(repositories) == 1
        
        # Test invalid JSON handling
        try:
            json.loads('{"invalid": json}')
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError:
            pass  # Expected
        
        print("✅ JSON parameter handling works correctly")
        return True
    except Exception as e:
        print(f"❌ JSON handling test failed: {e}")
        return False

async def test_parameter_mapping():
    """Test parameter mapping from MCP tools to GreptileClient."""
    try:
        from unittest.mock import AsyncMock, patch
        from src.main import query_repository

        # Set environment variables to avoid initialization errors
        os.environ['GREPTILE_API_KEY'] = 'test_key'
        os.environ['GITHUB_TOKEN'] = 'test_token'

        # Get the actual function from FastMCP FunctionTool
        if hasattr(query_repository, 'fn'):
            actual_func = query_repository.fn
        else:
            actual_func = query_repository

        with patch('src.main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.query_repositories.return_value = {"message": "test response"}
            mock_get_client.return_value = mock_client

            result = await actual_func(
                query="test query",
                repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]'
            )
            
            # Verify client was called with messages parameter
            call_args = mock_client.query_repositories.call_args
            assert 'messages' in call_args.kwargs
            messages = call_args.kwargs['messages']
            assert messages[0]['content'] == "test query"
            
            # Verify result is JSON string
            result_dict = json.loads(result)
            assert 'message' in result_dict
            
        print("✅ Parameter mapping works correctly")
        return True
    except Exception as e:
        print(f"❌ Parameter mapping test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_server_initialization():
    """Test that FastMCP server initializes without errors."""
    try:
        from src.main import mcp
        assert mcp is not None
        assert mcp.name == "Greptile MCP Server"
        print("✅ FastMCP server initializes correctly")
        return True
    except Exception as e:
        print(f"❌ Server initialization failed: {e}")
        return False

async def test_error_handling():
    """Test error handling with invalid JSON."""
    try:
        from src.main import query_repository

        # Set environment variables to avoid initialization errors
        os.environ['GREPTILE_API_KEY'] = 'test_key'
        os.environ['GITHUB_TOKEN'] = 'test_token'

        # Get the actual function from FastMCP FunctionTool
        if hasattr(query_repository, 'fn'):
            actual_func = query_repository.fn
        else:
            actual_func = query_repository

        result = await actual_func(
            query="test",
            repositories='{"invalid": json}'
        )
        
        result_dict = json.loads(result)
        assert 'error' in result_dict
        assert 'JSONDecodeError' in result_dict['error']
        
        print("✅ Error handling works correctly")
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

async def main():
    """Run quick validation tests."""
    print("🧪 Running Quick Validation Tests")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports, False),
        ("Parameter Types", test_parameter_types, False),
        ("JSON Handling", test_json_handling, False),
        ("Server Initialization", test_server_initialization, False),
        ("Parameter Mapping", test_parameter_mapping, True),
        ("Error Handling", test_error_handling, True)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func, is_async in tests:
        try:
            if is_async:
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All critical fixes validated!")
        print("✅ Smithery deployment should work correctly")
        print("✅ MCP error -32602 resolved")
        print("✅ Parameter mapping fixed")
    else:
        print("❌ Some critical issues remain")
    
    return passed == total

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
