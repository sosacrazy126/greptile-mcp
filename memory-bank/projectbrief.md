# Greptile MCP Server - Project Brief

## Project Overview
A Model Context Protocol (MCP) server that integrates with Greptile's AI-powered code analysis API to provide intelligent codebase querying capabilities. This server enables AI assistants to analyze, search, and understand codebases through natural language queries.

## Core Purpose
Transform how AI assistants interact with codebases by providing:
- **Natural Language Code Queries**: Ask questions about code in plain English
- **Intelligent Code Search**: Find relevant files and functions without exact matches
- **Repository Analysis**: Get insights about codebase structure and patterns
- **Conversation Context**: Maintain context across multiple queries about the same codebase

## Key Requirements

### Functional Requirements
1. **Repository Indexing**: Index GitHub/GitLab repositories for analysis
2. **Natural Language Queries**: Process questions about code functionality, patterns, and structure
3. **File Search**: Find relevant files based on semantic understanding
4. **Repository Information**: Provide status and metadata about indexed repositories
5. **Session Management**: Maintain conversation context across queries
6. **Streaming Support**: Real-time response streaming for long queries

### Technical Requirements
1. **MCP Protocol Compliance**: Full compatibility with MCP 2024-11-05 specification
2. **FastMCP 2.0 Framework**: Modern, simplified MCP server implementation
3. **Greptile API Integration**: Seamless integration with Greptile's analysis services
4. **Docker Deployment**: Containerized deployment for production environments
5. **Smithery Compatibility**: Deploy through Smithery AI platform
6. **Error Resilience**: Robust error handling and graceful degradation

### Integration Requirements
1. **Environment Configuration**: API keys and tokens via environment variables
2. **Multiple Repository Support**: Handle queries across multiple repositories
3. **Branch Flexibility**: Support different branches (main, dev, feature branches)
4. **Response Formatting**: JSON responses compatible with MCP clients

## Success Criteria
- ✅ **Smithery Deployment**: Successfully deploy and run on Smithery platform
- ✅ **Docker Registry Ready**: Prepared for Docker MCP Registry submission
- ✅ **Production Stable**: Handles real-world queries without errors
- ✅ **Performance Optimized**: Fast startup and response times
- ✅ **Developer Friendly**: Clear documentation and easy setup

## Target Users
- **AI Assistant Developers**: Building code-aware AI applications
- **Development Teams**: Analyzing large codebases efficiently
- **Code Reviewers**: Understanding unfamiliar codebases quickly
- **Documentation Writers**: Extracting insights from code for documentation

## Technology Stack
- **Framework**: FastMCP 2.0 (Modern MCP server framework)
- **Language**: Python 3.12
- **API Integration**: Greptile REST API
- **Deployment**: Docker containers
- **Platform**: Smithery AI, Docker MCP Registry

## Project Constraints
- **API Dependencies**: Requires Greptile API key and GitHub token
- **Network Requirements**: Outbound HTTPS access for API calls
- **Memory Considerations**: Efficient handling of large repository data
- **Rate Limiting**: Respect Greptile API rate limits

## Current Status
**PRODUCTION READY** - Successfully modernized, tested, and deployed with all critical issues resolved.
