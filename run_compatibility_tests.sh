#!/bin/bash

# Greptile MCP Server - Compatibility Test Suite Runner
# 
# This script runs the complete compatibility test suite to validate
# that the Cloudflare Workers deployment maintains full backward 
# compatibility with the existing Python FastMCP implementation.

set -e

echo "🧪 Greptile MCP Server - Compatibility Test Suite"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [[ ! -f "src/main.py" || ! -f "cloudflare/worker.py" ]]; then
    echo "❌ Error: Please run this script from the greptile-mcp project root directory"
    exit 1
fi

# Set up test environment
echo "🔧 Setting up test environment..."
export GREPTILE_API_KEY="test_api_key_compatibility"
export GITHUB_TOKEN="ghp_test_token_compatibility"
export GREPTILE_BASE_URL="https://api.greptile.test/v2"

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ Error: pytest is not installed. Please install it with: pip install pytest pytest-asyncio"
    exit 1
fi

# Check if required dependencies are available
echo "📦 Checking dependencies..."
python -c "import sys; sys.path.append('src'); import main" 2>/dev/null || {
    echo "❌ Error: Cannot import src.main. Please install dependencies: pip install -r requirements.txt"
    exit 1
}

python -c "import sys; sys.path.append('cloudflare'); import shared_utils" 2>/dev/null || {
    echo "❌ Error: Cannot import cloudflare.shared_utils. Please check cloudflare/ directory"
    exit 1
}

echo "✅ All dependencies available"
echo ""

# Run compatibility test suites
echo "🚀 Running Compatibility Test Suites"
echo "======================================"
echo ""

# 1. Core Compatibility Tests
echo "1️⃣  Running Core Compatibility Tests..."
echo "   Testing: API compatibility, session management, response formats"
python -m pytest test_core_compatibility.py -v --tb=short
CORE_EXIT_CODE=$?

if [[ $CORE_EXIT_CODE -eq 0 ]]; then
    echo "   ✅ Core compatibility tests PASSED"
else
    echo "   ❌ Core compatibility tests FAILED (exit code: $CORE_EXIT_CODE)"
fi
echo ""

# 2. Local Deployment Tests  
echo "2️⃣  Running Local Deployment Tests..."
echo "   Testing: Docker compatibility, start scripts, infrastructure"
python -m pytest test_local_deployment.py::TestLocalDeployment::test_docker_compatibility test_local_deployment.py::TestLocalDeployment::test_start_script_compatibility -v --tb=short
LOCAL_EXIT_CODE=$?

if [[ $LOCAL_EXIT_CODE -eq 0 ]]; then
    echo "   ✅ Local deployment tests PASSED"
else
    echo "   ❌ Local deployment tests FAILED (exit code: $LOCAL_EXIT_CODE)"
fi
echo ""

# 3. Original Implementation Tests (existing test suite)
echo "3️⃣  Running Original Implementation Tests..."
echo "   Testing: Existing test suite to ensure no regressions"
if [[ -f "src/tests/test_server.py" ]]; then
    python -m pytest src/tests/test_server.py -v --tb=short
    ORIGINAL_EXIT_CODE=$?
    
    if [[ $ORIGINAL_EXIT_CODE -eq 0 ]]; then
        echo "   ✅ Original implementation tests PASSED"
    else
        echo "   ❌ Original implementation tests FAILED (exit code: $ORIGINAL_EXIT_CODE)"
    fi
else
    echo "   ⚠️  Original test suite not found, skipping"
    ORIGINAL_EXIT_CODE=0
fi
echo ""

# 4. Local Server Smoke Test
echo "4️⃣  Running Local Server Smoke Test..."
echo "   Testing: Local server can start and respond"

# Start server in background
timeout 10s python -m src.main > /tmp/greptile_server.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Check if server is running
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "   ✅ Local server started successfully"
    # Clean up
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
    SERVER_EXIT_CODE=0
else
    echo "   ❌ Local server failed to start"
    echo "   📋 Server log:"
    cat /tmp/greptile_server.log
    SERVER_EXIT_CODE=1
fi
echo ""

# Summary
echo "📊 Test Results Summary"
echo "======================"
echo ""

TOTAL_FAILURES=0

if [[ $CORE_EXIT_CODE -eq 0 ]]; then
    echo "✅ Core Compatibility: PASSED"
else
    echo "❌ Core Compatibility: FAILED"
    ((TOTAL_FAILURES++))
fi

if [[ $LOCAL_EXIT_CODE -eq 0 ]]; then
    echo "✅ Local Deployment: PASSED"
else
    echo "❌ Local Deployment: FAILED"
    ((TOTAL_FAILURES++))
fi

if [[ $ORIGINAL_EXIT_CODE -eq 0 ]]; then
    echo "✅ Original Implementation: PASSED"
else
    echo "❌ Original Implementation: FAILED"
    ((TOTAL_FAILURES++))
fi

if [[ $SERVER_EXIT_CODE -eq 0 ]]; then
    echo "✅ Local Server Smoke Test: PASSED"
else
    echo "❌ Local Server Smoke Test: FAILED"
    ((TOTAL_FAILURES++))
fi

echo ""

# Final verdict
if [[ $TOTAL_FAILURES -eq 0 ]]; then
    echo "🎉 ALL COMPATIBILITY TESTS PASSED!"
    echo ""
    echo "✅ The Cloudflare Workers deployment maintains full backward compatibility"
    echo "✅ Existing client configurations will continue to work"
    echo "✅ Local/Docker deployment remains unchanged and functional"
    echo ""
    echo "📋 See COMPATIBILITY_REPORT.md for detailed analysis and recommendations"
    echo ""
    echo "🚀 SAFE TO DEPLOY CLOUDFLARE WORKERS VERSION"
    exit 0
else
    echo "⚠️  COMPATIBILITY ISSUES FOUND ($TOTAL_FAILURES failures)"
    echo ""
    echo "❌ Please review test failures before deployment"
    echo "📋 See COMPATIBILITY_REPORT.md for detailed analysis"
    echo ""
    echo "🔧 Recommended actions:"
    echo "   1. Review failed test output above"
    echo "   2. Check COMPATIBILITY_REPORT.md for specific issues"
    echo "   3. Fix compatibility issues before deployment"
    exit $TOTAL_FAILURES
fi