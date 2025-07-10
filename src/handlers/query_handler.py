"""
Handler for repository query operations.
"""

from typing import List, Dict, Any, Optional
from src.models.requests import QueryRequest
from src.services.greptile_service import GreptileService


class QueryHandler:
    """Handler for repository query MCP tools."""
    
    def __init__(self, greptile_service: GreptileService):
        self.greptile_service = greptile_service
    
    async def handle_query_repository(
        self,
        query: str,
        repositories: str,  # JSON string format for MCP compatibility
        session_id: Optional[str] = None,
        stream: bool = False,
        genius: bool = True,
        timeout: Optional[float] = None,
        messages: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Handle the query_repository MCP tool call.
        
        Args:
            query: Natural language query about the codebase
            repositories: JSON string containing repository list
            session_id: Optional session ID for conversation continuity
            stream: Whether to stream the response
            genius: Whether to use enhanced query capabilities
            timeout: Optional request timeout in seconds
            messages: Optional custom message history
            
        Returns:
            JSON string with query results
        """
        try:
            # Parse repositories from JSON string
            repo_objects = self.greptile_service.parse_repositories_from_string(repositories)
            
            # Create request object
            request = QueryRequest(
                query=query,
                repositories=repo_objects,
                session_id=session_id,
                stream=stream,
                genius=genius,
                timeout=timeout,
                messages=messages
            )
            
            return await self.greptile_service.query_repository(request)
            
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