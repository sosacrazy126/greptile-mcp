import httpx
import os
import urllib.parse
import uuid
import json
import asyncio
import logging
from typing import Dict, List, Optional, AsyncGenerator, Any, Union
from httpx import HTTPStatusError, Response, AsyncClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GreptileClient:
    """Client for interacting with the Greptile API with enhanced features."""
    
    def __init__(self, 
                api_key: str, 
                github_token: str, 
                base_url: str = "https://api.greptile.com/v2",
                default_timeout: float = 60.0):
        """
        Initialize the Greptile API client.
        
        Args:
            api_key: Greptile API key
            github_token: GitHub/GitLab personal access token
            base_url: Base URL for the Greptile API
            default_timeout: Default timeout for API calls in seconds
        """
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "X-GitHub-Token": github_token,
            "Content-Type": "application/json"
        }
        self.default_timeout = default_timeout
        self.client = httpx.AsyncClient(timeout=default_timeout)
        
        # In-memory session cache for conversation context
        self._session_cache: Dict[str, List[Dict[str, str]]] = {}
        
        # Rate limiting configuration
        self.max_retries = 5
        self.retry_base_delay = 1.0  # Base delay in seconds
        
    async def aclose(self):
        """Close the underlying HTTPX client."""
        await self.client.aclose()
    
    async def _make_request(self, 
                           method: str, 
                           url: str, 
                           json_data: Optional[Dict] = None, 
                           params: Optional[Dict] = None,
                           timeout: Optional[float] = None,
                           handle_rate_limit: bool = True) -> Response:
        """
        Make an API request with rate limit handling and retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            json_data: JSON data to send
            params: URL parameters
            timeout: Custom timeout for this request
            handle_rate_limit: Whether to handle rate limiting with retries
            
        Returns:
            Response object
            
        Raises:
            HTTPStatusError: If the request fails
        """
        if timeout is not None:
            # Create a new client with the specified timeout just for this request
            async with httpx.AsyncClient(timeout=timeout, headers=self.headers) as client:
                request_client = client
        else:
            # Use the default client
            request_client = self.client
            
        retries = 0
        while True:
            try:
                if method.upper() == "GET":
                    response = await request_client.get(url, params=params, headers=self.headers)
                elif method.upper() == "POST":
                    response = await request_client.post(url, json=json_data, headers=self.headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response
                
            except HTTPStatusError as e:
                # Handle rate limiting
                if e.response.status_code == 429 and handle_rate_limit and retries < self.max_retries:
                    retries += 1
                    # Get retry-after header or use exponential backoff
                    retry_after = e.response.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        delay = float(retry_after)
                    else:
                        # Exponential backoff with jitter
                        delay = self.retry_base_delay * (2 ** retries) * (0.8 + 0.4 * (asyncio.get_event_loop().time() % 1))
                        
                    logger.warning(f"Rate limited. Retrying after {delay:.2f} seconds (attempt {retries}/{self.max_retries})")
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Re-raise the exception for other errors or if max retries exceeded
                    raise
    
    async def index_repository(self, 
                              remote: str, 
                              repository: str, 
                              branch: str, 
                              reload: bool = False, 
                              notify: bool = False,
                              timeout: Optional[float] = None) -> Dict:
        """
        Index a repository for code search and querying.
        
        Args:
            remote: The repository host, either "github" or "gitlab"
            repository: The repository in owner/repo format
            branch: The branch to index
            reload: Whether to force reprocessing
            notify: Whether to send an email notification
            timeout: Custom timeout for this request in seconds
        
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
        
        response = await self._make_request("POST", url, json_data=payload, timeout=timeout)
        return response.json()
    
    async def query_repositories_stream(self, 
                                      messages: List[Dict[str, str]], 
                                      repositories: List[Dict[str, str]], 
                                      session_id: Optional[str] = None, 
                                      genius: bool = True,
                                      timeout: Optional[float] = None) -> AsyncGenerator[Dict, None]:
        """
        Query repositories with streaming response.
        
        Args:
            messages: List of message objects with role and content
            repositories: List of repository objects
            session_id: Optional session ID for continuing a conversation
            genius: Whether to use enhanced query capabilities
            timeout: Custom timeout for this request in seconds
        
        Yields:
            Chunks of the API response as they are received
        """
        url = f"{self.base_url}/query"
        payload = {
            "messages": messages,
            "repositories": repositories,
            "stream": True,
            "genius": genius
        }
        
        if session_id:
            payload["sessionId"] = session_id
            
            # Update session cache with the current messages
            if session_id in self._session_cache:
                # Add only new messages to avoid duplication
                existing_messages = {msg.get("id", idx): msg 
                                   for idx, msg in enumerate(self._session_cache[session_id])}
                
                for msg in messages:
                    msg_id = msg.get("id", f"msg-{len(existing_messages)}")
                    if msg_id not in existing_messages:
                        self._session_cache[session_id].append(msg)
            else:
                self._session_cache[session_id] = messages.copy()
        
        # Use a custom client with the specified timeout for streaming
        timeout_settings = httpx.Timeout(timeout or self.default_timeout)
        async with httpx.AsyncClient(timeout=timeout_settings) as client:
            try:
                async with client.stream("POST", url, json=payload, headers=self.headers) as response:
                    response.raise_for_status()
                    
                    # Process the stream
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        
                        # Try to parse complete JSON objects from the buffer
                        while True:
                            try:
                                # Find the position of the first complete JSON object
                                json_end = buffer.find("}")
                                if json_end == -1:
                                    break
                                    
                                # Extract and parse the JSON object
                                json_str = buffer[:json_end + 1]
                                data = json.loads(json_str)
                                
                                # Update the buffer
                                buffer = buffer[json_end + 1:]
                                
                                # Yield the parsed data
                                yield data
                            except json.JSONDecodeError:
                                # If we can't parse a complete JSON object, wait for more data
                                break
                    
                    # Process any remaining data in the buffer
                    if buffer.strip():
                        try:
                            yield json.loads(buffer)
                        except json.JSONDecodeError:
                            # If we can't parse the remaining data, log a warning
                            logger.warning(f"Failed to parse remaining data in stream: {buffer}")
            except HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Handle rate limiting for streaming
                    retry_after = e.response.headers.get("Retry-After", "60")
                    if retry_after.isdigit():
                        retry_seconds = int(retry_after)
                    else:
                        retry_seconds = 60
                        
                    logger.warning(f"Rate limited during streaming. Retry after {retry_seconds} seconds")
                    yield {"error": "rate_limited", "retry_after": retry_seconds}
                else:
                    # Re-raise other errors
                    raise
    
    async def query_repositories(self, 
                              messages: List[Dict[str, str]], 
                              repositories: List[Dict[str, str]], 
                              session_id: Optional[str] = None, 
                              stream: bool = False, 
                              genius: bool = True,
                              timeout: Optional[float] = None) -> Union[Dict, AsyncGenerator[Dict, None]]:
        """
        Query repositories to get an answer with code references.
        
        Args:
            messages: List of message objects with role and content
            repositories: List of repository objects
            session_id: Optional session ID for continuing a conversation
            stream: Whether to stream the response
            genius: Whether to use enhanced query capabilities
            timeout: Custom timeout for this request in seconds
        
        Returns:
            The API response as a dictionary if stream=False,
            or an AsyncGenerator yielding chunks if stream=True
        """
        if stream:
            # Return streaming response
            return self.query_repositories_stream(
                messages, repositories, session_id, genius, timeout
            )
            
        url = f"{self.base_url}/query"
        payload = {
            "messages": messages,
            "repositories": repositories,
            "stream": False,
            "genius": genius
        }
        
        if session_id:
            payload["sessionId"] = session_id
            
            # Update session cache with the current messages
            if session_id in self._session_cache:
                # Add only new messages to avoid duplication
                existing_messages = {msg.get("id", idx): msg 
                                   for idx, msg in enumerate(self._session_cache[session_id])}
                
                for msg in messages:
                    msg_id = msg.get("id", f"msg-{len(existing_messages)}")
                    if msg_id not in existing_messages:
                        self._session_cache[session_id].append(msg)
            else:
                self._session_cache[session_id] = messages.copy()
        
        response = await self._make_request("POST", url, json_data=payload, timeout=timeout)
        result = response.json()
        
        # If this is a session, store the assistant response in the session cache
        if session_id and "message" in result:
            assistant_message = {
                "role": "assistant",
                "content": result["message"]
            }
            if session_id in self._session_cache:
                self._session_cache[session_id].append(assistant_message)
            else:
                self._session_cache[session_id] = [assistant_message]
                
        return result
    
    async def search_repositories(self, 
                               messages: List[Dict[str, str]], 
                               repositories: List[Dict[str, str]], 
                               session_id: Optional[str] = None, 
                               genius: bool = True,
                               timeout: Optional[float] = None) -> Dict:
        """
        Search repositories for relevant files without generating a full answer.
        
        Args:
            messages: List of message objects with role and content
            repositories: List of repository objects
            session_id: Optional session ID for continuing a conversation
            genius: Whether to use enhanced search capabilities
            timeout: Custom timeout for this request in seconds
        
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
            
            # Update session cache with the current messages
            if session_id in self._session_cache:
                # Add only new messages to avoid duplication
                existing_messages = {msg.get("id", idx): msg 
                                   for idx, msg in enumerate(self._session_cache[session_id])}
                
                for msg in messages:
                    msg_id = msg.get("id", f"msg-{len(existing_messages)}")
                    if msg_id not in existing_messages:
                        self._session_cache[session_id].append(msg)
            else:
                self._session_cache[session_id] = messages.copy()
        
        response = await self._make_request("POST", url, json_data=payload, timeout=timeout)
        return response.json()
    
    async def get_repository_info(self, repository_id: str, timeout: Optional[float] = None) -> Dict:
        """
        Get information about an indexed repository.
        
        Args:
            repository_id: Repository ID in the format "remote:branch:owner/repository"
            timeout: Custom timeout for this request in seconds
        
        Returns:
            The API response as a dictionary
        """
        # Fully encode the repository_id, this ensures the slashes are properly encoded
        encoded_id = urllib.parse.quote_plus(repository_id, safe='')
        url = f"{self.base_url}/repositories/{encoded_id}"
        
        response = await self._make_request("GET", url, timeout=timeout)
        return response.json()

    async def monitor_repository_processing(self, 
                                        repository_id: str, 
                                        polling_interval: float = 5.0, 
                                        max_attempts: int = 60,
                                        timeout: Optional[float] = None) -> Dict:
        """
        Monitor repository processing until completion or timeout.
        
        Args:
            repository_id: Repository ID in the format "remote:branch:owner/repository"
            polling_interval: Seconds between status checks (default: 5.0)
            max_attempts: Maximum number of status checks before timeout (default: 60)
            timeout: Custom timeout for each request in seconds
            
        Returns:
            Final repository status or timeout notification
        """
        attempts = 0
        start_time = asyncio.get_event_loop().time()
        
        while attempts < max_attempts:
            try:
                status = await self.get_repository_info(repository_id, timeout)
                
                # If processing is complete, return the status
                if status.get("status") in ["COMPLETED", "FAILED", "ERROR"]:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    logger.info(f"Repository processing completed with status '{status.get('status')}' after {elapsed:.1f} seconds")
                    return status
                    
                # Log progress
                files_processed = status.get("filesProcessed", 0)
                num_files = status.get("numFiles", 0)
                if num_files > 0:
                    progress = (files_processed / num_files) * 100
                    logger.info(f"Repository processing: {progress:.1f}% ({files_processed}/{num_files} files)")
                else:
                    logger.info(f"Repository processing: {files_processed} files processed")
                
                # Wait before checking again
                await asyncio.sleep(polling_interval)
                attempts += 1
                
            except Exception as e:
                logger.error(f"Error monitoring repository processing: {str(e)}")
                return {
                    "status": "ERROR",
                    "error": str(e),
                    "repository_id": repository_id
                }
        
        # If we reach here, we've timed out
        total_time = polling_interval * max_attempts
        logger.warning(f"Repository processing monitoring timed out after {total_time} seconds")
        return {
            "status": "TIMEOUT", 
            "message": f"Repository processing did not complete within {total_time} seconds",
            "repository_id": repository_id
        }

    def get_session_messages(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get all messages for a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            List of message objects for the session
        """
        return self._session_cache.get(session_id, [])
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear a session from the cache.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if the session was found and cleared, False otherwise
        """
        if session_id in self._session_cache:
            del self._session_cache[session_id]
            return True
        return False
    
    @staticmethod
    def generate_session_id() -> str:
        """
        Generate a unique session ID.
        
        Returns:
            A unique session ID
        """
        return str(uuid.uuid4())

def get_greptile_client(timeout: Optional[float] = None) -> GreptileClient:
    """
    Create and configure a Greptile API client based on environment variables.
    
    Args:
        timeout: Custom default timeout for API calls in seconds
        
    Returns:
        GreptileClient: Configured Greptile API client
        
    Raises:
        ValueError: If required environment variables are missing
    """
    api_key = os.getenv("GREPTILE_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    base_url = os.getenv("GREPTILE_BASE_URL", "https://api.greptile.com/v2")
    
    if not api_key:
        raise ValueError("GREPTILE_API_KEY environment variable is required")
    
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    
    default_timeout = timeout or float(os.getenv("GREPTILE_TIMEOUT", "60.0"))
    
    return GreptileClient(api_key, github_token, base_url, default_timeout)
