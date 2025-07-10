"""
Handler for repository search operations.
"""

from typing import Optional
from src.models.requests import SearchRequest
from src.services.greptile_service import GreptileService


class SearchHandler:
    """Handler for repository search MCP tool."""
    
    def __init__(self, greptile_service: GreptileService):
        self.greptile_service = greptile_service
    
    async def handle_search_repository(
        self,
        query: str,
        repositories: str,  # JSON string format for MCP compatibility
        session_id: Optional[str] = None,
        genius: bool = True
    ) -> str:
        """
        Handle the search_repository MCP tool call.
        
        Args:
            query: Search query about the codebase
            repositories: JSON string containing repository list
            session_id: Optional session ID for conversation continuity
            genius: Whether to use enhanced search capabilities
            
        Returns:
            JSON string with search results
        """
        try:
            # Parse repositories from JSON string
            repo_objects = self.greptile_service.parse_repositories_from_string(repositories)
            
            # Create request object
            request = SearchRequest(
                query=query,
                repositories=repo_objects,
                session_id=session_id,
                genius=genius
            )
            
            return await self.greptile_service.search_repository(request)
            
        except ValueError as e:
            import json
            return json.dumps({
                "error": f"Invalid repositories format: {str(e)}",
                "type": "ValidationError"
            }, indent=2)
        except Exception as e:
            import json
            return json.dumps({
                "error": str(e),
                "type": type(e).__name__
            }, indent=2)