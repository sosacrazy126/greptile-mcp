#!/usr/bin/env python3
"""
Test Parameter Mapping - MCP Tools to GreptileClient
Tests that parameter conversion from MCP tool interface to GreptileClient methods works correctly.
"""

import pytest
import json
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Change to project root for imports
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

class TestParameterMapping:
    """Test parameter mapping between MCP tools and GreptileClient."""
    
    async def test_query_to_messages_conversion(self):
        """Test that query string is correctly converted to messages format."""
        from src.main import query_repository
        
        # Mock the GreptileClient
        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.query_repositories.return_value = {"message": "test response", "sources": []}
            mock_get_client.return_value = mock_client
            
            # Test the conversion
            query = "How does authentication work?"
            repositories = '[{"remote": "github", "repository": "test/repo", "branch": "main"}]'
            
            result = await query_repository(
                query=query,
                repositories=repositories,
                session_id="test-session"
            )
            
            # Verify the client was called with correct messages format
            mock_client.query_repositories.assert_called_once()
            call_args = mock_client.query_repositories.call_args
            
            # Check that messages parameter was passed correctly
            assert 'messages' in call_args.kwargs
            messages = call_args.kwargs['messages']
            assert isinstance(messages, list)
            assert len(messages) == 1
            assert messages[0]['role'] == 'user'
            assert messages[0]['content'] == query
            
            print("✅ Query to messages conversion works correctly")
    
    async def test_previous_messages_merging(self):
        """Test that previous messages are correctly merged with new query."""
        from src.main import query_repository

        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.query_repositories.return_value = {"message": "test response"}
            mock_get_client.return_value = mock_client

            query = "Follow-up question"
            repositories = '[{"remote": "github", "repository": "test/repo", "branch": "main"}]'
            previous_messages = '[{"role": "user", "content": "Previous question"}, {"role": "assistant", "content": "Previous answer"}]'

            await query_repository(
                query=query,
                repositories=repositories,
                previous_messages=previous_messages
            )

            # Verify messages were merged correctly
            call_args = mock_client.query_repositories.call_args
            messages = call_args.kwargs['messages']

            assert len(messages) == 3  # 2 previous + 1 new
            assert messages[0]['content'] == "Previous question"
            assert messages[1]['content'] == "Previous answer"
            assert messages[2]['content'] == query

            print("✅ Previous messages merging works correctly")

    async def test_repositories_json_parsing(self):
        """Test that repositories JSON string is correctly parsed."""
        from main import query_repository

        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.query_repositories.return_value = {"message": "test"}
            mock_get_client.return_value = mock_client

            repositories_json = '[{"remote": "github", "repository": "owner/repo", "branch": "main"}, {"remote": "gitlab", "repository": "other/repo", "branch": "dev"}]'

            await query_repository(
                query="test query",
                repositories=repositories_json
            )

            # Verify repositories were parsed correctly
            call_args = mock_client.query_repositories.call_args
            repositories = call_args.kwargs['repositories']

            assert isinstance(repositories, list)
            assert len(repositories) == 2
            assert repositories[0]['remote'] == 'github'
            assert repositories[1]['remote'] == 'gitlab'

            print("✅ Repositories JSON parsing works correctly")

    async def test_search_repository_mapping(self):
        """Test parameter mapping for search_repository function."""
        from main import search_repository

        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search_repositories.return_value = {"files": []}
            mock_get_client.return_value = mock_client

            await search_repository(
                query="test search",
                repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]'
            )

            # Verify correct parameter mapping
            mock_client.search_repositories.assert_called_once()
            call_args = mock_client.search_repositories.call_args

            assert 'messages' in call_args.kwargs
            assert 'repositories' in call_args.kwargs

            messages = call_args.kwargs['messages']
            assert messages[0]['content'] == "test search"

            print("✅ Search repository parameter mapping works correctly")

    async def test_json_error_handling(self):
        """Test that invalid JSON parameters are handled gracefully."""
        from main import query_repository

        # Test with invalid JSON
        result = await query_repository(
            query="test",
            repositories='{"invalid": json}'  # Invalid JSON
        )

        # Should return error response
        result_dict = json.loads(result)
        assert 'error' in result_dict
        assert 'JSONDecodeError' in result_dict['error']

        print("✅ JSON error handling works correctly")

    async def test_return_value_serialization(self):
        """Test that return values are properly serialized to JSON."""
        from main import query_repository
        
        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_response = {
                "message": "Test response",
                "sources": [{"file": "test.py", "line": 10}]
            }
            mock_client.query_repositories.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = await query_repository(
                query="test",
                repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]'
            )
            
            # Verify result is valid JSON string
            assert isinstance(result, str)
            result_dict = json.loads(result)
            assert result_dict['message'] == "Test response"
            assert 'session_id' in result_dict
            
            print("✅ Return value serialization works correctly")

if __name__ == "__main__":
    import asyncio
    
    async def run_tests():
        test = TestParameterMapping()
        
        print("🧪 Running Parameter Mapping Tests...")
        print("=" * 50)
        
        try:
            await test.test_query_to_messages_conversion()
            await test.test_previous_messages_merging()
            await test.test_repositories_json_parsing()
            await test.test_search_repository_mapping()
            await test.test_json_error_handling()
            await test.test_return_value_serialization()
            
            print("\n" + "=" * 50)
            print("🎉 All Parameter Mapping Tests PASSED!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True
    
    success = asyncio.run(run_tests())
    if not success:
        sys.exit(1)
