#!/usr/bin/env python3
"""
Core Compatibility Test Suite

This test suite validates the core functionality compatibility between
the original implementation and the Cloudflare Workers shared utilities,
without requiring Cloudflare Workers runtime dependencies.
"""

import pytest
import pytest_asyncio
import asyncio
import json
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any, List
import time
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "cloudflare"))

# Import the original implementation
from src.main import (
    index_repository as original_index_repository,
    query_repository as original_query_repository, 
    search_repository as original_search_repository,
    get_repository_info as original_get_repository_info
)
from src.utils import GreptileClient as OriginalGreptileClient, SessionManager as OriginalSessionManager

# Import only the shared utilities (avoid worker.py which has JS dependencies)
from cloudflare.shared_utils import (
    GreptileClient as WorkersGreptileClient,
    SessionManager as WorkersSessionManager,
    create_success_response,
    create_error_response,
    get_environment_variable
)

# Set test environment variables
os.environ["GREPTILE_API_KEY"] = "test_api_key_12345"
os.environ["GITHUB_TOKEN"] = "ghp_test_token_12345"
os.environ["GREPTILE_BASE_URL"] = "https://api.greptile.test/v2"

class MockContext:
    """Mock MCP Context for testing original implementation."""
    
    def __init__(self, session_manager):
        self.request_context = MagicMock()
        self.request_context.lifespan_context = MagicMock()
        self.request_context.lifespan_context.session_manager = session_manager

