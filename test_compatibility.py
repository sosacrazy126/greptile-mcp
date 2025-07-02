#!/usr/bin/env python3
"""
Comprehensive Compatibility Test Suite for Greptile MCP Server

This test suite validates that the new Cloudflare Workers deployment maintains
full backward compatibility with the existing Python FastMCP implementation.

Test Coverage:
- All 4 MCP tools function identically
- Response formats are identical  
- Session management compatibility
- Environment variable handling
- Error handling and edge cases
- Performance characteristics
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
import tempfile
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "cloudflare"))

# Import both implementations
from src.main import (
    index_repository as original_index_repository,
    query_repository as original_query_repository, 
    search_repository as original_search_repository,
    get_repository_info as original_get_repository_info
)
from src.utils import GreptileClient as OriginalGreptileClient, SessionManager as OriginalSessionManager

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

class TestCompatibilityCore:
    """Core compatibility tests for MCP tools."""
    
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
    
    @pytest.fixture
    def workers_client_mock(self, mock_api_responses):
        """Mock for Workers GreptileClient."""
        client = MagicMock(spec=WorkersGreptileClient)
        client.index_repository = AsyncMock(return_value=mock_api_responses["index_repository"])
        client.query_repositories = AsyncMock(return_value=mock_api_responses["query_repository"])
        client.search_repositories = AsyncMock(return_value=mock_api_responses["search_repository"])
        client.get_repository_info = AsyncMock(return_value=mock_api_responses["get_repository_info"])
        client.aclose = AsyncMock()
        return client

class TestToolCompatibility(TestCompatibilityCore):
    """Test that all 4 MCP tools produce identical results."""
    
    @pytest.mark.asyncio
    async def test_index_repository_compatibility(self, original_client_mock, workers_client_mock, mock_api_responses):
        """Test index_repository tool compatibility."""
        # Test original implementation
        original_session_manager = OriginalSessionManager()
        original_ctx = MockContext(original_session_manager)
        
        with patch('src.utils.get_greptile_client', return_value=original_client_mock):
            original_result = await original_index_repository(
                ctx=original_ctx,
                remote="github",
                repository="test/repo", 
                branch="main",
                reload=True,
                notify=False
            )
        
        # Test workers implementation
        from cloudflare.worker import GreptileMCPWorker
        workers_instance = GreptileMCPWorker()
        
        with patch.object(workers_instance, 'get_greptile_client', return_value=workers_client_mock):
            workers_result = await workers_instance.index_repository(
                remote="github",
                repository="test/repo",
                branch="main", 
                reload=True,
                notify=False
            )
        
        # Validate compatibility
        original_data = json.loads(original_result)
        workers_data = workers_result["data"] if workers_result["success"] else None
        
        assert workers_result["success"] == True, "Workers implementation should succeed"
        assert original_data == workers_data, f"Response data mismatch:\nOriginal: {original_data}\nWorkers: {workers_data}"
        
        # Verify both clients called with same parameters
        original_client_mock.index_repository.assert_called_once_with("github", "test/repo", "main", True, False)
        workers_client_mock.index_repository.assert_called_once_with("github", "test/repo", "main", True, False)
    
    @pytest.mark.asyncio 
    async def test_query_repository_compatibility(self, original_client_mock, workers_client_mock, mock_api_responses):
        """Test query_repository tool compatibility."""
        # Test parameters
        test_query = "How does authentication work in this codebase?"
        test_repositories = [{"remote": "github", "repository": "test/repo", "branch": "main"}]
        test_session_id = "test-session-123"
        
        # Test original implementation
        original_session_manager = OriginalSessionManager()
        original_ctx = MockContext(original_session_manager)
        
        with patch('src.utils.get_greptile_client', return_value=original_client_mock):
            original_result = await original_query_repository(
                ctx=original_ctx,
                query=test_query,
                repositories=test_repositories,
                session_id=test_session_id,
                stream=False,
                genius=True,
                timeout=None,
                previous_messages=None
            )
        
        # Test workers implementation
        from cloudflare.worker import GreptileMCPWorker
        workers_instance = GreptileMCPWorker()
        
        with patch.object(workers_instance, 'get_greptile_client', return_value=workers_client_mock):
            workers_result = await workers_instance.query_repository(
                query=test_query,
                repositories=test_repositories,
                session_id=test_session_id,
                stream=False,
                genius=True,
                timeout=None,
                previous_messages=None
            )
        
        # Validate compatibility
        original_data = json.loads(original_result)
        workers_data = workers_result["data"] if workers_result["success"] else None
        
        assert workers_result["success"] == True, "Workers implementation should succeed"
        
        # Both should have _session_id field
        assert "_session_id" in original_data, "Original should include _session_id"
        assert "_session_id" in workers_data, "Workers should include _session_id"
        
        # Remove session IDs for comparison as they may differ
        original_data_no_session = {k: v for k, v in original_data.items() if k != "_session_id"}
        workers_data_no_session = {k: v for k, v in workers_data.items() if k != "_session_id"}
        
        assert original_data_no_session == workers_data_no_session, f"Response data mismatch:\nOriginal: {original_data_no_session}\nWorkers: {workers_data_no_session}"
    
    @pytest.mark.asyncio
    async def test_search_repository_compatibility(self, original_client_mock, workers_client_mock, mock_api_responses):
        """Test search_repository tool compatibility."""
        # Test parameters
        test_query = "find authentication middleware files"
        test_repositories = [{"remote": "github", "repository": "test/repo", "branch": "main"}]
        test_session_id = "search-session-456"
        
        # Test original implementation
        original_session_manager = OriginalSessionManager()
        original_ctx = MockContext(original_session_manager)
        
        with patch('src.utils.get_greptile_client', return_value=original_client_mock):
            original_result = await original_search_repository(
                ctx=original_ctx,
                query=test_query,
                repositories=test_repositories,
                session_id=test_session_id,
                genius=True
            )
        
        # Test workers implementation  
        from cloudflare.worker import GreptileMCPWorker
        workers_instance = GreptileMCPWorker()
        
        with patch.object(workers_instance, 'get_greptile_client', return_value=workers_client_mock):
            workers_result = await workers_instance.search_repository(
                query=test_query,
                repositories=test_repositories,
                session_id=test_session_id,
                genius=True
            )
        
        # Validate compatibility
        original_data = json.loads(original_result)
        workers_data = workers_result["data"] if workers_result["success"] else None
        
        assert workers_result["success"] == True, "Workers implementation should succeed"
        assert original_data == workers_data, f"Response data mismatch:\nOriginal: {original_data}\nWorkers: {workers_data}"
    
    @pytest.mark.asyncio
    async def test_get_repository_info_compatibility(self, original_client_mock, workers_client_mock, mock_api_responses):
        """Test get_repository_info tool compatibility."""
        # Test parameters
        test_remote = "github"
        test_repository = "test/repo"
        test_branch = "main"
        
        # Test original implementation
        original_session_manager = OriginalSessionManager()
        original_ctx = MockContext(original_session_manager)
        
        with patch('src.utils.get_greptile_client', return_value=original_client_mock):
            original_result = await original_get_repository_info(
                ctx=original_ctx,
                remote=test_remote,
                repository=test_repository,
                branch=test_branch
            )
        
        # Test workers implementation
        from cloudflare.worker import GreptileMCPWorker
        workers_instance = GreptileMCPWorker()
        
        with patch.object(workers_instance, 'get_greptile_client', return_value=workers_client_mock):
            workers_result = await workers_instance.get_repository_info(
                remote=test_remote,
                repository=test_repository,
                branch=test_branch
            )
        
        # Validate compatibility
        original_data = json.loads(original_result)
        workers_data = workers_result["data"] if workers_result["success"] else None
        
        assert workers_result["success"] == True, "Workers implementation should succeed"
        assert original_data == workers_data, f"Response data mismatch:\nOriginal: {original_data}\nWorkers: {workers_data}"
        
        # Verify both called with correct repository ID format
        expected_repo_id = f"{test_remote}:{test_branch}:{test_repository}"
        original_client_mock.get_repository_info.assert_called_once_with(expected_repo_id)
        workers_client_mock.get_repository_info.assert_called_once_with(expected_repo_id)

class TestSessionManagementCompatibility(TestCompatibilityCore):
    """Test session management compatibility between implementations."""
    
    @pytest.mark.asyncio
    async def test_session_manager_basic_operations(self):
        """Test basic session operations work identically."""
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
    
    @pytest.mark.asyncio
    async def test_session_isolation(self):
        """Test that sessions are properly isolated."""
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

class TestErrorHandlingCompatibility(TestCompatibilityCore):
    """Test error handling compatibility."""
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_api_responses):
        """Test that both implementations handle API errors identically."""
        # Create failing mocks
        failing_client_original = MagicMock(spec=OriginalGreptileClient)
        failing_client_original.index_repository = AsyncMock(side_effect=Exception("API connection failed"))
        failing_client_original.aclose = AsyncMock()
        
        failing_client_workers = MagicMock(spec=WorkersGreptileClient)
        failing_client_workers.index_repository = AsyncMock(side_effect=Exception("API connection failed"))
        failing_client_workers.aclose = AsyncMock()
        
        # Test original implementation error handling
        original_session_manager = OriginalSessionManager()
        original_ctx = MockContext(original_session_manager) 
        
        with patch('src.utils.get_greptile_client', return_value=failing_client_original):
            original_result = await original_index_repository(
                ctx=original_ctx,
                remote="github",
                repository="test/repo",
                branch="main"
            )
        
        # Test workers implementation error handling
        from cloudflare.worker import GreptileMCPWorker
        workers_instance = GreptileMCPWorker()
        
        with patch.object(workers_instance, 'get_greptile_client', return_value=failing_client_workers):
            workers_result = await workers_instance.index_repository(
                remote="github",
                repository="test/repo",
                branch="main"
            )
        
        # Validate error handling compatibility
        assert original_result.startswith("Error indexing repository:"), "Original should return error message"
        assert workers_result["success"] == False, "Workers should indicate failure"
        assert "Error indexing repository:" in workers_result["error"]["message"], "Workers should include error details"
    
    @pytest.mark.asyncio
    async def test_environment_variable_errors(self):
        """Test handling of missing environment variables."""
        # Temporarily clear environment variables
        original_api_key = os.environ.get("GREPTILE_API_KEY")
        original_github_token = os.environ.get("GITHUB_TOKEN")
        
        try:
            # Remove required environment variables
            if "GREPTILE_API_KEY" in os.environ:
                del os.environ["GREPTILE_API_KEY"]
            if "GITHUB_TOKEN" in os.environ:
                del os.environ["GITHUB_TOKEN"]
            
            # Test workers environment variable handling
            from cloudflare.worker import GreptileMCPWorker
            workers_instance = GreptileMCPWorker()
            
            with pytest.raises(ValueError, match="GREPTILE_API_KEY environment variable is required"):
                workers_instance.get_greptile_client()
                
        finally:
            # Restore environment variables
            if original_api_key:
                os.environ["GREPTILE_API_KEY"] = original_api_key
            if original_github_token:
                os.environ["GITHUB_TOKEN"] = original_github_token

class TestPerformanceCompatibility(TestCompatibilityCore):
    """Test performance characteristics compatibility."""
    
    @pytest.mark.asyncio
    async def test_response_time_similarity(self, original_client_mock, workers_client_mock):
        """Test that both implementations have similar response times."""
        # Add small delays to simulate API calls
        original_client_mock.index_repository = AsyncMock(
            return_value={"status": "queued"}, 
            side_effect=lambda *args, **kwargs: asyncio.sleep(0.1)
        )
        workers_client_mock.index_repository = AsyncMock(
            return_value={"status": "queued"},
            side_effect=lambda *args, **kwargs: asyncio.sleep(0.1) 
        )
        
        # Time original implementation
        original_session_manager = OriginalSessionManager()
        original_ctx = MockContext(original_session_manager)
        
        start_time = time.time()
        with patch('src.utils.get_greptile_client', return_value=original_client_mock):
            await original_index_repository(
                ctx=original_ctx,
                remote="github", 
                repository="test/repo",
                branch="main"
            )
        original_time = time.time() - start_time
        
        # Time workers implementation  
        from cloudflare.worker import GreptileMCPWorker
        workers_instance = GreptileMCPWorker()
        
        start_time = time.time()
        with patch.object(workers_instance, 'get_greptile_client', return_value=workers_client_mock):
            await workers_instance.index_repository(
                remote="github",
                repository="test/repo", 
                branch="main"
            )
        workers_time = time.time() - start_time
        
        # Allow 50% variance in response times
        time_ratio = max(original_time, workers_time) / min(original_time, workers_time)
        assert time_ratio < 1.5, f"Response time difference too large: {original_time:.3f}s vs {workers_time:.3f}s"

class TestEnvironmentVariableCompatibility:
    """Test environment variable handling compatibility."""
    
    def test_environment_variable_abstraction(self):
        """Test that environment variable abstraction works correctly."""
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
            
        finally:
            # Clean up
            if test_key in os.environ:
                del os.environ[test_key]

if __name__ == "__main__":
    # Run the compatibility tests
    pytest.main([__file__, "-v", "--tb=short"])