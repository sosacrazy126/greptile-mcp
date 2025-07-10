"""
Handler for repository information operations.
"""

from src.models.requests import RepositoryInfoRequest
from src.services.greptile_service import GreptileService


class InfoHandler:
    """Handler for repository information MCP tool."""
    
    def __init__(self, greptile_service: GreptileService):
        self.greptile_service = greptile_service
    
    async def handle_get_repository_info(
        self,
        remote: str,
        repository: str,
        branch: str
    ) -> str:
        """
        Handle the get_repository_info MCP tool call.
        
        Args:
            remote: Repository platform ("github" or "gitlab")
            repository: Repository identifier in "owner/repo" format
            branch: Branch name
            
        Returns:
            JSON string with repository information
        """
        request = RepositoryInfoRequest(
            remote=remote,
            repository=repository,
            branch=branch
        )
        
        return await self.greptile_service.get_repository_info(request)