"""
Response models and context classes for Greptile MCP server.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class GreptileContext:
    """Context for the Greptile MCP server."""
    greptile_client: Any  # GreptileClient from utils
    initialized: bool = False
    session_manager: Optional[Any] = None  # SessionManager from utils
    default_session_id: str = "7dc8f451-9bf7-4262-a664-0865ac578e6c"


@dataclass
class Source:
    """Source reference from Greptile API response."""
    repository: str
    remote: str
    branch: str
    filepath: str
    linestart: int
    lineend: int
    summary: str


@dataclass
class QueryResponse:
    """Response model for repository queries."""
    message: str
    sources: List[Source]
    session_id: Optional[str] = None


@dataclass
class SearchResponse:
    """Response model for repository searches."""
    files: List[Dict[str, Any]]
    session_id: Optional[str] = None


@dataclass
class IndexResponse:
    """Response model for repository indexing."""
    message: str
    status_endpoint: Optional[str] = None
    status: Optional[str] = None


@dataclass
class RepositoryInfoResponse:
    """Response model for repository information."""
    status: str
    repository: str
    branch: str
    last_indexed: Optional[str] = None
    files_processed: Optional[int] = None