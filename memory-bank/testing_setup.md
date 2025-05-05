# Greptile MCP Testing Setup

## Testing Requirements

The Greptile MCP testing suite requires the following dependencies:

- `pytest` - Core testing framework
- `pytest-asyncio` - Extension for testing asynchronous code
- `httpx` - HTTP client used in the implementation
- `pytest-mock` - Mocking library for unit tests

## Installation

To install the required testing dependencies:

```bash
# Using pip
pip install pytest pytest-asyncio pytest-mock httpx

# Using uv
uv pip install pytest pytest-asyncio pytest-mock httpx
```

## Running Tests

After installing the dependencies, you can run the tests using:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest src/tests/test_client.py
```

## Test Structure

The testing suite is organized into two main files:

1. `src/tests/test_client.py` - Tests for the Greptile API client
2. `src/tests/test_server.py` - Tests for the MCP server and tools

Both files use `pytest_asyncio` for testing asynchronous functions.

## Mocking API Calls

For testing without making actual API calls, the tests use mocking:

```python
@pytest.fixture
def mock_httpx_client(mocker):
    """Mock the httpx.AsyncClient to avoid actual API calls."""
    mock_client = mocker.patch('httpx.AsyncClient')
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"status": "success"}
    mock_response.raise_for_status = mocker.Mock()
    mock_client.return_value.post.return_value = mock_response
    mock_client.return_value.get.return_value = mock_response
    return mock_client
```

## Testing with Real Credentials

For integration testing with real API calls:

1. Create a `.env.test` file with your test credentials
2. Run tests with the test environment:
   ```bash
   # Load test environment and run tests
   export $(cat .env.test | xargs) && pytest -v src/tests/integration_tests.py
   ```

## Current Test Status

- Unit tests are ready but missing dependencies
- Integration tests are planned but not yet implemented
- Test coverage is currently minimal

## Next Steps

1. Install required dependencies
2. Fix any failing tests
3. Implement integration tests with test repositories
4. Set up continuous integration for automated testing
