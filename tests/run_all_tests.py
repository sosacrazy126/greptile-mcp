#!/usr/bin/env python3
"""
Comprehensive Test Runner - Run All Test Suites
Runs all test suites and provides comprehensive validation report.
"""

import sys
import os
import subprocess
import asyncio
import time
from typing import Dict, List, Tuple

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class ComprehensiveTestRunner:
    """Run all test suites and generate comprehensive report."""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
        self.start_time = time.time()
    
    def run_sync_test(self, test_name: str, test_module: str) -> bool:
        """Run a synchronous test module."""
        try:
            print(f"\n🧪 Running {test_name}...")
            print("-" * 40)
            
            result = subprocess.run(
                [sys.executable, f'tests/{test_module}'],
                cwd=os.path.join(os.path.dirname(__file__), '..'),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            success = result.returncode == 0
            
            self.results[test_name] = {
                'success': success,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'type': 'sync'
            }
            
            if success:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                print(f"Error: {result.stderr}")
            
            return success
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_name} TIMED OUT")
            self.results[test_name] = {
                'success': False,
                'error': 'Test timed out',
                'type': 'sync'
            }
            return False
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            self.results[test_name] = {
                'success': False,
                'error': str(e),
                'type': 'sync'
            }
            return False
    
    async def run_async_test(self, test_name: str, test_module: str) -> bool:
        """Run an asynchronous test module."""
        try:
            print(f"\n🧪 Running {test_name}...")
            print("-" * 40)
            
            # Import and run the async test
            if test_module == 'test_parameter_mapping.py':
                from test_parameter_mapping import TestParameterMapping
                test = TestParameterMapping()
                
                await test.test_query_to_messages_conversion()
                await test.test_previous_messages_merging()
                await test.test_repositories_json_parsing()
                await test.test_search_repository_mapping()
                await test.test_json_error_handling()
                await test.test_return_value_serialization()
                
            elif test_module == 'test_end_to_end.py':
                from test_end_to_end import TestEndToEndFunctionality
                test = TestEndToEndFunctionality()
                
                await test.test_index_repository_functionality()
                await test.test_query_repository_functionality()
                await test.test_search_repository_functionality()
                await test.test_get_repository_info_functionality()
                await test.test_streaming_functionality()
                await test.test_session_management()
                await test.test_multiple_repositories()
                await test.test_conversation_context()
                
            elif test_module == 'test_error_handling.py':
                from test_error_handling import TestErrorHandling
                test = TestErrorHandling()
                
                await test.test_invalid_json_parameters()
                await test.test_greptile_client_errors()
                await test.test_network_timeout_errors()
                await test.test_authentication_errors()
                await test.test_empty_parameters()
                await test.test_malformed_repository_data()
                await test.test_streaming_errors()
                await test.test_client_initialization_errors()
                await test.test_error_response_format()
            
            print(f"✅ {test_name} PASSED")
            self.results[test_name] = {'success': True, 'type': 'async'}
            return True
            
        except Exception as e:
            print(f"❌ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            self.results[test_name] = {
                'success': False,
                'error': str(e),
                'type': 'async'
            }
            return False
    
    def test_docker_integration(self) -> bool:
        """Test Docker integration and Smithery compatibility."""
        try:
            print(f"\n🐳 Running Docker Integration Tests...")
            print("-" * 40)
            
            # Test Docker build
            print("Building Docker image...")
            build_result = subprocess.run(
                ['docker', 'build', '-t', 'greptile-mcp-test', '.'],
                cwd=os.path.join(os.path.dirname(__file__), '..'),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if build_result.returncode != 0:
                print(f"❌ Docker build failed: {build_result.stderr}")
                return False
            
            print("✅ Docker build successful")
            
            # Test container startup
            print("Testing container startup...")
            run_result = subprocess.run(
                [
                    'docker', 'run', '--rm',
                    '-e', 'GREPTILE_API_KEY=test_key',
                    '-e', 'GITHUB_TOKEN=test_token',
                    'greptile-mcp-test',
                    'python', '-c', 'from src.main import mcp; print("Container OK")'
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if run_result.returncode == 0 and "Container OK" in run_result.stdout:
                print("✅ Docker container startup successful")
                self.results['Docker Integration'] = {'success': True, 'type': 'docker'}
                return True
            else:
                print(f"❌ Docker container test failed: {run_result.stderr}")
                self.results['Docker Integration'] = {
                    'success': False,
                    'error': run_result.stderr,
                    'type': 'docker'
                }
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Docker test timed out")
            self.results['Docker Integration'] = {
                'success': False,
                'error': 'Docker test timed out',
                'type': 'docker'
            }
            return False
        except Exception as e:
            print(f"❌ Docker test error: {e}")
            self.results['Docker Integration'] = {
                'success': False,
                'error': str(e),
                'type': 'docker'
            }
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all test suites."""
        print("🚀 Starting Comprehensive Test Suite")
        print("=" * 60)
        
        test_results = {}
        
        # 1. Parameter Validation Tests (sync)
        test_results['Parameter Validation'] = self.run_sync_test(
            'Parameter Validation', 'test_parameter_validation.py'
        )
        
        # 2. Parameter Mapping Tests (async)
        test_results['Parameter Mapping'] = await self.run_async_test(
            'Parameter Mapping', 'test_parameter_mapping.py'
        )
        
        # 3. Smithery Compatibility Tests (sync)
        test_results['Smithery Compatibility'] = self.run_sync_test(
            'Smithery Compatibility', 'test_smithery_compatibility.py'
        )
        
        # 4. End-to-End Functionality Tests (async)
        test_results['End-to-End Functionality'] = await self.run_async_test(
            'End-to-End Functionality', 'test_end_to_end.py'
        )
        
        # 5. Error Handling Tests (async)
        test_results['Error Handling'] = await self.run_async_test(
            'Error Handling', 'test_error_handling.py'
        )
        
        # 6. Docker Integration Tests
        test_results['Docker Integration'] = self.test_docker_integration()
        
        return test_results
    
    def generate_report(self, test_results: Dict[str, bool]) -> None:
        """Generate comprehensive test report."""
        end_time = time.time()
        duration = end_time - self.start_time
        
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        passed = sum(1 for success in test_results.values() if success)
        total = len(test_results)
        
        print(f"⏱️  Total Duration: {duration:.2f} seconds")
        print(f"📈 Overall Results: {passed}/{total} test suites passed")
        print(f"📊 Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 Test Suite Results:")
        print("-" * 40)
        
        for test_name, success in test_results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            
            if not success and test_name in self.results:
                error = self.results[test_name].get('error', 'Unknown error')
                print(f"     Error: {error}")
        
        print("\n🎯 Fix Validation Summary:")
        print("-" * 40)
        
        fixes = [
            ("Parameter Validation", "FastMCP schema compatibility", test_results.get('Parameter Validation', False)),
            ("Parameter Mapping", "MCP tools → GreptileClient mapping", test_results.get('Parameter Mapping', False)),
            ("Smithery Compatibility", "MCP error -32602 resolution", test_results.get('Smithery Compatibility', False)),
            ("End-to-End Functionality", "All 4 tools working correctly", test_results.get('End-to-End Functionality', False)),
            ("Error Handling", "Robust error responses", test_results.get('Error Handling', False)),
            ("Docker Integration", "Container deployment ready", test_results.get('Docker Integration', False))
        ]
        
        for fix_name, description, success in fixes:
            status = "✅" if success else "❌"
            print(f"{status} {fix_name}: {description}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Greptile MCP Server is production ready!")
            print("✅ Smithery deployment should work without errors")
            print("✅ Docker Registry submission ready")
            print("✅ All fixes validated and working")
        else:
            print(f"\n⚠️  {total - passed} test suite(s) failed")
            print("❌ Issues need to be resolved before production deployment")
        
        print("=" * 60)

async def main():
    """Main test runner entry point."""
    runner = ComprehensiveTestRunner()
    
    try:
        test_results = await runner.run_all_tests()
        runner.generate_report(test_results)
        
        # Exit with appropriate code
        all_passed = all(test_results.values())
        sys.exit(0 if all_passed else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
