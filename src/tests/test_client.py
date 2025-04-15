import pytest
import pytest_asyncio
from httpx import Response
from unittest.mock import patch, MagicMock
import os
from dotenv import load_dotenv

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

    def test_get_greptile_client(self):
        """Test the get_greptile_client factory function using real environment variables."""
        client = get_greptile_client()
        
        # Verify client was created with correct configuration
        assert isinstance(client, GreptileClient)
        
        # Check that base URL is set correctly (either from env or default)
        expected_base_url = os.getenv("GREPTILE_BASE_URL", "https://api.greptile.com/v2")
        assert client.base_url == expected_base_url
        
        # Verify headers contain the API keys from environment
        assert client.headers["Authorization"] == f"Bearer {os.getenv('GREPTILE_API_KEY')}"
        assert client.headers["X-GitHub-Token"] == os.getenv("GITHUB_TOKEN")
        assert client.headers["Content-Type"] == "application/json"

    def test_client_initialization(self):
        """Test client initialization with values from environment."""
        api_key = os.getenv("GREPTILE_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")
        base_url = os.getenv("GREPTILE_BASE_URL", "https://api.greptile.com/v2")
        
        client = GreptileClient(api_key, github_token, base_url)
        
        assert client.base_url == base_url
        assert client.headers["Authorization"] == f"Bearer {api_key}"
        assert client.headers["X-GitHub-Token"] == github_token
        assert client.headers["Content-Type"] == "application/json"

    def test_index_repository(self):
        """Test the index_repository method with mocked response."""
        # Create a client with real environment variables
        client = get_greptile_client()
        
        # Create a mock response
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "queued",
            "id": "repo-123",
            "message": "Repository indexing queued"
        }
        
        # Patch the post method to return our mock response
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            result = client.index_repository(
                remote="github",
                repository="test/repo",
                branch="main"
            )
            
            # Check the result matches our mock
            assert result["status"] == "queued"
            assert result["id"] == "repo-123"
            
            # Verify the POST request was made with correct arguments
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            
            # Check URL is constructed correctly using the real base URL
            expected_base_url = os.getenv("GREPTILE_BASE_URL", "https://api.greptile.com/v2")
            assert args[0] == f"{expected_base_url}/repositories"
            
            # Check payload
            assert kwargs["json"] == {
                "remote": "github",
                "repository": "sosacrazy126/greptilecli",
                "branch": "main",
                "reload": False,
                "notify": False
            }
            
            # Check headers contain real API keys
            assert kwargs["headers"]["Authorization"] == f"Bearer {os.getenv('GREPTILE_API_KEY')}"
            assert kwargs["headers"]["X-GitHub-Token"] == os.getenv("GITHUB_TOKEN")

    def test_query_repositories(self):
        """Test the query_repositories method with mocked response."""
        # Create a client with real environment variables
        client = get_greptile_client()
        
        # Create a mock response
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "This is a test answer",
            "references": [{"file": "test.py", "snippet": "def test(): pass"}],
            "confidence": 0.95
        }
        
        # Patch the post method to return our mock response
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            messages = [{"role": "user", "content": "test query"}]
            repositories = [{"remote": "github", "repository": "test/repo", "branch": "main"}]
            
            result = client.query_repositories(
                messages=messages,
                repositories=repositories
            )
            
            # Check the result matches our mock
            assert result["answer"] == "This is a test answer"
            assert len(result["references"]) == 1
            assert result["confidence"] == 0.95
            
            # Verify the POST request was made with correct arguments
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            
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

    def test_get_repository_info(self):
        """Test the get_repository_info method with mocked response."""
        # Create a client with real environment variables
        client = get_greptile_client()
        
        # Create a mock response
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "github:main:test/repo",
            "status": "completed",
            "last_indexed": "2023-01-01T00:00:00Z"
        }
        
        # Patch the get method to return our mock response
        with patch.object(client.client, 'get', return_value=mock_response) as mock_get:
            repository_id = "github:main:test/repo"
            
            result = client.get_repository_info(repository_id)
            
            # Check the result matches our mock
            assert result["id"] == "github:main:test/repo"
            assert result["status"] == "completed"
            
            # Verify the GET request was made with correct arguments
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            
            # Check URL is constructed correctly using the real base URL
            expected_base_url = os.getenv("GREPTILE_BASE_URL", "https://api.greptile.com/v2")
            assert args[0] == f"{expected_base_url}/repositories/github%3Amain%3Atest%2Frepo"