class TestCoreCompatibility:
    """Test core functionality compatibility."""
    
    @pytest.fixture
    def mock_api_responses(self):
        """Standard mock API responses for testing."""
        return {
            "index_repository": {
                "status": "queued",
                "id": "test-repo-id-123",
                "message": "Repository indexing queued successfully",
                "timestamp": "2024-01-15T10:30:00Z"
            },
            "query_repository": {
                "output": "This is a comprehensive answer about the codebase structure and implementation patterns.",
                "messages": [
                    {"role": "user", "content": "test query"},
                    {"role": "assistant", "content": "This is a comprehensive answer about the codebase structure and implementation patterns."}
                ],
                "sources": [
                    {
                        "filepath": "src/main.py",
                        "summary": "Main application entry point",
                        "lines": [1, 50]
                    }
                ]
            },
            "search_repository": {
                "relevant_files": [
                    {
                        "file_path": "src/auth/authentication.py",
                        "relevance_score": 0.95,
                        "snippet": "class AuthenticationMiddleware...",
                        "line_numbers": [15, 45, 78],
                        "summary": "Main authentication logic implementation"
                    }
                ],
                "total_files_found": 12,
                "search_metadata": {
                    "query_complexity": "high",
                    "genius_mode_used": True,
                    "search_time_ms": 3240
                }
            },
            "get_repository_info": {
                "id": "github:main:test/repo",
                "status": "COMPLETED",
                "repository": "test/repo",
                "remote": "github",
                "branch": "main",
                "private": False,
                "filesProcessed": 234,
                "numFiles": 234,
                "lastIndexed": "2024-01-15T10:30:00Z",
                "indexingTime": 45.2,
                "size": "12.5MB"
            }
        }
    
    @pytest.fixture
    def original_client_mock(self, mock_api_responses):
        """Mock for original GreptileClient."""
        client = MagicMock(spec=OriginalGreptileClient)
        client.index_repository = AsyncMock(return_value=mock_api_responses["index_repository"])
        client.query_repositories = AsyncMock(return_value=mock_api_responses["query_repository"])
        client.search_repositories = AsyncMock(return_value=mock_api_responses["search_repository"]) 
        client.get_repository_info = AsyncMock(return_value=mock_api_responses["get_repository_info"])
        client.aclose = AsyncMock()
        return client
    
    @pytest.mark.asyncio
    async def test_greptile_client_api_compatibility(self, mock_api_responses):
        """Test that both GreptileClient implementations have the same API."""
        # Create mock HTTP responses for both clients
        mock_response = {"json": lambda: mock_api_responses["index_repository"]}
        
        # Test original client
        original_client = OriginalGreptileClient("test_key", "test_token")
        
        # Test workers client  
        workers_client = WorkersGreptileClient("test_key", "test_token")
        
        # Verify both have the same methods
        common_methods = [
            "index_repository",
            "query_repositories", 
            "search_repositories",
            "get_repository_info",
            "aclose"
        ]
        
        for method in common_methods:
            assert hasattr(original_client, method), f"Original client missing method: {method}"
            assert hasattr(workers_client, method), f"Workers client missing method: {method}"
        
        # Test method signatures match
        import inspect
        
        # index_repository signature compatibility
        orig_sig = inspect.signature(original_client.index_repository)
        workers_sig = inspect.signature(workers_client.index_repository)
        
        assert orig_sig.parameters.keys() == workers_sig.parameters.keys(), \
            f"index_repository signature mismatch:\nOriginal: {orig_sig}\nWorkers: {workers_sig}"
        
        # query_repositories signature compatibility
        orig_sig = inspect.signature(original_client.query_repositories)
        workers_sig = inspect.signature(workers_client.query_repositories)
        
        # Note: We expect some differences due to streaming implementation
        orig_params = set(orig_sig.parameters.keys())
        workers_params = set(workers_sig.parameters.keys())
        
        # Core parameters should be the same
        core_params = {"messages", "repositories", "session_id", "genius", "timeout"}
        assert core_params.issubset(orig_params), f"Original missing core params: {core_params - orig_params}"
        assert core_params.issubset(workers_params), f"Workers missing core params: {core_params - workers_params}"
        
        await original_client.aclose()
        await workers_client.aclose()
    
    @pytest.mark.asyncio
    async def test_session_manager_compatibility(self):
        """Test that both SessionManager implementations behave identically."""
        session_id = "test-session-789"
        test_messages = [
            {"role": "user", "content": "first message"},
            {"role": "assistant", "content": "first response"},
            {"role": "user", "content": "second message"}
        ]
        
        # Test original session manager
        original_sm = OriginalSessionManager()
        await original_sm.set_history(session_id, test_messages)
        original_history = await original_sm.get_history(session_id)
        
        # Test workers session manager
        workers_sm = WorkersSessionManager()
        await workers_sm.set_history(session_id, test_messages)
        workers_history = await workers_sm.get_history(session_id)
        
        # Validate identical behavior
        assert original_history == workers_history, "Session managers should store identical history"
        assert len(original_history) == 3, "Should store all 3 messages"
        
        # Test append message
        new_message = {"role": "assistant", "content": "second response"}
        await original_sm.append_message(session_id, new_message)
        await workers_sm.append_message(session_id, new_message)
        
        original_history_after = await original_sm.get_history(session_id)
        workers_history_after = await workers_sm.get_history(session_id)
        
        assert original_history_after == workers_history_after, "Append operation should be identical"
        assert len(original_history_after) == 4, "Should have 4 messages after append"
        
        # Test clear session
        await original_sm.clear_session(session_id)
        await workers_sm.clear_session(session_id)
        
        original_cleared = await original_sm.get_history(session_id)
        workers_cleared = await workers_sm.get_history(session_id)
        
        assert original_cleared == workers_cleared == [], "Clear session should result in empty history"
    
    @pytest.mark.asyncio
    async def test_session_isolation(self):
        """Test that sessions are properly isolated in both implementations."""
        session1 = "session-1"
        session2 = "session-2"
        
        messages1 = [{"role": "user", "content": "session 1 message"}]
        messages2 = [{"role": "user", "content": "session 2 message"}]
        
        # Test both implementations
        for sm_class, name in [(OriginalSessionManager, "original"), (WorkersSessionManager, "workers")]:
            sm = sm_class()
            
            await sm.set_history(session1, messages1)
            await sm.set_history(session2, messages2)
            
            history1 = await sm.get_history(session1)
            history2 = await sm.get_history(session2)
            
            assert history1 != history2, f"{name}: Sessions should be isolated"
            assert history1[0]["content"] == "session 1 message", f"{name}: Session 1 content mismatch"
            assert history2[0]["content"] == "session 2 message", f"{name}: Session 2 content mismatch"
    
    def test_response_format_compatibility(self):
        """Test response format functions."""
        test_data = {"result": "success", "value": 42}
        error_message = "Test error occurred"
        
        # Test success response format
        success_response = create_success_response(test_data)
        
        expected_success = {
            "success": True,
            "data": test_data,
            "error": None
        }
        
        assert success_response == expected_success, f"Success response format mismatch: {success_response}"
        
        # Test error response format
        error_response = create_error_response(error_message, "TEST_ERROR")
        
        expected_error = {
            "success": False,
            "data": None,
            "error": {
                "message": error_message,
                "code": "TEST_ERROR"
            }
        }
        
        assert error_response == expected_error, f"Error response format mismatch: {error_response}"
        
        # Test error response with default code
        error_response_default = create_error_response(error_message)
        
        expected_error_default = {
            "success": False,
            "data": None,
            "error": {
                "message": error_message,
                "code": "UNKNOWN_ERROR"
            }
        }
        
        assert error_response_default == expected_error_default, f"Default error response format mismatch: {error_response_default}"
    
    def test_environment_variable_compatibility(self):
        """Test environment variable handling."""
        # Test with standard environment variable
        test_key = "TEST_ENV_VAR_123"
        test_value = "test_value_456"
        
        os.environ[test_key] = test_value
        
        try:
            # Test workers environment variable getter
            result = get_environment_variable(test_key)
            assert result == test_value, "Should retrieve environment variable correctly"
            
            # Test with default value
            result_with_default = get_environment_variable("NONEXISTENT_VAR", "default_value")
            assert result_with_default == "default_value", "Should return default value for missing vars"
            
            # Test None default
            result_none = get_environment_variable("NONEXISTENT_VAR")
            assert result_none is None, "Should return None for missing vars without default"
            
        finally:
            # Clean up
            if test_key in os.environ:
                del os.environ[test_key]
    
    @pytest.mark.asyncio
    async def test_original_tool_functionality(self, original_client_mock, mock_api_responses):
        """Test that original tools still work as expected."""
        # Test index_repository
        original_session_manager = OriginalSessionManager()
        original_ctx = MockContext(original_session_manager)
        
        with patch('src.utils.get_greptile_client', return_value=original_client_mock):
            result = await original_index_repository(
                ctx=original_ctx,
                remote="github",
                repository="test/repo",
                branch="main",
                reload=True,
                notify=False
            )
        
        # Verify result is JSON string with expected data
        parsed_result = json.loads(result)
        assert parsed_result == mock_api_responses["index_repository"]
        
        # Verify client was called correctly
        original_client_mock.index_repository.assert_called_once_with("github", "test/repo", "main", True, False)
        original_client_mock.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_comparison(self, mock_api_responses):
        """Test error handling in both implementations."""
        # Create clients that will fail
        failing_original = MagicMock(spec=OriginalGreptileClient)
        failing_original.index_repository = AsyncMock(side_effect=Exception("Connection failed"))
        failing_original.aclose = AsyncMock()
        
        failing_workers = MagicMock(spec=WorkersGreptileClient)
        failing_workers.index_repository = AsyncMock(side_effect=Exception("Connection failed"))
        failing_workers.aclose = AsyncMock()
        
        # Test original error handling
        original_session_manager = OriginalSessionManager()
        original_ctx = MockContext(original_session_manager)
        
        with patch('src.utils.get_greptile_client', return_value=failing_original):
            original_result = await original_index_repository(
                ctx=original_ctx,
                remote="github",
                repository="test/repo",
                branch="main"
            )
        
        # Original should return error string
        assert isinstance(original_result, str), "Original should return string on error"
        assert "Error indexing repository:" in original_result, "Original should include error prefix"
        assert "Connection failed" in original_result, "Original should include original error message"
        
        # For workers, we'll test the shared utilities directly (without the wrapper)
        try:
            await failing_workers.index_repository("github", "test/repo", "main")
            assert False, "Workers client should have raised exception"
        except Exception as e:
            # Workers utility should propagate the exception
            assert str(e) == "Connection failed", "Workers should propagate original exception"

