#!/usr/bin/env python3
"""
Greptile API Response Structure Analyzer

This script performs deep analysis of Greptile API response structures,
authentication patterns, and error handling to better understand the API behavior.
"""

import os
import json
import asyncio
import httpx
import time
import uuid
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ResponseAnalysis:
    """Analysis results for a single API response"""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    headers: Dict[str, str]
    body_type: str  # 'json', 'text', 'stream', 'binary'
    schema: Optional[Dict[str, Any]] = None
    streaming_chunks: List[Dict[str, Any]] = field(default_factory=list)
    error_details: Optional[Dict[str, Any]] = None
    citations: List[Dict[str, Any]] = field(default_factory=list)
    session_info: Optional[Dict[str, Any]] = None

@dataclass
class AuthenticationAnalysis:
    """Authentication pattern analysis"""
    endpoint: str
    requires_api_key: bool
    requires_github_token: bool
    auth_header_format: str
    error_without_auth: Dict[str, Any]
    error_with_invalid_auth: Dict[str, Any]
    token_validation_patterns: List[str] = field(default_factory=list)

class GreptileResponseAnalyzer:
    """Advanced response structure and authentication analyzer"""
    
    def __init__(self, api_key: str, github_token: str, base_url: str = "https://api.greptile.com/v2"):
        self.api_key = api_key
        self.github_token = github_token
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.analyses: List[ResponseAnalysis] = []
        self.auth_analyses: List[AuthenticationAnalysis] = []
        
        # Test repository for safe testing
        self.test_repo = {
            "remote": "github",
            "repository": "octocat/Hello-World",
            "branch": "master"
        }

    async def analyze_all_endpoints(self) -> Dict[str, Any]:
        """Analyze all known endpoints comprehensively"""
        logger.info("Starting comprehensive response analysis...")
        
        # Test different scenarios for each endpoint
        await self._analyze_repositories_endpoint()
        await self._analyze_repository_info_endpoint()
        await self._analyze_query_endpoint()
        await self._analyze_search_endpoint()
        await self._analyze_chats_endpoint()
        
        # Analyze streaming patterns
        await self._analyze_streaming_patterns()
        
        # Analyze authentication patterns
        await self._analyze_authentication_patterns()
        
        # Analyze error patterns
        await self._analyze_error_patterns()
        
        return {
            "response_analyses": [self._analysis_to_dict(analysis) for analysis in self.analyses],
            "auth_analyses": [self._auth_analysis_to_dict(auth) for auth in self.auth_analyses],
            "summary": self._generate_summary()
        }

    async def _analyze_repositories_endpoint(self):
        """Deep analysis of /repositories endpoint"""
        logger.info("Analyzing /repositories endpoint...")
        
        endpoint = "/repositories"
        
        # Test successful indexing
        test_payload = {
            "remote": "github",
            "repository": "octocat/Hello-World",
            "branch": "master",
            "reload": False,
            "notify": False
        }
        
        analysis = await self._make_analyzed_request("POST", endpoint, json=test_payload)
        if analysis:
            self.analyses.append(analysis)
            
            # Test with different parameters
            variations = [
                {"reload": True, "notify": True},
                {"remote": "gitlab", "repository": "test/repo", "branch": "main"},
                {"repository": "invalid/repo", "branch": "nonexistent"}
            ]
            
            for variation in variations:
                test_payload.update(variation)
                variant_analysis = await self._make_analyzed_request("POST", endpoint, json=test_payload)
                if variant_analysis:
                    self.analyses.append(variant_analysis)

    async def _analyze_repository_info_endpoint(self):
        """Deep analysis of /repositories/{repositoryId} endpoint"""
        logger.info("Analyzing /repositories/{repositoryId} endpoint...")
        
        # Test different repository ID formats
        repo_ids = [
            "github:master:octocat%2FHello-World",
            "github:main:octocat%2FHello-World",
            "invalid:format:test",
            "github:master:nonexistent%2Frepo"
        ]
        
        for repo_id in repo_ids:
            endpoint = f"/repositories/{repo_id}"
            analysis = await self._make_analyzed_request("GET", endpoint)
            if analysis:
                self.analyses.append(analysis)

    async def _analyze_query_endpoint(self):
        """Deep analysis of /query endpoint"""
        logger.info("Analyzing /query endpoint...")
        
        endpoint = "/query"
        
        # Test different query types
        test_queries = [
            {
                "messages": [{"role": "user", "content": "What is this repository about?"}],
                "repositories": [self.test_repo],
                "stream": False,
                "genius": False
            },
            {
                "messages": [{"role": "user", "content": "Show me the main function"}],
                "repositories": [self.test_repo],
                "stream": False,
                "genius": True
            },
            {
                "messages": [
                    {"role": "user", "content": "What does this do?"},
                    {"role": "assistant", "content": "This is a test repository."},
                    {"role": "user", "content": "Show me more details"}
                ],
                "repositories": [self.test_repo],
                "stream": False,
                "genius": False,
                "sessionId": str(uuid.uuid4())
            }
        ]
        
        for query in test_queries:
            analysis = await self._make_analyzed_request("POST", endpoint, json=query)
            if analysis:
                self.analyses.append(analysis)

    async def _analyze_search_endpoint(self):
        """Deep analysis of /search endpoint"""
        logger.info("Analyzing /search endpoint...")
        
        endpoint = "/search"
        
        # Test different search queries
        search_queries = [
            "main function",
            "import statements",
            "class definition",
            "nonexistent code pattern"
        ]
        
        for query in search_queries:
            test_payload = {
                "query": query,
                "repositories": [self.test_repo],
                "sessionId": str(uuid.uuid4())
            }
            
            analysis = await self._make_analyzed_request("POST", endpoint, json=test_payload)
            if analysis:
                self.analyses.append(analysis)

    async def _analyze_chats_endpoint(self):
        """Deep analysis of /chats/{sessionId} endpoint"""
        logger.info("Analyzing /chats/{sessionId} endpoint...")
        
        # Test with different session IDs
        session_ids = [
            str(uuid.uuid4()),
            "test-session-123",
            "invalid-session",
            "nonexistent-session"
        ]
        
        for session_id in session_ids:
            endpoint = f"/chats/{session_id}"
            analysis = await self._make_analyzed_request("GET", endpoint)
            if analysis:
                self.analyses.append(analysis)

    async def _analyze_streaming_patterns(self):
        """Analyze streaming response patterns"""
        logger.info("Analyzing streaming patterns...")
        
        endpoint = "/query"
        test_payload = {
            "messages": [{"role": "user", "content": "Explain this repository in detail"}],
            "repositories": [self.test_repo],
            "stream": True,
            "genius": False
        }
        
        analysis = await self._make_streaming_request("POST", endpoint, json=test_payload)
        if analysis:
            self.analyses.append(analysis)

    async def _analyze_authentication_patterns(self):
        """Analyze authentication requirements and patterns"""
        logger.info("Analyzing authentication patterns...")
        
        endpoints_to_test = [
            ("POST", "/repositories"),
            ("GET", "/repositories/github:master:octocat%2FHello-World"),
            ("POST", "/query"),
            ("POST", "/search"),
            ("GET", "/chats/test-session")
        ]
        
        for method, endpoint in endpoints_to_test:
            auth_analysis = await self._analyze_endpoint_auth(method, endpoint)
            if auth_analysis:
                self.auth_analyses.append(auth_analysis)

    async def _analyze_error_patterns(self):
        """Analyze error response patterns"""
        logger.info("Analyzing error patterns...")
        
        # Test various error scenarios
        error_tests = [
            ("POST", "/repositories", {"invalid": "payload"}),
            ("GET", "/repositories/invalid-format"),
            ("POST", "/query", {"messages": []}),
            ("POST", "/search", {"query": ""}),
            ("GET", "/nonexistent-endpoint")
        ]
        
        for method, endpoint, payload in error_tests:
            if payload:
                analysis = await self._make_analyzed_request(method, endpoint, json=payload)
            else:
                analysis = await self._make_analyzed_request(method, endpoint)
            
            if analysis and analysis.status_code >= 400:
                self.analyses.append(analysis)

    async def _make_analyzed_request(self, method: str, endpoint: str, **kwargs) -> Optional[ResponseAnalysis]:
        """Make a request and analyze the response"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-GitHub-Token": self.github_token,
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.request(method, url, headers=headers, **kwargs)
            response_time = time.time() - start_time
            
            # Determine body type and parse content
            body_type = "text"
            schema = None
            error_details = None
            
            try:
                content = response.json()
                body_type = "json"
                schema = self._extract_schema(content)
                
                if response.status_code >= 400:
                    error_details = content
                    
            except json.JSONDecodeError:
                content = response.text
                body_type = "text"
            
            # Extract citations if present
            citations = []
            if isinstance(content, dict) and "sources" in content:
                citations = content.get("sources", [])
            
            # Extract session info if present
            session_info = None
            if isinstance(content, dict) and "sessionId" in content:
                session_info = {"sessionId": content["sessionId"]}
            
            return ResponseAnalysis(
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                response_time=response_time,
                headers=dict(response.headers),
                body_type=body_type,
                schema=schema,
                error_details=error_details,
                citations=citations,
                session_info=session_info
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {method} {endpoint}: {e}")
            return None

    async def _make_streaming_request(self, method: str, endpoint: str, **kwargs) -> Optional[ResponseAnalysis]:
        """Make a streaming request and analyze the response"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-GitHub-Token": self.github_token,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        start_time = time.time()
        streaming_chunks = []
        
        try:
            async with self.client.stream(method, url, headers=headers, **kwargs) as response:
                response_time = time.time() - start_time
                
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        # Parse SSE format
                        lines = chunk.strip().split('\n')
                        for line in lines:
                            if line.startswith('data: '):
                                try:
                                    data = json.loads(line[6:])  # Remove 'data: ' prefix
                                    streaming_chunks.append(data)
                                except json.JSONDecodeError:
                                    streaming_chunks.append({"raw": line[6:]})
                
                return ResponseAnalysis(
                    endpoint=endpoint,
                    method=method,
                    status_code=response.status_code,
                    response_time=response_time,
                    headers=dict(response.headers),
                    body_type="stream",
                    streaming_chunks=streaming_chunks
                )
                
        except Exception as e:
            logger.error(f"Error analyzing streaming {method} {endpoint}: {e}")
            return None

    async def _analyze_endpoint_auth(self, method: str, endpoint: str) -> Optional[AuthenticationAnalysis]:
        """Analyze authentication requirements for an endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        # Test without authentication
        no_auth_response = None
        try:
            no_auth_response = await self.client.request(method, url, headers={"Content-Type": "application/json"})
        except Exception as e:
            logger.debug(f"No auth test failed for {method} {endpoint}: {e}")
        
        # Test with invalid authentication
        invalid_auth_response = None
        try:
            invalid_headers = {
                "Authorization": "Bearer invalid-token",
                "X-GitHub-Token": "invalid-github-token",
                "Content-Type": "application/json"
            }
            invalid_auth_response = await self.client.request(method, url, headers=invalid_headers)
        except Exception as e:
            logger.debug(f"Invalid auth test failed for {method} {endpoint}: {e}")
        
        # Test with only API key
        api_key_only_response = None
        try:
            api_key_headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            api_key_only_response = await self.client.request(method, url, headers=api_key_headers)
        except Exception as e:
            logger.debug(f"API key only test failed for {method} {endpoint}: {e}")
        
        # Test with only GitHub token
        github_only_response = None
        try:
            github_headers = {
                "X-GitHub-Token": self.github_token,
                "Content-Type": "application/json"
            }
            github_only_response = await self.client.request(method, url, headers=github_headers)
        except Exception as e:
            logger.debug(f"GitHub token only test failed for {method} {endpoint}: {e}")
        
        # Analyze results
        requires_api_key = True
        requires_github_token = True
        
        if api_key_only_response and api_key_only_response.status_code < 400:
            requires_github_token = False
        
        if github_only_response and github_only_response.status_code < 400:
            requires_api_key = False
        
        return AuthenticationAnalysis(
            endpoint=endpoint,
            requires_api_key=requires_api_key,
            requires_github_token=requires_github_token,
            auth_header_format="Bearer token + X-GitHub-Token",
            error_without_auth=self._response_to_dict(no_auth_response),
            error_with_invalid_auth=self._response_to_dict(invalid_auth_response)
        )

    def _extract_schema(self, data: Any, path: str = "") -> Dict[str, Any]:
        """Extract schema information from response data"""
        if isinstance(data, dict):
            schema = {"type": "object", "properties": {}}
            for key, value in data.items():
                schema["properties"][key] = self._extract_schema(value, f"{path}.{key}")
            return schema
        elif isinstance(data, list):
            if data:
                return {"type": "array", "items": self._extract_schema(data[0], f"{path}[0]")}
            else:
                return {"type": "array", "items": {"type": "unknown"}}
        elif isinstance(data, str):
            return {"type": "string", "example": data[:100]}
        elif isinstance(data, int):
            return {"type": "integer", "example": data}
        elif isinstance(data, float):
            return {"type": "number", "example": data}
        elif isinstance(data, bool):
            return {"type": "boolean", "example": data}
        elif data is None:
            return {"type": "null"}
        else:
            return {"type": "unknown"}

    def _response_to_dict(self, response: Optional[httpx.Response]) -> Dict[str, Any]:
        """Convert response to dictionary for analysis"""
        if not response:
            return {"error": "No response"}
        
        try:
            content = response.json()
        except:
            content = response.text
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": content
        }

    def _analysis_to_dict(self, analysis: ResponseAnalysis) -> Dict[str, Any]:
        """Convert analysis to dictionary"""
        return {
            "endpoint": analysis.endpoint,
            "method": analysis.method,
            "status_code": analysis.status_code,
            "response_time": analysis.response_time,
            "headers": analysis.headers,
            "body_type": analysis.body_type,
            "schema": analysis.schema,
            "streaming_chunks": analysis.streaming_chunks,
            "error_details": analysis.error_details,
            "citations": analysis.citations,
            "session_info": analysis.session_info
        }

    def _auth_analysis_to_dict(self, auth: AuthenticationAnalysis) -> Dict[str, Any]:
        """Convert auth analysis to dictionary"""
        return {
            "endpoint": auth.endpoint,
            "requires_api_key": auth.requires_api_key,
            "requires_github_token": auth.requires_github_token,
            "auth_header_format": auth.auth_header_format,
            "error_without_auth": auth.error_without_auth,
            "error_with_invalid_auth": auth.error_with_invalid_auth,
            "token_validation_patterns": auth.token_validation_patterns
        }

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate analysis summary"""
        return {
            "total_requests": len(self.analyses),
            "successful_requests": len([a for a in self.analyses if a.status_code < 400]),
            "error_requests": len([a for a in self.analyses if a.status_code >= 400]),
            "streaming_endpoints": len([a for a in self.analyses if a.body_type == "stream"]),
            "average_response_time": sum(a.response_time for a in self.analyses) / len(self.analyses) if self.analyses else 0,
            "endpoints_with_citations": len([a for a in self.analyses if a.citations]),
            "endpoints_with_sessions": len([a for a in self.analyses if a.session_info]),
            "auth_required_endpoints": len([a for a in self.auth_analyses if a.requires_api_key or a.requires_github_token])
        }

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    def save_results(self, results: Dict[str, Any], output_file: str = "response_analysis.json"):
        """Save analysis results to file"""
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Analysis results saved to {output_file}")

