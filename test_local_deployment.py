#!/usr/bin/env python3
"""
Local Deployment Compatibility Test

This script tests that the original local/Docker deployment still works unchanged
after the addition of the Cloudflare Workers implementation.
"""

import asyncio
import subprocess
import time
import os
import signal
import requests
import json
import logging
from pathlib import Path
import pytest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalServerTester:
    """Test the local MCP server deployment."""
    
    def __init__(self):
        self.server_process = None
        self.base_url = None
        
    async def start_server(self, transport="sse", port=8050):
        """Start the local MCP server."""
        # Set environment variables for testing
        env = os.environ.copy()
        env.update({
            "GREPTILE_API_KEY": "test_api_key_local",
            "GITHUB_TOKEN": "ghp_test_token_local", 
            "GREPTILE_BASE_URL": "https://api.greptile.test/v2",
            "TRANSPORT": transport,
            "PORT": str(port),
            "HOST": "127.0.0.1"
        })
        
        # Start the server process
        cmd = ["python", "-m", "src.main"]
        logger.info(f"Starting server with command: {' '.join(cmd)}")
        
        self.server_process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent
        )
        
        self.base_url = f"http://127.0.0.1:{port}"
        
        # Wait for server to start
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get(f"{self.base_url}/health", timeout=1)
                if response.status_code == 200:
                    logger.info("Server started successfully")
                    return True
            except:
                pass
            
            if self.server_process.poll() is not None:
                # Process has terminated
                stdout, stderr = self.server_process.communicate()
                logger.error(f"Server process terminated unexpectedly")
                logger.error(f"STDOUT: {stdout.decode()}")
                logger.error(f"STDERR: {stderr.decode()}")
                return False
                
            await asyncio.sleep(1)
        
        logger.error("Server failed to start within timeout")
        return False
    
    def stop_server(self):
        """Stop the local server."""
        if self.server_process:
            logger.info("Stopping server...")
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("Server did not terminate gracefully, killing...")
                self.server_process.kill()
                self.server_process.wait()
            except Exception as e:
                logger.error(f"Error stopping server: {e}")
            finally:
                self.server_process = None
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            assert response.status_code == 200, f"Health check failed: {response.status_code}"
            
            data = response.json()
            assert "status" in data, "Health response missing status field"
            assert data["status"] == "healthy", f"Health status not healthy: {data['status']}"
            
            logger.info("✅ Health endpoint test passed")
            return True
        except Exception as e:
            logger.error(f"❌ Health endpoint test failed: {e}")
            return False
    
    def test_server_info(self):
        """Test server information endpoint."""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            assert response.status_code == 200, f"Server info failed: {response.status_code}"
            
            data = response.json()
            expected_fields = ["name", "description", "transport", "tools"]
            for field in expected_fields:
                assert field in data, f"Server info missing {field} field"
            
            # Verify all 4 tools are present
            expected_tools = ["index_repository", "query_repository", "search_repository", "get_repository_info"]
            for tool in expected_tools:
                assert tool in data["tools"], f"Missing tool: {tool}"
            
            logger.info("✅ Server info test passed")
            return True
        except Exception as e:
            logger.error(f"❌ Server info test failed: {e}")
            return False
    
    def test_mcp_tool_endpoints(self):
        """Test MCP tool endpoints with mock requests."""
        test_cases = [
            {
                "tool": "index_repository",
                "params": {
                    "remote": "github",
                    "repository": "test/repo",
                    "branch": "main",
                    "reload": False,
                    "notify": False
                }
            },
            {
                "tool": "get_repository_info", 
                "params": {
                    "remote": "github",
                    "repository": "test/repo",
                    "branch": "main"
                }
            },
            {
                "tool": "search_repository",
                "params": {
                    "query": "test search query",
                    "repositories": [{"remote": "github", "repository": "test/repo", "branch": "main"}],
                    "genius": False
                }
            },
            {
                "tool": "query_repository",
                "params": {
                    "query": "test query",
                    "repositories": [{"remote": "github", "repository": "test/repo", "branch": "main"}],
                    "stream": False,
                    "genius": False
                }
            }
        ]
        
        passed_tests = 0
        for test_case in test_cases:
            try:
                # Create MCP-style request
                mcp_request = {
                    "method": test_case["tool"],
                    "params": test_case["params"]
                }
                
                response = requests.post(
                    f"{self.base_url}/mcp",
                    json=mcp_request,
                    timeout=10,
                    headers={"Content-Type": "application/json"}
                )
                
                # We expect these to fail due to invalid API keys, but the server should handle them gracefully
                assert response.status_code in [200, 400, 500], f"Unexpected status code for {test_case['tool']}: {response.status_code}"
                
                # Try to parse response as JSON
                try:
                    data = response.json()
                    # Should have some kind of structured response
                    assert isinstance(data, dict), f"Response should be a dictionary for {test_case['tool']}"
                except json.JSONDecodeError:
                    # If not JSON, should at least be a string (error message)
                    assert isinstance(response.text, str), f"Response should be JSON or string for {test_case['tool']}"
                
                logger.info(f"✅ Tool endpoint test passed: {test_case['tool']}")
                passed_tests += 1
                
            except Exception as e:
                logger.error(f"❌ Tool endpoint test failed for {test_case['tool']}: {e}")
        
        return passed_tests == len(test_cases)

