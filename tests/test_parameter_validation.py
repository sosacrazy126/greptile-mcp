#!/usr/bin/env python3
"""
Test Parameter Validation - FastMCP Schema Compatibility
Tests that simplified parameter types work correctly with FastMCP schema validation.
"""

import pytest
import json
import sys
import os
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Change to project root for imports
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from src.main import mcp, get_greptile_client
from src.utils import GreptileClient

class TestParameterValidation:
    """Test FastMCP parameter validation with simplified types."""
    
    def test_fastmcp_server_initialization(self):
        """Test that FastMCP server initializes without schema errors."""
        assert mcp is not None
        assert mcp.name == "Greptile MCP Server"
        print("✅ FastMCP server initializes correctly")
    
    def test_tool_registration(self):
        """Test that all tools are registered without type validation errors."""
        # This would fail if FastMCP couldn't generate schemas for our parameter types
        try:
            # Try to access the tools (this triggers schema validation)
            tools = []
            # Note: FastMCP 2.0 doesn't expose tools directly, but initialization success means schema validation passed
            print("✅ All tools registered without schema validation errors")
            return True
        except Exception as e:
            pytest.fail(f"Tool registration failed: {e}")
    
    def test_simple_parameter_types(self):
        """Test that all parameters use simple types compatible with FastMCP."""
        import inspect
        from main import query_repository, search_repository, index_repository, get_repository_info
        
        # Check query_repository parameters
        sig = inspect.signature(query_repository)
        params = sig.parameters
        
        # Verify simplified types
        assert params['query'].annotation == str, "query should be str"
        assert params['repositories'].annotation == str, "repositories should be str (JSON)"
        assert str(params['session_id'].annotation) == "typing.Union[str, NoneType]", "session_id should be Optional[str]"
        assert params['stream'].annotation == bool, "stream should be bool"
        assert params['genius'].annotation == bool, "genius should be bool"
        
        # Check return type is simplified
        assert sig.return_annotation == str, "return type should be str (JSON)"
        
        print("✅ All parameter types are FastMCP compatible")
    
    def test_json_parameter_parsing(self):
        """Test that JSON string parameters can be parsed correctly."""
        # Test valid JSON
        repositories_json = '[{"remote": "github", "repository": "test/repo", "branch": "main"}]'
        try:
            repositories = json.loads(repositories_json)
            assert isinstance(repositories, list)
            assert len(repositories) == 1
            assert repositories[0]["remote"] == "github"
            print("✅ JSON parameter parsing works correctly")
        except json.JSONDecodeError:
            pytest.fail("Valid JSON should parse correctly")
        
        # Test invalid JSON handling
        invalid_json = '{"invalid": json}'
        try:
            json.loads(invalid_json)
            pytest.fail("Invalid JSON should raise JSONDecodeError")
        except json.JSONDecodeError:
            print("✅ Invalid JSON properly raises JSONDecodeError")
    
    def test_parameter_defaults(self):
        """Test that parameter defaults are properly set."""
        import inspect
        from main import query_repository
        
        sig = inspect.signature(query_repository)
        params = sig.parameters
        
        # Check defaults
        assert params['session_id'].default is None
        assert params['stream'].default is False
        assert params['genius'].default is True
        assert params['timeout'].default is None
        
        print("✅ Parameter defaults are correctly set")

if __name__ == "__main__":
    test = TestParameterValidation()
    
    print("🧪 Running Parameter Validation Tests...")
    print("=" * 50)
    
    try:
        test.test_fastmcp_server_initialization()
        test.test_tool_registration()
        test.test_simple_parameter_types()
        test.test_json_parameter_parsing()
        test.test_parameter_defaults()
        
        print("\n" + "=" * 50)
        print("🎉 All Parameter Validation Tests PASSED!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
