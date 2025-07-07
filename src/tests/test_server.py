import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import json
import os

# Correct import for FastMCP and Context
from mcp.server.fastmcp import FastMCP, Context

# Import the tools from your main.py file
# Make sure the path is correct based on your project structure
from src.main import index_repository, query_repository, search_repository, get_repository_info
from src.utils import GreptileClient

# Set environment variables for testing
os.environ["GREPTILE_API_KEY"] = "test_api_key"
os.environ["GITHUB_TOKEN"] = "test_github_token"
os.environ["GREPTILE_BASE_URL"] = "https://api.greptile.test/v2"

@pytest.fixture
def mock_greptile_client():
    """Create a mock GreptileClient for testing."""
    client = MagicMock(spec=GreptileClient)
    
    # Updated mock responses to match actual API responses
    client.index_repository = AsyncMock(return_value={
        "status": "queued",
        "id": "test-id",
        "message": "Repository indexing queued"
    })
    client.query_repositories = AsyncMock(return_value={
        "answer": "Test answer",
        "references": [],
        "confidence": 0.95
    })
    client.search_repositories = AsyncMock(return_value={
        "files": [
            {
                "path": "test/file.py",
                "score": 0.85,
                "matches": []
            }
        ]
    })
    client.get_repository_info = AsyncMock(return_value={
        "id": "test-id",
        "status": "completed",
        "last_indexed": "2024-03-20T12:00:00Z",
        "branch": "main"
    })
    client.aclose = AsyncMock()
    return client

@pytest.fixture
def mock_context(mock_greptile_client):
    """Create a mock Context with the GreptileClient."""
    ctx = MagicMock(spec=Context)
    # Set up the context structure to match what the tools expect
    ctx.request_context.lifespan_context.greptile_client = mock_greptile_client
    return ctx

class TestMCPTools:
    """Test suite for the MCP tools."""

    @pytest.mark.asyncio
    async def test_index_repository(self, mock_context, mock_greptile_client):
        """Test the index_repository tool."""
        result = await index_repository(
            ctx=mock_context,
            remote="github",
            repository="test/repo",
            branch="main"
        )
        
        # Verify the client method was called with correct parameters
        mock_greptile_client.index_repository.assert_called_once_with(
            "github", "test/repo", "main", True, False  # Updated to match current defaults
        )
        
        # Parse and verify the result
        parsed_result = json.loads(result)
        assert parsed_result["status"] == "queued"
        assert parsed_result["id"] == "test-id"
        assert "message" in parsed_result

    @pytest.mark.asyncio
    async def test_query_repository(self, mock_context, mock_greptile_client):
        """Test the query_repository tool."""
        result = await query_repository(
            ctx=mock_context,
            query="test query",
            repositories=[{"remote": "github", "repository": "test/repo", "branch": "main"}]
        )
        
        # Verify the client method was called with correct parameters
        mock_greptile_client.query_repositories.assert_called_once()
        args, kwargs = mock_greptile_client.query_repositories.call_args
        
        # Verify the arguments match what we expect
        # The first arg should be messages with id field
        assert args[0] == [{"id": "msg_0", "content": "test query", "role": "user"}]
        # The second arg should be repositories
        assert args[1] == [{"remote": "github", "repository": "test/repo", "branch": "main"}]
        
        # Parse and verify the result
        parsed_result = json.loads(result)
        assert parsed_result["answer"] == "Test answer"
        assert "confidence" in parsed_result

    @pytest.mark.asyncio
    async def test_search_repository(self, mock_context, mock_greptile_client):
        """Test the search_repository tool."""
        result = await search_repository(
            ctx=mock_context,
            query="test query",
            repositories=[{"remote": "github", "repository": "test/repo", "branch": "main"}]
        )
        
        # Verify the client method was called with correct parameters
        mock_greptile_client.search_repositories.assert_called_once()
        args, kwargs = mock_greptile_client.search_repositories.call_args
        
        # Verify the arguments match what we expect
        # The first arg should be messages with id field
        assert args[0] == [{"id": "msg_0", "content": "test query", "role": "user"}]
        # The second arg should be repositories
        assert args[1] == [{"remote": "github", "repository": "test/repo", "branch": "main"}]
        
        # Parse and verify the result
        parsed_result = json.loads(result)
        assert "files" in parsed_result
        assert len(parsed_result["files"]) == 1
        assert parsed_result["files"][0]["path"] == "test/file.py"
        assert "score" in parsed_result["files"][0]

    @pytest.mark.asyncio
    async def test_get_repository_info(self, mock_context, mock_greptile_client):
        """Test the get_repository_info tool."""
        result = await get_repository_info(
            ctx=mock_context,
            remote="github",
            repository="test/repo",
            branch="main"
        )
        
        # Verify the client method was called with correct parameters
        mock_greptile_client.get_repository_info.assert_called_once_with("github:main:test/repo")
        
        # Parse and verify the result
        parsed_result = json.loads(result)
        assert parsed_result["id"] == "test-id"
        assert parsed_result["status"] == "completed"
        assert "last_indexed" in parsed_result

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_context, mock_greptile_client):
        """Test that errors are properly handled and returned as error strings."""
        # Set up the mock to raise an exception
        mock_greptile_client.index_repository = AsyncMock(side_effect=Exception("Test error"))
        
        result = await index_repository(
            ctx=mock_context,
            remote="github",
            repository="test/repo",
            branch="main"
        )
        
        # Verify the error message is returned
        assert result.startswith("Error indexing repository: Test error")