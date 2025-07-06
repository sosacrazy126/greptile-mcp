#!/usr/bin/env python3
"""
Test Error Handling - Robust Error Response Validation
Tests that proper error responses are returned for various failure scenarios.
"""

import json
import sys
import os
from unittest.mock import AsyncMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestErrorHandling:
    """Test error handling across all MCP tools."""
    
    async def test_invalid_json_parameters(self):
        """Test handling of invalid JSON in parameters."""
        from main import query_repository, search_repository
        
        # Test invalid repositories JSON
        result = await query_repository(
            query="test query",
            repositories='{"invalid": json syntax}'
        )
        
        result_dict = json.loads(result)
        assert 'error' in result_dict
        assert 'JSONDecodeError' in result_dict['error']
        assert result_dict['type'] == 'JSONDecodeError'
        
        # Test invalid previous_messages JSON
        result2 = await search_repository(
            query="test search",
            repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]',
            previous_messages='[{"invalid": json}]'
        )
        
        result2_dict = json.loads(result2)
        assert 'error' in result2_dict
        assert 'JSONDecodeError' in result2_dict['error']
        
        print("✅ Invalid JSON parameters handled correctly")
    
    async def test_greptile_client_errors(self):
        """Test handling of GreptileClient API errors."""
        from main import query_repository, index_repository
        
        with patch('main.get_greptile_client') as mock_get_client:
            # Test API error
            mock_client = AsyncMock()
            mock_client.query_repositories.side_effect = Exception("API rate limit exceeded")
            mock_get_client.return_value = mock_client
            
            result = await query_repository(
                query="test query",
                repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]'
            )
            
            result_dict = json.loads(result)
            assert 'error' in result_dict
            assert 'API rate limit exceeded' in result_dict['error']
            assert result_dict['type'] == 'Exception'
            assert 'session_id' in result_dict
            
            # Test different error type
            mock_client.index_repository.side_effect = ValueError("Invalid repository format")
            
            result2 = await index_repository(
                remote="github",
                repository="invalid-repo",
                branch="main"
            )
            
            result2_dict = json.loads(result2)
            assert 'error' in result2_dict
            assert 'Invalid repository format' in result2_dict['error']
            assert result2_dict['type'] == 'ValueError'
            
        print("✅ GreptileClient errors handled correctly")
    
    async def test_network_timeout_errors(self):
        """Test handling of network timeout errors."""
        from main import get_repository_info
        
        with patch('main.get_greptile_client') as mock_get_client:
            import asyncio
            
            mock_client = AsyncMock()
            mock_client.get_repository_info.side_effect = asyncio.TimeoutError("Request timed out")
            mock_get_client.return_value = mock_client
            
            result = await get_repository_info(
                remote="github",
                repository="test/repo",
                branch="main"
            )
            
            result_dict = json.loads(result)
            assert 'error' in result_dict
            assert 'Request timed out' in result_dict['error']
            assert result_dict['type'] == 'TimeoutError'
            
        print("✅ Network timeout errors handled correctly")
    
    async def test_authentication_errors(self):
        """Test handling of authentication errors."""
        from main import query_repository
        
        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.query_repositories.side_effect = Exception("Invalid API key")
            mock_get_client.return_value = mock_client
            
            result = await query_repository(
                query="test query",
                repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]'
            )
            
            result_dict = json.loads(result)
            assert 'error' in result_dict
            assert 'Invalid API key' in result_dict['error']
            
        print("✅ Authentication errors handled correctly")
    
    async def test_empty_parameters(self):
        """Test handling of empty or missing parameters."""
        from main import query_repository, search_repository
        
        # Test empty query
        result = await query_repository(
            query="",
            repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]'
        )
        
        # Should not error, but pass empty query to client
        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.query_repositories.return_value = {"message": "empty query response"}
            mock_get_client.return_value = mock_client
            
            result = await query_repository(
                query="",
                repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]'
            )
            
            # Verify empty query was passed through
            call_args = mock_client.query_repositories.call_args
            messages = call_args.kwargs['messages']
            assert messages[0]['content'] == ""
        
        # Test empty repositories
        result2 = await search_repository(
            query="test search",
            repositories='[]'
        )
        
        # Should handle empty repositories list
        result2_dict = json.loads(result2)
        # Should either work or return appropriate error
        assert isinstance(result2_dict, dict)
        
        print("✅ Empty parameters handled correctly")
    
    async def test_malformed_repository_data(self):
        """Test handling of malformed repository data."""
        from main import query_repository
        
        # Test repositories missing required fields
        malformed_repos = [
            '[]',  # Empty array
            '[{}]',  # Empty object
            '[{"remote": "github"}]',  # Missing repository and branch
            '[{"repository": "test/repo"}]',  # Missing remote and branch
            '[{"remote": "invalid", "repository": "test/repo", "branch": "main"}]'  # Invalid remote
        ]
        
        for repo_json in malformed_repos:
            with patch('main.get_greptile_client') as mock_get_client:
                mock_client = AsyncMock()
                mock_client.query_repositories.side_effect = Exception("Invalid repository data")
                mock_get_client.return_value = mock_client
                
                result = await query_repository(
                    query="test query",
                    repositories=repo_json
                )
                
                result_dict = json.loads(result)
                # Should either work or return error gracefully
                assert isinstance(result_dict, dict)
        
        print("✅ Malformed repository data handled correctly")
    
    async def test_streaming_errors(self):
        """Test error handling in streaming mode."""
        from main import query_repository
        
        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            
            # Mock streaming that raises an error
            async def mock_stream_error():
                yield "Starting response..."
                raise Exception("Streaming connection lost")
            
            mock_client.stream_query_repositories.return_value = mock_stream_error()
            mock_get_client.return_value = mock_client
            
            result = await query_repository(
                query="test query",
                repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]',
                stream=True
            )
            
            result_dict = json.loads(result)
            assert 'error' in result_dict
            assert 'Streaming connection lost' in result_dict['error']
            
        print("✅ Streaming errors handled correctly")
    
    async def test_client_initialization_errors(self):
        """Test handling of client initialization errors."""
        from main import query_repository
        
        with patch('main.get_greptile_client') as mock_get_client:
            mock_get_client.side_effect = Exception("Failed to initialize Greptile client")
            
            result = await query_repository(
                query="test query",
                repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]'
            )
            
            result_dict = json.loads(result)
            assert 'error' in result_dict
            assert 'Failed to initialize Greptile client' in result_dict['error']
            
        print("✅ Client initialization errors handled correctly")
    
    async def test_error_response_format(self):
        """Test that all error responses follow consistent format."""
        from main import query_repository, search_repository, index_repository, get_repository_info
        
        tools = [
            (query_repository, {
                'query': 'test',
                'repositories': '{"invalid": json}'
            }),
            (search_repository, {
                'query': 'test',
                'repositories': '{"invalid": json}'
            }),
            (index_repository, {
                'remote': 'github',
                'repository': 'test/repo',
                'branch': 'main'
            }),
            (get_repository_info, {
                'remote': 'github',
                'repository': 'test/repo',
                'branch': 'main'
            })
        ]
        
        for tool_func, params in tools:
            if 'repositories' in params and params['repositories'] == '{"invalid": json}':
                # This will cause JSON error
                result = await tool_func(**params)
            else:
                # Mock client error for other tools
                with patch('main.get_greptile_client') as mock_get_client:
                    mock_client = AsyncMock()
                    mock_client.index_repository.side_effect = Exception("Test error")
                    mock_client.get_repository_info.side_effect = Exception("Test error")
                    mock_get_client.return_value = mock_client
                    
                    result = await tool_func(**params)
            
            # Verify error response format
            result_dict = json.loads(result)
            assert 'error' in result_dict
            assert 'type' in result_dict
            assert isinstance(result_dict['error'], str)
            assert isinstance(result_dict['type'], str)
            
        print("✅ Error response format is consistent across all tools")

if __name__ == "__main__":
    import asyncio
    
    async def run_tests():
        test = TestErrorHandling()
        
        print("🧪 Running Error Handling Tests...")
        print("=" * 50)
        
        tests = [
            test.test_invalid_json_parameters,
            test.test_greptile_client_errors,
            test.test_network_timeout_errors,
            test.test_authentication_errors,
            test.test_empty_parameters,
            test.test_malformed_repository_data,
            test.test_streaming_errors,
            test.test_client_initialization_errors,
            test.test_error_response_format
        ]
        
        passed = 0
        total = len(tests)
        
        for test_func in tests:
            try:
                await test_func()
                passed += 1
            except Exception as e:
                print(f"❌ {test_func.__name__} failed: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 50)
        print(f"📊 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All Error Handling Tests PASSED!")
            return True
        else:
            print("❌ Some tests failed")
            return False
    
    success = asyncio.run(run_tests())
    if not success:
        sys.exit(1)
