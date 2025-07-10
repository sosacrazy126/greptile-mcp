"""
Core service for Greptile API operations and business logic.
"""

import json
import os
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
from src.utils import GreptileClient, get_greptile_client
from src.models.requests import IndexRequest, QueryRequest, SearchRequest, RepositoryInfoRequest, Repository
from src.models.responses import GreptileContext
from .session_service import SessionService


class GreptileService:
    """Core service for Greptile API operations."""
    
    def __init__(self, session_service: SessionService):
        self.session_service = session_service
        self._client: Optional[GreptileClient] = None
    
    async def get_client(self) -> GreptileClient:
        """Get or create the Greptile client instance."""
        if self._client is None:
            self._client = get_greptile_client()
        return self._client
    
    async def close_client(self) -> None:
        """Close the Greptile client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def index_repository(self, request: IndexRequest) -> str:
        """
        Index a repository for code search and querying.
        
        Args:
            request: IndexRequest containing repository details
            
        Returns:
            JSON string with indexing status
        """
        try:
            client = await self.get_client()
            result = await client.index_repository(
                remote=request.remote,
                repository=request.repository,
                branch=request.branch,
                reload=request.reload,
                notify=request.notify
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({
                "error": str(e), 
                "type": type(e).__name__
            }, indent=2)
    
    async def query_repository(self, request: QueryRequest) -> str:
        """
        Query repositories with natural language.
        
        Args:
            request: QueryRequest containing query details
            
        Returns:
            JSON string response or async generator for streaming
        """
        try:
            client = await self.get_client()
            
            # Convert Repository objects to dict format expected by client
            repositories_dict = [
                {
                    "remote": repo.remote,
                    "repository": repo.repository,
                    "branch": repo.branch
                }
                for repo in request.repositories
            ]
            
            # Prepare messages - if not provided, create from query
            if request.messages:
                messages = self.session_service.format_messages_for_api(request.messages)
            else:
                messages = self.session_service.format_messages_for_api([], request.query)
            
            # Generate session ID if not provided
            session_id = request.session_id
            if not session_id:
                session_id = self.session_service.generate_session_id()
            
            # Make API call (for now, handle only non-streaming)
            result = await client.query_repositories(
                messages=messages,
                repositories=repositories_dict,
                session_id=session_id,
                stream=False,  # Force non-streaming for now
                genius=request.genius,
                timeout=request.timeout
            )
            
            # Add session metadata and return
            return self.session_service.add_session_metadata(result, session_id)
                
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "type": type(e).__name__
            }, indent=2)
    
    async def search_repository(self, request: SearchRequest) -> str:
        """
        Search repositories for relevant files.
        
        Args:
            request: SearchRequest containing search details
            
        Returns:
            JSON string with search results
        """
        try:
            client = await self.get_client()
            
            # Convert Repository objects to dict format
            repositories_dict = [
                {
                    "remote": repo.remote,
                    "repository": repo.repository,
                    "branch": repo.branch
                }
                for repo in request.repositories
            ]
            
            # Format messages
            messages = self.session_service.format_messages_for_api([], request.query)
            
            # Generate session ID if not provided
            session_id = request.session_id
            if not session_id:
                session_id = self.session_service.generate_session_id()
            
            # Make API call
            result = await client.search_repositories(
                messages=messages,
                repositories=repositories_dict,
                session_id=session_id,
                genius=request.genius
            )
            
            # Add session metadata and return
            return self.session_service.add_session_metadata(result, session_id)
            
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "type": type(e).__name__
            }, indent=2)
    
    async def get_repository_info(self, request: RepositoryInfoRequest) -> str:
        """
        Get information about an indexed repository.
        
        Args:
            request: RepositoryInfoRequest containing repository details
            
        Returns:
            JSON string with repository information
        """
        try:
            client = await self.get_client()
            
            # Format repository ID as expected by API
            repository_id = f"{request.remote}:{request.branch}:{request.repository}"
            
            result = await client.get_repository_info(repository_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "type": type(e).__name__
            }, indent=2)
    
    def parse_repositories_from_string(self, repositories_str: str) -> List[Repository]:
        """
        Parse repositories from JSON string format.
        
        Args:
            repositories_str: JSON string containing repository list
            
        Returns:
            List of Repository objects
        """
        try:
            repos_data = json.loads(repositories_str)
            if not isinstance(repos_data, list):
                raise ValueError("Repositories must be a list")
            
            repositories = []
            for repo_data in repos_data:
                if not isinstance(repo_data, dict):
                    raise ValueError("Each repository must be a dictionary")
                
                # Validate required fields
                required_fields = ["remote", "repository", "branch"]
                for field in required_fields:
                    if field not in repo_data:
                        raise ValueError(f"Missing required field: {field}")
                
                repositories.append(Repository(
                    remote=repo_data["remote"],
                    repository=repo_data["repository"],
                    branch=repo_data["branch"]
                ))
            
            return repositories
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing repositories: {str(e)}")