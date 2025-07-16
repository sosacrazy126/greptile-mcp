# Greptile API Analysis Tools

This directory contains comprehensive tools for reverse engineering and analyzing the Greptile API to better understand its endpoints, response structures, authentication patterns, and behavior.

## Tools Overview

### 1. `greptile_api_discovery.py`
**Purpose:** Discovers all available API endpoints and their basic characteristics.

**Features:**
- Probes known and potential endpoints
- Detects authentication requirements
- Identifies streaming support
- Analyzes rate limiting patterns
- Generates OpenAPI specification
- Creates comprehensive documentation

**Usage:**
```bash
export GREPTILE_API_KEY="your_api_key"
export GITHUB_TOKEN="your_github_token"
python greptile_api_discovery.py
```

**Output:**
- `api_discovery/discovery_report.json` - Raw discovery data
- `api_discovery/openapi_spec.yaml` - OpenAPI specification
- `api_discovery/api_reference.md` - Human-readable documentation

### 2. `greptile_response_analyzer.py`
**Purpose:** Performs deep analysis of API response structures and patterns.

**Features:**
- Schema extraction from responses
- Streaming response analysis
- Error pattern detection
- Authentication requirement testing
- Performance metrics collection
- Citation and session tracking

**Usage:**
```bash
export GREPTILE_API_KEY="your_api_key"
export GITHUB_TOKEN="your_github_token"
python greptile_response_analyzer.py
```

**Output:**
- `response_analysis.json` - Detailed response structure analysis

### 3. `run_api_analysis.py`
**Purpose:** Orchestrates complete API analysis combining discovery and response analysis.

**Features:**
- Runs both discovery and response analysis
- Generates combined insights
- Creates comprehensive reports
- Provides development recommendations
- Assesses API health and performance

**Usage:**
```bash
export GREPTILE_API_KEY="your_api_key"
export GITHUB_TOKEN="your_github_token"
python run_api_analysis.py
```

**Output:**
- `api_analysis_results/comprehensive_analysis.json` - Complete analysis data
- `api_analysis_results/analysis_report.md` - Executive summary report
- `api_analysis_results/discovery/` - Endpoint discovery results
- `api_analysis_results/response_analysis.json` - Response analysis results

## Quick Start

1. **Set up environment variables:**
```bash
export GREPTILE_API_KEY="your_greptile_api_key"
export GITHUB_TOKEN="your_github_personal_access_token"
export GREPTILE_BASE_URL="https://api.greptile.com/v2"  # Optional
```

2. **Run complete analysis:**
```bash
cd tools/
python run_api_analysis.py
```

3. **View results:**
- Check `api_analysis_results/analysis_report.md` for executive summary
- Review `api_analysis_results/comprehensive_analysis.json` for detailed data
- Examine `api_analysis_results/discovery/` for endpoint documentation

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GREPTILE_API_KEY` | Yes | Your Greptile API key |
| `GITHUB_TOKEN` | Yes | GitHub personal access token |
| `GREPTILE_BASE_URL` | No | API base URL (default: https://api.greptile.com/v2) |

## Analysis Components

### Endpoint Discovery
- **Known Endpoints:** `/repositories`, `/query`, `/search`, `/chats/{sessionId}`, `/repositories/{repositoryId}`
- **Probe Patterns:** Common API patterns like `/health`, `/status`, `/docs`, etc.
- **Authentication Testing:** Determines auth requirements for each endpoint
- **Response Analysis:** Basic response structure and status codes

### Response Structure Analysis
- **Schema Extraction:** Automatic JSON schema generation from responses
- **Streaming Analysis:** SSE (Server-Sent Events) parsing and chunk analysis
- **Error Pattern Detection:** Comprehensive error response analysis
- **Performance Metrics:** Response time measurement and analysis
- **Feature Detection:** Citations, sessions, and special response features

### Authentication Analysis
- **Multi-Auth Testing:** Tests API key only, GitHub token only, both, and neither
- **Error Response Analysis:** Analyzes authentication failure patterns
- **Token Validation:** Identifies token format requirements
- **Security Assessment:** Evaluates authentication implementation

### Combined Insights
- **API Health Assessment:** Overall API reliability and performance
- **Coverage Analysis:** Percentage of endpoints successfully analyzed
- **Performance Insights:** Response time analysis and optimization recommendations
- **Security Insights:** Authentication coverage and security patterns
- **Development Recommendations:** Actionable suggestions for API usage

## Example Output

### Discovery Results
```
GREPTILE API DISCOVERY SUMMARY
==================================================
Base URL: https://api.greptile.com/v2
Total Endpoints: 8
Rate Limiting: Detected

