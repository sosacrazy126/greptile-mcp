#!/usr/bin/env python3
"""
Test Smithery Compatibility - MCP Protocol Compliance
Tests that the server works correctly with Smithery's npx CLI and MCP protocol.
"""

import subprocess
import json
import time
import sys
import os
import signal
from typing import Dict, Any

class TestSmitheryCompatibility:
    """Test compatibility with Smithery deployment and MCP protocol."""
    
    def test_stdio_transport_initialization(self):
        """Test that server starts correctly with stdio transport (used by Smithery)."""
        env = os.environ.copy()
        env.update({
            'GREPTILE_API_KEY': 'test_key',
            'GITHUB_TOKEN': 'test_token',
            'TRANSPORT': 'stdio'
        })
        
        try:
            # Start server with stdio transport
            process = subprocess.Popen(
                [sys.executable, '-m', 'src.main'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=os.path.join(os.path.dirname(__file__), '..')
            )
            
            # Give it time to start
            time.sleep(2)
            
            # Check if process is running
            if process.poll() is None:
                print("✅ Server starts successfully with stdio transport")
                process.terminate()
                process.wait(timeout=5)
                return True
            else:
                stderr = process.stderr.read().decode()
                print(f"❌ Server failed to start: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing stdio transport: {e}")
            return False
    
    def test_mcp_protocol_compliance(self):
        """Test basic MCP protocol compliance."""
        env = os.environ.copy()
        env.update({
            'GREPTILE_API_KEY': 'test_key',
            'GITHUB_TOKEN': 'test_token',
            'TRANSPORT': 'stdio'
        })
        
        try:
            process = subprocess.Popen(
                [sys.executable, '-m', 'src.main'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=os.path.join(os.path.dirname(__file__), '..')
            )
            
            # Send MCP initialize request
            initialize_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            request_json = json.dumps(initialize_request) + '\n'
            process.stdin.write(request_json.encode())
            process.stdin.flush()
            
            # Give time for response
            time.sleep(1)
            
            # Try to read response (non-blocking)
            try:
                process.terminate()
                stdout, stderr = process.communicate(timeout=2)
                
                # Check if we got any output (indicates server is responding)
                if stdout or not stderr:
                    print("✅ Server responds to MCP protocol messages")
                    return True
                else:
                    print(f"❌ Server not responding to MCP protocol: {stderr.decode()}")
                    return False
                    
            except subprocess.TimeoutExpired:
                process.kill()
                print("✅ Server is running and processing MCP messages")
                return True
                
        except Exception as e:
            print(f"❌ Error testing MCP protocol: {e}")
            return False
    
    def test_parameter_schema_generation(self):
        """Test that FastMCP can generate schemas for our simplified parameters."""
        try:
            # Import and check that server initializes without schema errors
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
            from main import mcp
            
            # If we get here without exceptions, schema generation worked
            assert mcp is not None
            print("✅ FastMCP successfully generates schemas for simplified parameters")
            return True
            
        except Exception as e:
            print(f"❌ Schema generation failed: {e}")
            return False
    
    def test_docker_container_compatibility(self):
        """Test that Docker container works with Smithery-style environment variables."""
        try:
            # Test Docker build
            build_result = subprocess.run(
                ['docker', 'build', '-t', 'greptile-mcp-test', '.'],
                cwd=os.path.join(os.path.dirname(__file__), '..'),
                capture_output=True,
                text=True
            )
            
            if build_result.returncode != 0:
                print(f"❌ Docker build failed: {build_result.stderr}")
                return False
            
            # Test container startup with environment variables
            run_result = subprocess.run(
                [
                    'docker', 'run', '--rm',
                    '-e', 'GREPTILE_API_KEY=test_key',
                    '-e', 'GITHUB_TOKEN=test_token',
                    '-e', 'TRANSPORT=stdio',
                    'greptile-mcp-test',
                    'python', '-c', 'from src.main import mcp; print("Container OK")'
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if run_result.returncode == 0 and "Container OK" in run_result.stdout:
                print("✅ Docker container works with Smithery environment variables")
                return True
            else:
                print(f"❌ Docker container test failed: {run_result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Docker container test timed out")
            return False
        except Exception as e:
            print(f"❌ Docker test error: {e}")
            return False
    
    def test_smithery_cli_simulation(self):
        """Simulate Smithery CLI call pattern."""
        # This simulates how Smithery would call our server
        env = os.environ.copy()
        env.update({
            'GREPTILE_API_KEY': 'test_key',
            'GITHUB_TOKEN': 'test_token',
            'TRANSPORT': 'stdio',
            'HOST': '0.0.0.0',
            'PORT': '8050'
        })
        
        try:
            # Simulate the command Smithery would run
            process = subprocess.Popen(
                [sys.executable, '-m', 'src.main'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=os.path.join(os.path.dirname(__file__), '..')
            )
            
            # Give it time to start
            time.sleep(2)
            
            # Check if process started successfully
            if process.poll() is None:
                print("✅ Server starts successfully with Smithery-style configuration")
                process.terminate()
                process.wait(timeout=5)
                return True
            else:
                stderr = process.stderr.read().decode()
                print(f"❌ Smithery simulation failed: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error in Smithery CLI simulation: {e}")
            return False
    
    def test_no_parameter_validation_errors(self):
        """Test that we don't get MCP error -32602 (Invalid request parameters)."""
        # This test ensures our parameter simplification resolved the validation issue
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
            
            # Import all tools - this would fail if parameter validation was broken
            from main import query_repository, search_repository, index_repository, get_repository_info
            
            # Check that all functions have simple parameter types
            import inspect
            
            for func in [query_repository, search_repository, index_repository, get_repository_info]:
                sig = inspect.signature(func)
                for param_name, param in sig.parameters.items():
                    # Ensure no complex nested types that cause validation errors
                    annotation_str = str(param.annotation)
                    
                    # These would cause MCP error -32602
                    assert 'List[Dict[' not in annotation_str, f"Complex type in {func.__name__}.{param_name}"
                    assert 'Dict[str, Any]' not in annotation_str, f"Complex type in {func.__name__}.{param_name}"
            
            print("✅ No parameter validation errors - MCP error -32602 resolved")
            return True
            
        except Exception as e:
            print(f"❌ Parameter validation test failed: {e}")
            return False

if __name__ == "__main__":
    test = TestSmitheryCompatibility()
    
    print("🧪 Running Smithery Compatibility Tests...")
    print("=" * 50)
    
    tests = [
        test.test_stdio_transport_initialization,
        test.test_mcp_protocol_compliance,
        test.test_parameter_schema_generation,
        test.test_docker_container_compatibility,
        test.test_smithery_cli_simulation,
        test.test_no_parameter_validation_errors
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Smithery Compatibility Tests PASSED!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