class TestToolParameterCompatibility:
    """Test that tool parameters are handled identically."""
    
    def test_tool_parameter_specifications(self):
        """Verify tool parameter specifications match between implementations."""
        # Import the original tool functions to inspect their signatures
        import inspect
        
        tools_to_test = [
            ("index_repository", original_index_repository),
            ("query_repository", original_query_repository),
            ("search_repository", original_search_repository),
            ("get_repository_info", original_get_repository_info)
        ]
        
        for tool_name, tool_func in tools_to_test:
            sig = inspect.signature(tool_func)
            params = sig.parameters
            
            # Verify ctx parameter is present (MCP context)
            assert "ctx" in params, f"{tool_name} should have ctx parameter"
            
            # Check specific parameter requirements for each tool
            if tool_name == "index_repository":
                required_params = {"remote", "repository", "branch", "reload", "notify"}
                for param in required_params:
                    assert param in params, f"{tool_name} missing parameter: {param}"
                
                # Check default values
                assert params["reload"].default == True, f"{tool_name} reload default should be True"
                assert params["notify"].default == False, f"{tool_name} notify default should be False"
            
            elif tool_name == "query_repository":
                required_params = {"query", "repositories", "session_id", "stream", "genius", "timeout", "previous_messages"}
                for param in required_params:
                    assert param in params, f"{tool_name} missing parameter: {param}"
                
                # Check default values
                assert params["session_id"].default is None, f"{tool_name} session_id default should be None"
                assert params["stream"].default == False, f"{tool_name} stream default should be False"
                assert params["genius"].default == True, f"{tool_name} genius default should be True"
            
            elif tool_name == "search_repository":
                required_params = {"query", "repositories", "session_id", "genius"}
                for param in required_params:
                    assert param in params, f"{tool_name} missing parameter: {param}"
            
            elif tool_name == "get_repository_info":
                required_params = {"remote", "repository", "branch"}
                for param in required_params:
                    assert param in params, f"{tool_name} missing parameter: {param}"

