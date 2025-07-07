import pytest
import pytest_asyncio
from httpx import Response
from unittest.mock import patch, MagicMock, AsyncMock
import os
from dotenv import load_dotenv
import urllib.parse

from src.utils import GreptileClient, get_greptile_client

# Load environment variables from .env file
load_dotenv()

class TestGreptileClient:
    """Test suite for the GreptileClient class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        # Ensure required environment variables exist
        if not os.getenv("GREPTILE_API_KEY"):
            pytest.skip("GREPTILE_API_KEY environment variable not set")
        if not os.getenv("GITHUB_TOKEN"):
            pytest.skip("GITHUB_TOKEN environment variable not set")

    @pytest.mark.asyncio
    async def test_get_greptile_client(self):
        """Test the get_greptile_client factory function using real environment variables."""
        client = get_greptile_client()
        
        try:
            # Verify client was created with correct configuration
            assert isinstance(client, GreptileClient)
            
            # Check that base URL is set correctly (either from env or default)
            expected_base_url = os.getenv("GREPTILE_BASE_URL", "https://api.greptile.com/v2")
            assert client.base_url == expected_base_url
            
            # Verify headers contain the API keys from environment
            assert client.headers["Authorization"] == f"Bearer {os.getenv('GREPTILE_API_KEY')}"
            assert client.headers["X-GitHub-Token"] == os.getenv("GITHUB_TOKEN")
            assert client.headers["Content-Type"] == "application/json"
        finally:
            # Clean up by closing the client
            await client.aclose()

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization with values from environment."""
        api_key = os.getenv("GREPTILE_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")
        base_url = os.getenv("GREPTILE_BASE_URL", "https://api.greptile.com/v2")
        
        client = GreptileClient(api_key, github_token, base_url)
        
        try:
            assert client.base_url == base_url
            assert client.headers["Authorization"] == f"Bearer {api_key}"
            assert client.headers["X-GitHub-Token"] == github_token
            assert client.headers["Content-Type"] == "application/json"
        finally:
            # Clean up by closing the client
            await client.aclose()

    @pytest.mark.asyncio
    async def test_index_repository(self):
        """Test the index_repository method with mocked response."""
        # Create a client with real environment variables
        client = get_greptile_client()
        
        try:
            # Create a mock response
            mock_response = MagicMock(spec=Response)
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "queued",
                "id": "repo-123",
                "message": "Repository indexing queued"
            }
            
            # Patch the post method to return our mock response
            client.client.post = AsyncMock(return_value=mock_response)
            
            result = await client.index_repository(
                remote="github",
                repository="test/repo",
                branch="main"
            )
            
            # Check the result matches our mock
            assert result["status"] == "queued"
            assert result["id"] == "repo-123"
            
            # Verify the POST request was made with correct arguments
            client.client.post.assert_called_once()
            args, kwargs = client.client.post.call_args
            
            # Check URL is constructed correctly using the real base URL
            expected_base_url = os.getenv("GREPTILE_BASE_URL", "https://api.greptile.com/v2")
            assert args[0] == f"{expected_base_url}/repositories"
            
            # Check payload
            assert kwargs["json"] == {
                "remote": "github",
                "repository": "test/repo",
                "branch": "main",
                "reload": True,  # Updated to match current default
                "notify": False
            }
            
            # Check headers contain real API keys
            assert kwargs["headers"]["Authorization"] == f"Bearer {os.getenv('GREPTILE_API_KEY')}"
            assert kwargs["headers"]["X-GitHub-Token"] == os.getenv("GITHUB_TOKEN")
        finally:
            await client.aclose()

    @pytest.mark.asyncio
    async def test_query_repositories(self):
        """Test the query_repositories method with mocked response."""
        # Create a client with real environment variables
        client = get_greptile_client()
        
        try:
            # Create a mock response
            mock_response = MagicMock(spec=Response)
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "answer": "This is a test answer",
                "references": [{"file": "test.py", "snippet": "def test(): pass"}],
                "confidence": 0.95
            }
            
            # Create a mock async client
            mock_async_client = AsyncMock()
            mock_async_client.post = AsyncMock(return_value=mock_response)
            mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
            mock_async_client.__aexit__ = AsyncMock(return_value=None)
            
            # Patch httpx.AsyncClient to return our mock
            with patch('httpx.AsyncClient', return_value=mock_async_client):
                messages = [{"role": "user", "content": "test query"}]
                repositories = [{"remote": "github", "repository": "test/repo", "branch": "main"}]
                
                result = await client.query_repositories(
                    messages=messages,
                    repositories=repositories
                )
            
            # Check the result matches our mock
            assert result["answer"] == "This is a test answer"
            assert len(result["references"]) == 1
            assert result["confidence"] == 0.95
            
            # Verify the POST request was made with correct arguments
            mock_async_client.post.assert_called_once()
            args, kwargs = mock_async_client.post.call_args
            
            # Check URL is constructed correctly using the real base URL
            expected_base_url = os.getenv("GREPTILE_BASE_URL", "https://api.greptile.com/v2")
            assert args[0] == f"{expected_base_url}/query"
            
            # Check payload
            assert kwargs["json"] == {
                "messages": messages,
                "repositories": repositories,
                "stream": False,
                "genius": True
            }
        finally:
            await client.aclose()

    @pytest.mark.asyncio
    async def test_get_repository_info(self):
        """Test the get_repository_info method with mocked response."""
        # Create a client with real environment variables
        client = get_greptile_client()
        
        try:
            # Create a mock response
            mock_response = MagicMock(spec=Response)
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "github:main:test/repo",
                "status": "completed",
                "last_indexed": "2023-01-01T00:00:00Z"
            }
            
            # Patch the get method to return our mock response
            client.client.get = AsyncMock(return_value=mock_response)
            
            repository_id = "github:main:test/repo"
            
            result = await client.get_repository_info(repository_id)
            
            # Check the result matches our mock
            assert result["id"] == "github:main:test/repo"
            assert result["status"] == "completed"
            
            # Verify the GET request was made with correct arguments
            client.client.get.assert_called_once()
            args, kwargs = client.client.get.call_args
            
            # Check URL is constructed correctly using the real base URL
            expected_base_url = os.getenv("GREPTILE_BASE_URL", "https://api.greptile.com/v2")
            # Use quote_plus with safe='' to ensure complete encoding, including slashes
            encoded_repo = urllib.parse.quote_plus("github:main:test/repo", safe='')
            assert args[0] == f"{expected_base_url}/repositories/{encoded_repo}"
        finally:
            await client.aclose()