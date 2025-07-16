#!/usr/bin/env python3
"""
Greptile API Discovery and Reverse Engineering Tool

This script discovers and analyzes the Greptile API endpoints, response structures,
and authentication patterns to create a comprehensive API reference.
"""

import os
import json
import asyncio
import httpx
import yaml
import time
import sys
from typing import Dict, List, Any, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EndpointInfo:
    """Information about a discovered API endpoint"""
    path: str
    method: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    request_body: Optional[Dict[str, Any]] = None
    response_schemas: List[Dict[str, Any]] = field(default_factory=list)
    status_codes: Set[int] = field(default_factory=set)
    auth_required: bool = True
    streaming_support: bool = False
    examples: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class APIDiscoveryResult:
    """Complete API discovery results"""
    base_url: str
    endpoints: List[EndpointInfo]
    auth_schemes: Dict[str, str]
    common_errors: Dict[int, str]
    rate_limits: Dict[str, Any]
    discovered_at: datetime
    total_endpoints: int

class GreptileAPIDiscovery:
    """Greptile API discovery and analysis tool"""
    
    def __init__(self, api_key: str, github_token: str, base_url: str = "https://api.greptile.com/v2"):
        self.api_key = api_key
        self.github_token = github_token
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.discovered_endpoints: List[EndpointInfo] = []
        self.auth_schemes = {
            "ApiKeyAuth": f"Bearer {api_key}",
            "GitHubToken": github_token
        }
        
        # Known endpoints from existing code analysis
        self.known_endpoints = [
            "/repositories",
            "/repositories/{repositoryId}",
            "/query",
            "/search",
            "/chats/{sessionId}",
        ]
        
        # Common API patterns to probe
        self.probe_patterns = [
            "/health",
            "/status",
            "/version",
            "/info",
            "/docs",
            "/openapi",
            "/swagger",
            "/api-docs",
            "/repositories/{repositoryId}/status",
            "/repositories/{repositoryId}/files",
            "/repositories/{repositoryId}/branches",
            "/users",
            "/users/me",
            "/sessions",
            "/sessions/{sessionId}",
            "/sessions/{sessionId}/messages",
            "/billing",
            "/usage",
            "/limits",
            "/admin",
            "/webhooks",
        ]

    async def discover_endpoints(self) -> APIDiscoveryResult:
        """Discover all available API endpoints"""
        logger.info("Starting API endpoint discovery...")
        
        # First, analyze known endpoints
        await self._analyze_known_endpoints()
        
        # Then probe for additional endpoints
        await self._probe_additional_endpoints()
        
        # Analyze response structures
        await self._analyze_response_structures()
        
        # Detect rate limiting
        rate_limits = await self._analyze_rate_limits()
        
        # Analyze authentication patterns
        await self._analyze_auth_patterns()
        
        return APIDiscoveryResult(
            base_url=self.base_url,
            endpoints=self.discovered_endpoints,
            auth_schemes=self.auth_schemes,
            common_errors=self._get_common_errors(),
            rate_limits=rate_limits,
            discovered_at=datetime.now(),
            total_endpoints=len(self.discovered_endpoints)
        )

    async def _analyze_known_endpoints(self):
        """Analyze known endpoints from existing code"""
        logger.info("Analyzing known endpoints...")
        
        for endpoint_path in self.known_endpoints:
            logger.info(f"Analyzing endpoint: {endpoint_path}")
            
            if endpoint_path == "/repositories":
                await self._analyze_repositories_endpoint()
            elif endpoint_path.startswith("/repositories/{repositoryId}"):
                await self._analyze_repository_info_endpoint()
            elif endpoint_path == "/query":
                await self._analyze_query_endpoint()
            elif endpoint_path == "/search":
                await self._analyze_search_endpoint()
            elif endpoint_path.startswith("/chats/{sessionId}"):
                await self._analyze_chats_endpoint()

    async def _analyze_repositories_endpoint(self):
        """Analyze the /repositories endpoint"""
        endpoint = EndpointInfo(
            path="/repositories",
            method="POST",
            description="Index a repository for code search and querying",
            auth_required=True,
            headers={"Authorization": f"Bearer {self.api_key}", "X-GitHub-Token": self.github_token}
        )
        
        # Test with a small public repository
        test_payload = {
            "remote": "github",
            "repository": "octocat/Hello-World",
            "branch": "master",
            "reload": False,
            "notify": False
        }
        
        try:
            response = await self._make_request("POST", "/repositories", json=test_payload)
            if response:
                endpoint.status_codes.add(response.status_code)
                endpoint.request_body = test_payload
                endpoint.response_schemas.append(response.json())
                endpoint.examples.append({
                    "request": test_payload,
                    "response": response.json()
                })
        except Exception as e:
            logger.warning(f"Error testing repositories endpoint: {e}")
        
        self.discovered_endpoints.append(endpoint)

    async def _analyze_repository_info_endpoint(self):
        """Analyze the /repositories/{repositoryId} endpoint"""
        endpoint = EndpointInfo(
            path="/repositories/{repositoryId}",
            method="GET",
            description="Get information about a repository",
            auth_required=True,
            parameters={"repositoryId": "Repository ID in format: remote:branch:owner%2Frepo"}
        )
        
        # Test with a known repository format
        repo_id = "github:master:octocat%2FHello-World"
        
        try:
            response = await self._make_request("GET", f"/repositories/{repo_id}")
            if response:
                endpoint.status_codes.add(response.status_code)
                endpoint.response_schemas.append(response.json())
                endpoint.examples.append({
                    "request": {"repositoryId": repo_id},
                    "response": response.json()
                })
        except Exception as e:
            logger.warning(f"Error testing repository info endpoint: {e}")
        
        self.discovered_endpoints.append(endpoint)

    async def _analyze_query_endpoint(self):
        """Analyze the /query endpoint"""
        endpoint = EndpointInfo(
            path="/query",
            method="POST",
            description="Execute natural language queries against indexed repositories",
            auth_required=True,
            streaming_support=True
        )
        
        # Test both streaming and non-streaming
        test_payload = {
            "messages": [{"role": "user", "content": "What is this repository about?"}],
            "repositories": [{"remote": "github", "repository": "octocat/Hello-World", "branch": "master"}],
            "stream": False,
            "genius": False
        }
        
        try:
            # Test non-streaming
            response = await self._make_request("POST", "/query", json=test_payload)
            if response:
                endpoint.status_codes.add(response.status_code)
                endpoint.request_body = test_payload
                endpoint.response_schemas.append(response.json())
                
            # Test streaming
            test_payload["stream"] = True
            stream_response = await self._make_request("POST", "/query", json=test_payload, stream=True)
            if stream_response:
                endpoint.streaming_support = True
                
        except Exception as e:
            logger.warning(f"Error testing query endpoint: {e}")
        
        self.discovered_endpoints.append(endpoint)

    async def _analyze_search_endpoint(self):
        """Analyze the /search endpoint"""
        endpoint = EndpointInfo(
            path="/search",
            method="POST",
            description="Search repositories for relevant files and code",
            auth_required=True
        )
        
        test_payload = {
            "query": "main function",
            "repositories": [{"remote": "github", "repository": "octocat/Hello-World", "branch": "master"}]
        }
        
        try:
            response = await self._make_request("POST", "/search", json=test_payload)
            if response:
                endpoint.status_codes.add(response.status_code)
                endpoint.request_body = test_payload
                endpoint.response_schemas.append(response.json())
                
        except Exception as e:
            logger.warning(f"Error testing search endpoint: {e}")
        
        self.discovered_endpoints.append(endpoint)

    async def _analyze_chats_endpoint(self):
        """Analyze the /chats/{sessionId} endpoint"""
        endpoint = EndpointInfo(
            path="/chats/{sessionId}",
            method="GET",
            description="Retrieve chat history for a session",
            auth_required=True,
            parameters={"sessionId": "Session ID for chat history"}
        )
        
        # Test with a dummy session ID
        session_id = "test-session-123"
        
        try:
            response = await self._make_request("GET", f"/chats/{session_id}")
            if response:
                endpoint.status_codes.add(response.status_code)
                endpoint.response_schemas.append(response.json())
                
        except Exception as e:
            logger.warning(f"Error testing chats endpoint: {e}")
        
        self.discovered_endpoints.append(endpoint)

    async def _probe_additional_endpoints(self):
        """Probe for additional endpoints that might exist"""
        logger.info("Probing for additional endpoints...")
        
        for pattern in self.probe_patterns:
            try:
                # Try GET first
                response = await self._make_request("GET", pattern)
                if response and response.status_code != 404:
                    endpoint = EndpointInfo(
                        path=pattern,
                        method="GET",
                        description=f"Discovered endpoint: {pattern}",
                        auth_required=response.status_code != 401
                    )
                    endpoint.status_codes.add(response.status_code)
                    if response.status_code == 200:
                        try:
                            endpoint.response_schemas.append(response.json())
                        except:
                            pass
                    self.discovered_endpoints.append(endpoint)
                    logger.info(f"Found endpoint: GET {pattern} -> {response.status_code}")
                
                # Try POST for some patterns
                if pattern in ["/repositories", "/query", "/search"]:
                    response = await self._make_request("POST", pattern, json={})
                    if response and response.status_code not in [404, 405]:
                        endpoint = EndpointInfo(
                            path=pattern,
                            method="POST",
                            description=f"Discovered endpoint: {pattern}",
                            auth_required=response.status_code != 401
                        )
                        endpoint.status_codes.add(response.status_code)
                        if response.status_code == 200:
                            try:
                                endpoint.response_schemas.append(response.json())
                            except:
                                pass
                        self.discovered_endpoints.append(endpoint)
                        logger.info(f"Found endpoint: POST {pattern} -> {response.status_code}")
                        
            except Exception as e:
                logger.debug(f"Probing {pattern} failed: {e}")
                continue

    async def _analyze_response_structures(self):
        """Analyze response structures and extract schemas"""
        logger.info("Analyzing response structures...")
        
        for endpoint in self.discovered_endpoints:
            if endpoint.response_schemas:
                # Analyze each response schema
                for schema in endpoint.response_schemas:
                    self._extract_schema_info(schema, endpoint)

    def _extract_schema_info(self, response_data: Dict[str, Any], endpoint: EndpointInfo):
        """Extract schema information from response data"""
        if isinstance(response_data, dict):
            for key, value in response_data.items():
                if key == "sources" and isinstance(value, list):
                    # This is likely a sources array
                    endpoint.description += f" Returns sources with {len(value)} items"
                elif key == "message" and isinstance(value, str):
                    # This is likely a message response
                    endpoint.description += " Returns message response"
                elif key == "statusEndpoint" and isinstance(value, str):
                    # This indicates async processing
                    endpoint.description += " Returns status endpoint for async processing"

    async def _analyze_rate_limits(self) -> Dict[str, Any]:
        """Analyze rate limiting patterns"""
        logger.info("Analyzing rate limits...")
        
        rate_limit_info = {
            "detected": False,
            "headers": {},
            "limits": {}
        }
        
        # Make multiple requests to detect rate limiting
        for i in range(5):
            try:
                response = await self._make_request("GET", "/repositories/github:master:octocat%2FHello-World")
                if response:
                    # Check for rate limit headers
                    for header in response.headers:
                        if any(keyword in header.lower() for keyword in ['rate', 'limit', 'throttle']):
                            rate_limit_info["headers"][header] = response.headers[header]
                            rate_limit_info["detected"] = True
                            
                    if response.status_code == 429:
                        rate_limit_info["detected"] = True
                        rate_limit_info["limits"]["status_429_encountered"] = True
                        
            except Exception as e:
                logger.debug(f"Rate limit test {i} failed: {e}")
                
            await asyncio.sleep(0.1)  # Small delay between requests
        
        return rate_limit_info

    async def _analyze_auth_patterns(self):
        """Analyze authentication patterns"""
        logger.info("Analyzing authentication patterns...")
        
        # Test endpoints without authentication
        for endpoint in self.discovered_endpoints:
            if endpoint.auth_required:
                try:
                    # Test without auth headers
                    response = await self._make_request_no_auth(endpoint.method, endpoint.path)
                    if response:
                        if response.status_code == 401:
                            endpoint.auth_required = True
                        elif response.status_code == 200:
                            endpoint.auth_required = False
                except Exception as e:
                    logger.debug(f"Auth test for {endpoint.path} failed: {e}")

    async def _make_request(self, method: str, path: str, **kwargs) -> Optional[httpx.Response]:
        """Make an authenticated HTTP request"""
        url = urljoin(self.base_url, path)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-GitHub-Token": self.github_token,
            "Content-Type": "application/json"
        }
        
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            del kwargs["headers"]
        
        try:
            response = await self.client.request(method, url, headers=headers, **kwargs)
            return response
        except Exception as e:
            logger.debug(f"Request to {method} {path} failed: {e}")
            return None

    async def _make_request_no_auth(self, method: str, path: str, **kwargs) -> Optional[httpx.Response]:
        """Make an unauthenticated HTTP request"""
        url = urljoin(self.base_url, path)
        headers = {"Content-Type": "application/json"}
        
        try:
            response = await self.client.request(method, url, headers=headers, **kwargs)
            return response
        except Exception as e:
            logger.debug(f"Unauth request to {method} {path} failed: {e}")
            return None

    def _get_common_errors(self) -> Dict[int, str]:
        """Get common error codes and their meanings"""
        return {
            400: "Bad Request - Invalid request format or parameters",
            401: "Unauthorized - Invalid or missing authentication",
            403: "Forbidden - Access denied",
            404: "Not Found - Endpoint or resource not found",
            429: "Too Many Requests - Rate limit exceeded",
            500: "Internal Server Error - Server error",
            502: "Bad Gateway - Gateway error",
            503: "Service Unavailable - Service temporarily unavailable"
        }

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    def generate_openapi_spec(self, discovery_result: APIDiscoveryResult) -> Dict[str, Any]:
        """Generate OpenAPI specification from discovery results"""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Greptile API",
                "version": "2.0",
                "description": "Discovered API endpoints for Greptile code search service"
            },
            "servers": [{"url": discovery_result.base_url}],
            "components": {
                "securitySchemes": {
                    "ApiKeyAuth": {
                        "type": "http",
                        "scheme": "bearer"
                    },
                    "GitHubToken": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-GitHub-Token"
                    }
                }
            },
            "paths": {}
        }
        
        for endpoint in discovery_result.endpoints:
            path = endpoint.path
            if path not in spec["paths"]:
                spec["paths"][path] = {}
            
            method = endpoint.method.lower()
            spec["paths"][path][method] = {
                "summary": endpoint.description,
                "responses": {
                    str(code): {"description": f"Status code {code}"}
                    for code in endpoint.status_codes
                }
            }
            
            if endpoint.auth_required:
                spec["paths"][path][method]["security"] = [
                    {"ApiKeyAuth": [], "GitHubToken": []}
                ]
            
            if endpoint.request_body:
                spec["paths"][path][method]["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }
        
        return spec

    def save_results(self, discovery_result: APIDiscoveryResult, output_dir: str = "api_discovery"):
        """Save discovery results to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON report
        json_report = {
            "discovered_at": discovery_result.discovered_at.isoformat(),
            "base_url": discovery_result.base_url,
            "total_endpoints": discovery_result.total_endpoints,
            "endpoints": [
                {
                    "path": ep.path,
                    "method": ep.method,
                    "description": ep.description,
                    "auth_required": ep.auth_required,
                    "status_codes": list(ep.status_codes),
                    "streaming_support": ep.streaming_support,
                    "parameters": ep.parameters,
                    "examples": ep.examples
                }
                for ep in discovery_result.endpoints
            ],
            "auth_schemes": discovery_result.auth_schemes,
            "rate_limits": discovery_result.rate_limits,
            "common_errors": discovery_result.common_errors
        }
        
        with open(f"{output_dir}/discovery_report.json", "w") as f:
            json.dump(json_report, f, indent=2, default=str)
        
        # Save OpenAPI spec
        openapi_spec = self.generate_openapi_spec(discovery_result)
        with open(f"{output_dir}/openapi_spec.yaml", "w") as f:
            yaml.dump(openapi_spec, f, default_flow_style=False)
        
        # Save markdown report
        markdown_report = self._generate_markdown_report(discovery_result)
        with open(f"{output_dir}/api_reference.md", "w") as f:
            f.write(markdown_report)
        
        logger.info(f"Results saved to {output_dir}/")

    def _generate_markdown_report(self, discovery_result: APIDiscoveryResult) -> str:
        """Generate a markdown report of the discovery results"""
        report = [
            "# Greptile API Discovery Report",
            f"",
            f"**Base URL:** {discovery_result.base_url}",
            f"**Discovery Date:** {discovery_result.discovered_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Endpoints:** {discovery_result.total_endpoints}",
            f"",
            "## Endpoints",
            ""
        ]
        
        for endpoint in discovery_result.endpoints:
            report.extend([
                f"### {endpoint.method} {endpoint.path}",
                f"",
                f"**Description:** {endpoint.description}",
                f"**Authentication Required:** {'Yes' if endpoint.auth_required else 'No'}",
                f"**Streaming Support:** {'Yes' if endpoint.streaming_support else 'No'}",
                f"**Status Codes:** {', '.join(map(str, sorted(endpoint.status_codes)))}",
                f""
            ])
            
            if endpoint.parameters:
                report.extend([
                    "**Parameters:**",
                    ""
                ])
                for param, desc in endpoint.parameters.items():
                    report.append(f"- `{param}`: {desc}")
                report.append("")
            
            if endpoint.examples:
                report.extend([
                    "**Examples:**",
                    ""
                ])
                for i, example in enumerate(endpoint.examples):
                    report.extend([
                        f"Example {i+1}:",
                        "```json",
                        json.dumps(example, indent=2),
                        "```",
                        ""
                    ])
        
        if discovery_result.rate_limits.get("detected"):
            report.extend([
                "## Rate Limiting",
                "",
                "Rate limiting has been detected on this API.",
                ""
            ])
            
            if discovery_result.rate_limits.get("headers"):
                report.extend([
                    "**Rate Limit Headers:**",
                    ""
                ])
                for header, value in discovery_result.rate_limits["headers"].items():
                    report.append(f"- `{header}`: {value}")
                report.append("")
        
        report.extend([
            "## Common Error Codes",
            ""
        ])
        
        for code, desc in discovery_result.common_errors.items():
            report.append(f"- **{code}**: {desc}")
        
        return "\n".join(report)

async def main():
    """Main function to run the API discovery"""
    api_key = os.getenv("GREPTILE_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    base_url = os.getenv("GREPTILE_BASE_URL", "https://api.greptile.com/v2")
    
    if not api_key:
        logger.error("GREPTILE_API_KEY environment variable is required")
        sys.exit(1)
    
    if not github_token:
        logger.error("GITHUB_TOKEN environment variable is required")
        sys.exit(1)
    
    discovery = GreptileAPIDiscovery(api_key, github_token, base_url)
    
    try:
        logger.info("Starting Greptile API discovery...")
        start_time = time.time()
        
        result = await discovery.discover_endpoints()
        
        end_time = time.time()
        logger.info(f"Discovery completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Found {result.total_endpoints} endpoints")
        
        # Save results
        discovery.save_results(result)
        
        # Print summary
        print("\n" + "="*50)
        print("GREPTILE API DISCOVERY SUMMARY")
        print("="*50)
        print(f"Base URL: {result.base_url}")
        print(f"Total Endpoints: {result.total_endpoints}")
        print(f"Rate Limiting: {'Detected' if result.rate_limits.get('detected') else 'Not detected'}")
        print("\nEndpoints found:")
        for endpoint in result.endpoints:
            auth_str = "🔒" if endpoint.auth_required else "🔓"
            stream_str = "📡" if endpoint.streaming_support else ""
            print(f"  {auth_str} {endpoint.method} {endpoint.path} {stream_str}")
        
        print(f"\nResults saved to api_discovery/")
        
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        sys.exit(1)
    
    finally:
        await discovery.close()

if __name__ == "__main__":
    asyncio.run(main())