# 🧪 Greptile MCP Server Test Suite

Comprehensive test suite to validate all fixes and ensure production readiness.

## 📋 Test Coverage

### 1. **Parameter Validation Tests** (`test_parameter_validation.py`)
- ✅ FastMCP server initialization without schema errors
- ✅ Tool registration with simplified parameter types
- ✅ JSON parameter parsing and validation
- ✅ Parameter defaults and type compatibility

### 2. **Parameter Mapping Tests** (`test_parameter_mapping.py`)
- ✅ Query string to messages format conversion
- ✅ Previous messages merging and context preservation
- ✅ Repositories JSON parsing and validation
- ✅ Return value JSON serialization
- ✅ Error handling for invalid JSON

### 3. **Smithery Compatibility Tests** (`test_smithery_compatibility.py`)
- ✅ Stdio transport initialization (used by Smithery)
- ✅ MCP protocol compliance and message handling
- ✅ Parameter schema generation without validation errors
- ✅ Docker container compatibility with Smithery environment
- ✅ No MCP error -32602 (Invalid request parameters)

### 4. **End-to-End Functionality Tests** (`test_end_to_end.py`)
- ✅ All 4 MCP tools working correctly:
  - `index_repository` - Repository indexing
  - `query_repository` - Natural language queries with AI responses
  - `search_repository` - File search without full analysis
  - `get_repository_info` - Repository status and metadata
- ✅ Streaming functionality and session management
- ✅ Multiple repositories handling
- ✅ Conversation context preservation

### 5. **Error Handling Tests** (`test_error_handling.py`)
- ✅ Invalid JSON parameter handling
- ✅ GreptileClient API error responses
- ✅ Network timeout and authentication errors
- ✅ Empty parameters and malformed data
- ✅ Streaming errors and client initialization failures
- ✅ Consistent error response format

### 6. **Docker Integration Tests** (in `run_all_tests.py`)
- ✅ Docker image builds successfully
- ✅ Container starts with Smithery-style environment variables
- ✅ Server initializes correctly in containerized environment

## 🚀 Running Tests

### **Run All Tests (Recommended)**
```bash
cd tests
python run_all_tests.py
```

### **Run Individual Test Suites**
```bash
# Parameter validation
python test_parameter_validation.py

# Parameter mapping
python test_parameter_mapping.py

# Smithery compatibility
python test_smithery_compatibility.py

# End-to-end functionality
python test_end_to_end.py

# Error handling
python test_error_handling.py
```

### **Run with Docker**
```bash
# Build and test Docker image
docker build -t greptile-mcp-test .
docker run --rm -e GREPTILE_API_KEY=test -e GITHUB_TOKEN=test greptile-mcp-test python tests/run_all_tests.py
```

## 📊 Expected Results

When all tests pass, you should see:

```
🎉 ALL TESTS PASSED! Greptile MCP Server is production ready!
✅ Smithery deployment should work without errors
✅ Docker Registry submission ready
✅ All fixes validated and working
```

## 🔧 Test Environment Setup

### **Local Testing**
```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Set environment variables (optional for most tests)
export GREPTILE_API_KEY=your_test_key
export GITHUB_TOKEN=your_test_token
```

### **Docker Testing**
```bash
# Build test image
docker build -t greptile-mcp-test .

# Run tests in container
docker run --rm greptile-mcp-test python tests/run_all_tests.py
```

## 🎯 What These Tests Validate

### **Fix Validation:**
1. **✅ MCP Error -32602 Resolved** - Parameter validation errors fixed
2. **✅ TypeError Fixed** - Parameter mapping between MCP tools and GreptileClient corrected
3. **✅ Smithery Compatibility** - Server works with Smithery's npx CLI
4. **✅ FastMCP 2.0 Compliance** - Modern MCP framework compatibility
5. **✅ Production Readiness** - All functionality working end-to-end

### **Quality Assurance:**
- **Parameter Types**: Simplified from complex nested types to JSON strings
- **Error Handling**: Robust error responses for all failure scenarios
- **API Compatibility**: 100% compatibility with GreptileClient methods
- **Session Management**: Proper conversation context and session handling
- **Docker Deployment**: Container works in production environments

## 🐛 Troubleshooting

### **Common Issues:**

1. **Import Errors**
   ```bash
   # Ensure you're running from the project root
   cd /path/to/greptile-mcp
   python tests/run_all_tests.py
   ```

2. **Docker Not Available**
   ```bash
   # Skip Docker tests if Docker isn't available
   python test_parameter_validation.py
   python test_parameter_mapping.py
   # ... run individual tests
   ```

3. **Test Timeouts**
   ```bash
   # Some tests may timeout on slower systems
   # This is usually not a problem for the actual functionality
   ```

## 📈 Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Greptile MCP Tests
  run: |
    pip install -r requirements.txt
    pip install -r tests/requirements.txt
    python tests/run_all_tests.py
```

## 🎉 Success Criteria

All tests passing indicates:
- ✅ **Smithery deployment will work** without MCP error -32602
- ✅ **Docker Registry submission ready** with all requirements met
- ✅ **Production deployment safe** with robust error handling
- ✅ **All 4 MCP tools functional** with proper parameter mapping
- ✅ **FastMCP 2.0 compliant** with modern MCP standards
