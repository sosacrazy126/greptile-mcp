# Greptile MCP Project Brief

## Project Overview
Greptile MCP (Machine Callable Platform) is a server implementation that integrates the Greptile code search and analysis API with the MCP protocol. This allows AI assistants to interact with and query codebases through a standardized interface.

## Core Goals
1. Provide a simple, reliable MCP server for code search and repository analysis
2. Enable AI assistants to index, query, and search code repositories
3. Integrate seamlessly with the Greptile API
4. Support both SSE and stdio transport methods for flexible deployment

## Scope
The project includes:
- An MCP server with a defined set of tools for repository operations
- A client for interacting with the Greptile API
- Configuration options for authentication and deployment
- Documentation for setup and usage

## Technical Constraints
- Built with Python using FastMCP for the server implementation
- Requires Greptile API credentials and GitHub/GitLab tokens
- Designed to be containerized for easy deployment

## Success Criteria
- Successfully index and query repositories through the MCP interface
- Properly handle authentication and error states
- Support both streaming and non-streaming responses
- Provide clear documentation for setup and usage 