async def main():
    """Main function"""
    api_key = os.getenv("GREPTILE_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    base_url = os.getenv("GREPTILE_BASE_URL", "https://api.greptile.com/v2")
    
    if not api_key or not github_token:
        logger.error("GREPTILE_API_KEY and GITHUB_TOKEN environment variables are required")
        return
    
    analyzer = GreptileResponseAnalyzer(api_key, github_token, base_url)
    
    try:
        results = await analyzer.analyze_all_endpoints()
        
        # Save results
        analyzer.save_results(results)
        
        # Print summary
        summary = results["summary"]
        print("\n" + "="*50)
        print("GREPTILE API RESPONSE ANALYSIS SUMMARY")
        print("="*50)
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Successful: {summary['successful_requests']}")
        print(f"Errors: {summary['error_requests']}")
        print(f"Streaming Endpoints: {summary['streaming_endpoints']}")
        print(f"Average Response Time: {summary['average_response_time']:.3f}s")
        print(f"Endpoints with Citations: {summary['endpoints_with_citations']}")
        print(f"Endpoints with Sessions: {summary['endpoints_with_sessions']}")
        print(f"Auth Required Endpoints: {summary['auth_required_endpoints']}")
        
    finally:
        await analyzer.close()

if __name__ == "__main__":
    asyncio.run(main())