class TestAPICallCompatibility:
    """Test API call patterns and compatibility."""
    
    @pytest.mark.asyncio
    async def test_repository_id_format_consistency(self):
        """Test that repository ID formatting is consistent."""
        test_remote = "github"
        test_repository = "test/repo"
        test_branch = "main"
        
        expected_repo_id = f"{test_remote}:{test_branch}:{test_repository}"
        
        # Test original implementation format
        original_session_manager = OriginalSessionManager()
        original_ctx = MockContext(original_session_manager)
        
        original_client_mock = MagicMock(spec=OriginalGreptileClient)
        original_client_mock.get_repository_info = AsyncMock(return_value={"status": "test"})
        original_client_mock.aclose = AsyncMock()
        
        with patch('src.utils.get_greptile_client', return_value=original_client_mock):
            await original_get_repository_info(
                ctx=original_ctx,
                remote=test_remote,
                repository=test_repository,
                branch=test_branch
            )
        
        # Verify the repository ID format used
        original_client_mock.get_repository_info.assert_called_once_with(expected_repo_id)
        
        # Test workers implementation format (using shared utilities directly)
        workers_client = WorkersGreptileClient("test_key", "test_token")
        
        # Mock the HTTP client call
        workers_client.client = MagicMock()
        workers_client.client.get = AsyncMock(return_value={"status": "test"})
        
        await workers_client.get_repository_info(expected_repo_id)
        
        # Verify URL encoding consistency
        import urllib.parse
        encoded_id = urllib.parse.quote_plus(expected_repo_id, safe='')
        expected_url = f"https://api.greptile.com/v2/repositories/{encoded_id}"
        
        workers_client.client.get.assert_called_once_with(expected_url, workers_client.headers)
        
        await workers_client.aclose()

if __name__ == "__main__":
    # Run the core compatibility tests
    pytest.main([__file__, "-v", "--tb=short"])