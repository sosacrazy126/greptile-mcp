"""
Handler for repository indexing operations.
"""

from typing import Optional
from src.models.requests import IndexRequest
from src.services.greptile_service import GreptileService


class IndexHandler:
    """Handler for repository indexing MCP tool."""
    
    def __init__(self, greptile_service: GreptileService):
        self.greptile_service = greptile_service
    
    async def handle_index_repository(
        self,
        remote: str,
        repository: str,
        branch: str,
        reload: bool = True,
        notify: bool = False
    ) -> str:
        """
        Handle the index_repository MCP tool call.
        
        Args:
            remote: Repository platform ("github" or "gitlab")
            repository: Repository identifier in "owner/repo" format
            branch: Target branch name
            reload: Force re-index latest commits
            notify: Email notification when indexing completes
            
        Returns:
            JSON string with indexing status
        """
        request = IndexRequest(
            remote=remote,
            repository=repository,
            branch=branch,
            reload=reload,
            notify=notify
        )
        
        return await self.greptile_service.index_repository(request)