class TestLocalDeployment:
    """Test suite for local deployment compatibility."""
    
    @pytest.mark.asyncio
    async def test_sse_transport(self):
        """Test SSE transport still works."""
        tester = LocalServerTester()
        
        try:
            # Start server with SSE transport
            success = await tester.start_server(transport="sse", port=8051)
            assert success, "Failed to start server with SSE transport"
            
            # Run basic tests
            assert tester.test_health_endpoint(), "Health endpoint test failed"
            assert tester.test_server_info(), "Server info test failed"
            assert tester.test_mcp_tool_endpoints(), "MCP tool endpoints test failed"
            
        finally:
            tester.stop_server()
    
    @pytest.mark.asyncio 
    async def test_stdio_transport(self):
        """Test stdio transport still works."""
        tester = LocalServerTester()
        
        try:
            # Start server with stdio transport
            success = await tester.start_server(transport="stdio", port=8052)
            assert success, "Failed to start server with stdio transport"
            
            # Run basic tests
            assert tester.test_health_endpoint(), "Health endpoint test failed"
            assert tester.test_server_info(), "Server info test failed"
            assert tester.test_mcp_tool_endpoints(), "MCP tool endpoints test failed"
            
        finally:
            tester.stop_server()
    
    def test_docker_compatibility(self):
        """Test that Docker setup still works."""
        # Check if Dockerfile exists and is valid
        dockerfile_path = Path(__file__).parent / "Dockerfile"
        assert dockerfile_path.exists(), "Dockerfile missing"
        
        # Check if requirements.txt includes all necessary dependencies
        requirements_path = Path(__file__).parent / "requirements.txt"
        assert requirements_path.exists(), "requirements.txt missing"
        
        requirements_content = requirements_path.read_text()
        required_packages = ["mcp", "httpx", "python-dotenv"]
        
        for package in required_packages:
            assert package in requirements_content, f"Missing required package: {package}"
        
        logger.info("✅ Docker compatibility check passed")
    
    def test_start_script_compatibility(self):
        """Test that start-server.sh script still works."""
        script_path = Path(__file__).parent / "start-server.sh"
        assert script_path.exists(), "start-server.sh script missing"
        
        # Check if script is executable
        assert os.access(script_path, os.X_OK), "start-server.sh is not executable"
        
        # Check script content for critical components
        script_content = script_path.read_text()
        critical_elements = [
            "python -m src.main",  # Main command
            "TRANSPORT",           # Transport configuration
            "PORT"                 # Port configuration
        ]
        
        for element in critical_elements:
            assert element in script_content, f"Missing critical element in start script: {element}"
        
        logger.info("✅ Start script compatibility check passed")

async def main():
    """Run comprehensive local deployment tests."""
    logger.info("🚀 Starting Local Deployment Compatibility Tests")
    
    try:
        # Run pytest tests
        import subprocess
        result = subprocess.run([
            "python", "-m", "pytest", 
            __file__, 
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ All local deployment tests passed!")
            print("=" * 60)
            print("LOCAL DEPLOYMENT COMPATIBILITY: ✅ PASSED")
            print("=" * 60)
            print(result.stdout)
        else:
            logger.error("❌ Some local deployment tests failed!")
            print("=" * 60)
            print("LOCAL DEPLOYMENT COMPATIBILITY: ❌ FAILED")
            print("=" * 60)
            print(result.stdout)
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"❌ Error running local deployment tests: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())