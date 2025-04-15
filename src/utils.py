import httpx
import os
import urllib.parse

class GreptileClient:
    """Client for interacting with the Greptile API."""
    
    def __init__(self, api_key, github_token, base_url="https://api.greptile.com/v2"):
        """
        Initialize the Greptile API client.
        
        Args:
            api_key: Greptile API key
            github_token: GitHub/GitLab personal access token
            base_url: Base URL for the Greptile API
        """
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "X-GitHub-Token": github_token,
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=60.0)  # Longer timeout for indexing operations
    
    async def aclose(self):
        """Close the underlying HTTPX client."""
        await self.client.aclose()
    
    async def index_repository(self, remote, repository, branch, reload=False, notify=False):
        """
        Index a repository for code search and querying.
        
        Args:
            remote: The repository host, either "github" or "gitlab"
            repository: The repository in owner/repo format
            branch: The branch to index
            reload: Whether to force reprocessing
            notify: Whether to send an email notification
        
        Returns:
            The API response as a dictionary
        """
        url = f"{self.base_url}/repositories"
        payload = {
            "remote": remote,
            "repository": repository,
            "branch": branch,
            "reload": reload,
            "notify": notify
        }
        
        response = await self.client.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    async def query_repositories(self, messages, repositories, session_id=None, stream=False, genius=True):
        """
        Query repositories to get an answer with code references.
        
        Args:
            messages: List of message objects with role and content
            repositories: List of repository objects
            session_id: Optional session ID for continuing a conversation
            stream: Whether to stream the response
            genius: Whether to use enhanced query capabilities
        
        Returns:
            The API response as a dictionary
        """
        url = f"{self.base_url}/query"
        payload = {
            "messages": messages,
            "repositories": repositories,
            "stream": stream,
            "genius": genius
        }
        
        if session_id:
            payload["sessionId"] = session_id
        
        response = await self.client.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    async def search_repositories(self, messages, repositories, session_id=None, genius=True):
        """
        Search repositories for relevant files without generating a full answer.
        
        Args:
            messages: List of message objects with role and content
            repositories: List of repository objects
            session_id: Optional session ID for continuing a conversation
            genius: Whether to use enhanced search capabilities
        
        Returns:
            The API response as a dictionary
        """
        url = f"{self.base_url}/search"
        payload = {
            "messages": messages,
            "repositories": repositories,
            "genius": genius
        }
        
        if session_id:
            payload["sessionId"] = session_id
        
        response = await self.client.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    async def get_repository_info(self, repository_id):
        """
        Get information about an indexed repository.
        
        Args:
            repository_id: Repository ID in the format "remote:branch:owner/repository"
        
        Returns:
            The API response as a dictionary
        """
        encoded_id = urllib.parse.quote(repository_id)
        url = f"{self.base_url}/repositories/{encoded_id}"
        
        response = await self.client.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

def get_greptile_client():
    """
    Create and configure a Greptile API client based on environment variables.
    
    Returns:
        GreptileClient: Configured Greptile API client
    """
    api_key = os.getenv("GREPTILE_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    base_url = os.getenv("GREPTILE_BASE_URL", "https://api.greptile.com/v2")
    
    if not api_key:
        raise ValueError("GREPTILE_API_KEY environment variable is required")
    
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    
    return GreptileClient(api_key, github_token, base_url)