Endpoints found:
  🔒 POST /repositories 📡
  🔒 GET /repositories/{repositoryId}
  🔒 POST /query 📡
  🔒 POST /search
  🔒 GET /chats/{sessionId}
  🔒 GET /health
  🔒 GET /status
  🔒 GET /docs
```

### Response Analysis Summary
```
GREPTILE API RESPONSE ANALYSIS SUMMARY
==================================================
Total Requests: 25
Successful: 18
Errors: 7
Streaming Endpoints: 2
Average Response Time: 1.245s
Endpoints with Citations: 3
Endpoints with Sessions: 4
Auth Required Endpoints: 8
```

### Combined Analysis
```
GREPTILE API COMPREHENSIVE ANALYSIS COMPLETE
============================================================
API Health: Healthy
Performance: Good
Coverage: 87.5%
Security: 100.0% authenticated

Key Recommendations:
  • Leverage streaming endpoints for better user experience
  • Implement session management for conversational interfaces
  • Consider implementing request caching to improve response times
```

## Use Cases

### 1. API Integration Development
- Understand all available endpoints before integration
- Identify authentication requirements and patterns
- Discover streaming capabilities and session management
- Plan error handling strategies

### 2. Performance Optimization
- Identify slow endpoints for optimization
- Understand response patterns for caching strategies
- Analyze streaming vs. non-streaming performance
- Measure and monitor API response times

### 3. Security Assessment
- Verify authentication requirements across all endpoints
- Identify potential security vulnerabilities
- Understand token requirements and validation
- Assess rate limiting implementation

### 4. Documentation Generation
- Create comprehensive API documentation
- Generate OpenAPI specifications
- Provide usage examples and patterns
- Document error handling and edge cases

### 5. Testing and Validation
- Validate API behavior across all endpoints
- Test authentication mechanisms
- Verify response structures and schemas
- Identify breaking changes in API updates

## Dependencies

- `httpx` - Async HTTP client
- `pyyaml` - YAML processing
- `asyncio` - Async programming
- `json` - JSON processing
- `uuid` - UUID generation

## Error Handling

The tools include comprehensive error handling for:
- Network timeouts and connection errors
- Authentication failures
- Rate limiting responses
- Invalid endpoint responses
- JSON parsing errors
- Stream processing errors

## Safety Features

- **Test Repository:** Uses `octocat/Hello-World` as a safe test repository
- **Rate Limiting:** Includes delays between requests to avoid overwhelming the API
- **Error Recovery:** Continues analysis even when individual requests fail
- **Graceful Degradation:** Provides partial results when some components fail
- **Resource Cleanup:** Properly closes HTTP connections and cleans up resources

## Future Enhancements

- **Webhook Analysis:** Discover and analyze webhook endpoints
- **Admin Endpoint Discovery:** Explore administrative endpoints
- **Performance Benchmarking:** Comprehensive performance testing
- **API Versioning:** Analysis of API version differences
- **Mock Server Generation:** Create mock servers from analysis results
- **Integration Testing:** Automated integration test generation

## Contributing

To add new analysis capabilities:
1. Create a new analyzer class following the existing patterns
2. Add it to the `run_api_analysis.py` orchestrator
3. Update the documentation and examples
4. Test thoroughly with the provided test repository

## License

This tool is provided as-is for educational and development purposes. Ensure compliance with Greptile's terms of service when using these tools.