"""
Request models for Greptile MCP server operations.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class Repository:
    """Repository specification for Greptile operations."""
    remote: str  # "github" or "gitlab"
    repository: str  # "owner/repo" format
    branch: str  # branch name


@dataclass
class IndexRequest:
    """Request model for repository indexing."""
    remote: str
    repository: str
    branch: str
    reload: bool = True
    notify: bool = False


@dataclass
class QueryRequest:
    """Request model for repository queries."""
    query: str
    repositories: List[Repository]
    session_id: Optional[str] = None
    stream: bool = False
    genius: bool = True
    timeout: Optional[float] = None
    messages: Optional[List[Dict[str, str]]] = None


@dataclass
class SearchRequest:
    """Request model for repository searches."""
    query: str
    repositories: List[Repository]
    session_id: Optional[str] = None
    genius: bool = True


@dataclass
class RepositoryInfoRequest:
    """Request model for repository information retrieval."""
    remote: str
    repository: str
    branch: str