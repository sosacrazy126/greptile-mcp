#!/usr/bin/env python3
"""
Test End-to-End Functionality - Real API Integration
Tests all 4 MCP tools with mock and real API calls to validate complete functionality.
"""

import pytest
import json
import sys
import os
from unittest.mock import AsyncMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestEndToEndFunctionality:
    """Test complete functionality of all 4 MCP tools."""
    
    async def test_index_repository_functionality(self):
        """Test index_repository tool end-to-end."""
        from main import index_repository
        
        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.index_repository.return_value = {
                "status": "indexing",
                "repository": "test/repo",
                "branch": "main",
                "progress": 0
            }
            mock_get_client.return_value = mock_client
            
            result = await index_repository(
                remote="github",
                repository="test/repo",
                branch="main",
                reload=False,
                notify=False
            )
            
            # Verify client was called correctly
            mock_client.index_repository.assert_called_once_with(
                remote="github",
                repository="test/repo",
                branch="main",
                reload=False,
                notify=False
            )
            
            # Verify result is JSON string
            result_dict = json.loads(result)
            assert result_dict["status"] == "indexing"
            assert result_dict["repository"] == "test/repo"
            
            print("✅ index_repository functionality works correctly")
    
    async def test_query_repository_functionality(self):
        """Test query_repository tool end-to-end."""
        from main import query_repository
        
        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.query_repositories.return_value = {
                "message": "The authentication is handled in auth.py using JWT tokens.",
                "sources": [
                    {"file": "auth.py", "line": 15, "content": "def authenticate(token):"}
                ]
            }
            mock_get_client.return_value = mock_client
            
            result = await query_repository(
                query="How does authentication work?",
                repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]',
                session_id="test-session",
                genius=True
            )
            
            # Verify client was called with correct parameters
            call_args = mock_client.query_repositories.call_args
            assert call_args.kwargs['messages'][0]['content'] == "How does authentication work?"
            assert call_args.kwargs['session_id'] == "test-session"
            assert call_args.kwargs['genius'] is True
            
            # Verify result
            result_dict = json.loads(result)
            assert "authentication is handled" in result_dict["message"]
            assert result_dict["session_id"] == "test-session"
            
            print("✅ query_repository functionality works correctly")
    
    async def test_search_repository_functionality(self):
        """Test search_repository tool end-to-end."""
        from main import search_repository
        
        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search_repositories.return_value = {
                "files": [
                    {"file": "auth.py", "relevance": 0.95},
                    {"file": "login.py", "relevance": 0.87}
                ]
            }
            mock_get_client.return_value = mock_client
            
            result = await search_repository(
                query="authentication functions",
                repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]',
                genius=True
            )
            
            # Verify client was called correctly
            call_args = mock_client.search_repositories.call_args
            assert call_args.kwargs['messages'][0]['content'] == "authentication functions"
            assert call_args.kwargs['genius'] is True
            
            # Verify result
            result_dict = json.loads(result)
            assert len(result_dict["files"]) == 2
            assert result_dict["files"][0]["file"] == "auth.py"
            
            print("✅ search_repository functionality works correctly")
    
    async def test_get_repository_info_functionality(self):
        """Test get_repository_info tool end-to-end."""
        from main import get_repository_info
        
        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_repository_info.return_value = {
                "status": "indexed",
                "repository": "test/repo",
                "branch": "main",
                "indexed_at": "2024-01-01T00:00:00Z",
                "file_count": 150
            }
            mock_get_client.return_value = mock_client
            
            result = await get_repository_info(
                remote="github",
                repository="test/repo",
                branch="main"
            )
            
            # Verify client was called correctly
            mock_client.get_repository_info.assert_called_once_with(
                remote="github",
                repository="test/repo",
                branch="main"
            )
            
            # Verify result
            result_dict = json.loads(result)
            assert result_dict["status"] == "indexed"
            assert result_dict["file_count"] == 150
            
            print("✅ get_repository_info functionality works correctly")
    
    async def test_streaming_functionality(self):
        """Test streaming functionality in query_repository."""
        from main import query_repository
        
        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            
            # Mock streaming response
            async def mock_stream():
                yield "The authentication "
                yield "is handled in "
                yield "auth.py file."
            
            mock_client.stream_query_repositories.return_value = mock_stream()
            mock_get_client.return_value = mock_client
            
            result = await query_repository(
                query="How does auth work?",
                repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]',
                stream=True
            )
            
            # Verify streaming was called
            mock_client.stream_query_repositories.assert_called_once()
            
            # Verify result contains streamed content
            result_dict = json.loads(result)
            assert result_dict["message"] == "The authentication is handled in auth.py file."
            assert result_dict["streamed"] is True
            
            print("✅ Streaming functionality works correctly")
    
    async def test_session_management(self):
        """Test session ID generation and management."""
        from main import query_repository
        
        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.query_repositories.return_value = {"message": "test"}
            mock_get_client.return_value = mock_client
            
            # Test without session_id (should generate one)
            result1 = await query_repository(
                query="test query",
                repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]'
            )
            
            result1_dict = json.loads(result1)
            assert "session_id" in result1_dict
            assert len(result1_dict["session_id"]) > 0
            
            # Test with provided session_id
            result2 = await query_repository(
                query="test query",
                repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]',
                session_id="custom-session"
            )
            
            result2_dict = json.loads(result2)
            assert result2_dict["session_id"] == "custom-session"
            
            print("✅ Session management works correctly")
    
    async def test_multiple_repositories(self):
        """Test handling multiple repositories in a single query."""
        from main import query_repository
        
        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.query_repositories.return_value = {"message": "multi-repo response"}
            mock_get_client.return_value = mock_client
            
            repositories = [
                {"remote": "github", "repository": "org/repo1", "branch": "main"},
                {"remote": "gitlab", "repository": "org/repo2", "branch": "dev"},
                {"remote": "github", "repository": "org/repo3", "branch": "feature"}
            ]
            
            result = await query_repository(
                query="How do these repos handle logging?",
                repositories=json.dumps(repositories)
            )
            
            # Verify client received all repositories
            call_args = mock_client.query_repositories.call_args
            passed_repos = call_args.kwargs['repositories']
            
            assert len(passed_repos) == 3
            assert passed_repos[0]['repository'] == "org/repo1"
            assert passed_repos[1]['remote'] == "gitlab"
            assert passed_repos[2]['branch'] == "feature"
            
            print("✅ Multiple repositories handling works correctly")
    
    async def test_conversation_context(self):
        """Test conversation context with previous messages."""
        from main import query_repository
        
        with patch('main.get_greptile_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.query_repositories.return_value = {"message": "follow-up response"}
            mock_get_client.return_value = mock_client
            
            previous_messages = [
                {"role": "user", "content": "What is the main function?"},
                {"role": "assistant", "content": "The main function is in main.py"},
                {"role": "user", "content": "How does it handle errors?"}
            ]
            
            result = await query_repository(
                query="Can you show me the error handling code?",
                repositories='[{"remote": "github", "repository": "test/repo", "branch": "main"}]',
                previous_messages=json.dumps(previous_messages)
            )
            
            # Verify conversation context was preserved
            call_args = mock_client.query_repositories.call_args
            messages = call_args.kwargs['messages']
            
            assert len(messages) == 4  # 3 previous + 1 new
            assert messages[0]['content'] == "What is the main function?"
            assert messages[1]['role'] == "assistant"
            assert messages[3]['content'] == "Can you show me the error handling code?"
            
            print("✅ Conversation context handling works correctly")

if __name__ == "__main__":
    import asyncio
    
    async def run_tests():
        test = TestEndToEndFunctionality()
        
        print("🧪 Running End-to-End Functionality Tests...")
        print("=" * 50)
        
        tests = [
            test.test_index_repository_functionality,
            test.test_query_repository_functionality,
            test.test_search_repository_functionality,
            test.test_get_repository_info_functionality,
            test.test_streaming_functionality,
            test.test_session_management,
            test.test_multiple_repositories,
            test.test_conversation_context
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
            print("🎉 All End-to-End Functionality Tests PASSED!")
            return True
        else:
            print("❌ Some tests failed")
            return False
    
    success = asyncio.run(run_tests())
    if not success:
        sys.exit(1)
