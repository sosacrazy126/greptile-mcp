"""
Pytest configuration and shared fixtures for Greptile MCP Server tests.

This file contains common test fixtures and configuration that can be used
across all test modules.
"""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Generator

from src.utils import GreptileClient, SessionManager


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_env_vars() -> Generator[Dict[str, str], None, None]:
    """Provide mock environment variables for testing."""
    test_env = {
        'GREPTILE_API_KEY': 'test_api_key_12345',
        'GITHUB_TOKEN': 'test_github_token_67890',
        'GREPTILE_BASE_URL': 'https://api.greptile.com/v2',
        'HOST': '0.0.0.0',
        'PORT': '8050'
    }
    
    with patch.dict(os.environ, test_env, clear=True):
        yield test_env


@pytest.fixture
def mock_greptile_client() -> AsyncMock:
    """Create a mock GreptileClient for testing."""
    mock_client = AsyncMock(spec=GreptileClient)
    
    # Set up default return values for common methods
    mock_client.index_repository.return_value = {
        "message": "Indexing Job Submitted for: test/repo",
        "statusEndpoint": "https://api.greptile.com/v2/repositories/github:main:test%2Frepo"
    }
    
    mock_client.query_repositories.return_value = {
        "message": "Test response from Greptile API",
        "sources": [
            {
                "repository": "test/repo",
                "remote": "github",
                "branch": "main",
                "filepath": "/src/test.py",
                "linestart": 1,
                "lineend": 10,
                "summary": "Test file"
            }
        ]
    }
    
    mock_client.search_repositories.return_value = {
        "files": [
            {
                "repository": "test/repo",
                "remote": "github",
                "branch": "main",
                "filepath": "/src/",
                "summary": "Source directory"
            }
        ]
    }
    
    mock_client.get_repository_info.return_value = {
        "repository": "test/repo",
        "remote": "github",
        "branch": "main",
        "status": "indexed",
        "numFiles": 42,
        "indexedAt": "2024-01-15T10:30:00Z"
    }
    
    # Mock streaming response
    async def mock_stream():
        yield {"chunk": "First chunk"}
        yield {"chunk": "Second chunk"}
        yield {"chunk": "Final chunk"}
    
    mock_client.stream_query_repositories.return_value = mock_stream()
    
    return mock_client


@pytest.fixture
def mock_session_manager() -> AsyncMock:
    """Create a mock SessionManager for testing."""
    mock_manager = AsyncMock(spec=SessionManager)
    
    # Set up default behavior
    mock_manager.get_history.return_value = []
    mock_manager.append_message.return_value = None
    mock_manager.set_history.return_value = None
    mock_manager.clear_session.return_value = None
    
    return mock_manager


@pytest.fixture
def sample_repositories() -> list:
    """Provide sample repository data for testing."""
    return [
        {
            "remote": "github",
            "repository": "test/repo1",
            "branch": "main"
        },
        {
            "remote": "github", 
            "repository": "test/repo2",
            "branch": "develop"
        },
        {
            "remote": "gitlab",
            "repository": "example/project",
            "branch": "main"
        }
    ]


@pytest.fixture
def sample_messages() -> list:
    """Provide sample message data for testing."""
    return [
        {"role": "user", "content": "How does authentication work?"},
        {"role": "assistant", "content": "Authentication is handled using JWT tokens..."},
        {"role": "user", "content": "Can you show me the implementation?"}
    ]


@pytest.fixture
def sample_mcp_request() -> Dict[str, Any]:
    """Provide a sample MCP JSON-RPC request for testing."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "query_repository",
            "arguments": {
                "query": "How is authentication implemented?",
                "repositories": '[{"remote":"github","repository":"test/repo","branch":"main"}]',
                "session_id": "test-session-123",
                "genius": True
            }
        }
    }


@pytest.fixture
def sample_tool_response() -> Dict[str, Any]:
    """Provide a sample tool response for testing."""
    return {
        "message": "Authentication is implemented using JWT tokens in the auth module.",
        "sources": [
            {
                "repository": "test/repo",
                "remote": "github",
                "branch": "main",
                "filepath": "/src/auth/jwt.py",
                "linestart": 15,
                "lineend": 45,
                "summary": "JWT token validation and generation"
            }
        ],
        "session_id": "test-session-123"
    }


@pytest.fixture(autouse=True)
def reset_global_client():
    """Reset the global client instance before each test."""
    # Import here to avoid circular imports
    import src.main
    src.main._greptile_client = None
    yield
    # Clean up after test
    src.main._greptile_client = None


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response for testing."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}
    mock_response.raise_for_status.return_value = None
    return mock_response


class AsyncContextManagerMock:
    """Helper class for mocking async context managers."""
    
    def __init__(self, return_value):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx.AsyncClient for testing."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"test": "response"}
    mock_response.raise_for_status.return_value = None
    
    mock_client.post.return_value = mock_response
    mock_client.get.return_value = mock_response
    mock_client.aclose.return_value = None
    
    return mock_client


# Test markers for different test categories
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.slow = pytest.mark.slow


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add unit marker to unit tests
        if "unit" in item.nodeid or "test_" in item.name:
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to integration tests
        if "integration" in item.nodeid or "Integration" in item.name:
            item.add_marker(pytest.mark.integration)
        
        # Add e2e marker to end-to-end tests
        if "e2e" in item.nodeid or "E2E" in item.name:
            item.add_marker(pytest.mark.e2e)
        
        # Add slow marker to tests that might be slow
        if any(keyword in item.name.lower() for keyword in ["stream", "timeout", "large"]):
            item.add_marker(pytest.mark.slow)
