# Greptile MCP Activation Protocol

## Overview
This document outlines the activation protocol for the Greptile MCP (Model Context Protocol) implementation. It serves as a reference for initializing the system, updating log history, and tracking task progress.

## Initialization Sequence

1. **Environment Setup**
   - Verify API keys in `.env` file (GREPTILE_API_KEY and GITHUB_TOKEN)
   - Confirm network connectivity to Greptile API endpoints
   - Set appropriate transport mode (SSE or stdio)

2. **Server Startup**
   - Navigate to `/home/evilbastardxd/Desktop/tools/grep-mcp/`
   - Execute `python -m src.main` or use Docker container
   - Verify successful initialization in console output
   - Confirm server is listening on configured port (default: 8050)

3. **Memory Bank Initialization**
   - System automatically connects to memory bank directory
   - Hardset session ID maintains persistent context
   - No manual session management required

## Log History Management

The system automatically maintains a log history in the memory bank. To update manually:

1. **Progress Tracking**
   - Update `/home/evilbastardxd/Desktop/tools/grep-mcp/memory-bank/progress.md`
   - Mark completed tasks and add new ones
   - Document any issues or blockers encountered

2. **Implementation Context**
   - Update `/home/evilbastardxd/Desktop/tools/grep-mcp/memory-bank/greptile-mcp-implementation.md`
   - Document any changes to architecture or design
   - Note version updates or dependency changes

3. **Active Context**
   - Update `/home/evilbastardxd/Desktop/tools/grep-mcp/memory-bank/activeContext.md`
   - Record current session information and status
   - Document ongoing operations or queries

## Task Reference System

Use the following structure to organize and reference tasks:

1. **Task Categorization**
   - `FEATURE`: New functionality to implement
   - `BUG`: Issues needing resolution
   - `ENHANCEMENT`: Improvements to existing features
   - `DOCS`: Documentation updates
   - `TEST`: Test creation or modification

2. **Task Formatting**
   ```
   [CATEGORY:ID] Task description
   ```
   Example: `[FEATURE:01] Implement rate limiting for API calls`

3. **Task Tracking**
   - Add tasks to `/home/evilbastardxd/Desktop/tools/grep-mcp/memory-bank/progress.md`
   - Update status with checkboxes: `- [ ]` for pending, `- [x]` for completed
   - Reference task IDs in commit messages and PRs

## Operational Commands

### Start Server
```bash
cd /home/evilbastardxd/Desktop/tools/grep-mcp
python -m src.main
```

### Docker Deployment
```bash
cd /home/evilbastardxd/Desktop/tools/grep-mcp
docker build -t greptile-mcp .
docker run --rm --env-file .env -p 8050:8050 greptile-mcp
```

### Update Memory Bank
```bash
cd /home/evilbastardxd/Desktop/tools/grep-mcp
# Edit files in memory-bank directory using your preferred editor
```

## Next Task Reference

Based on the progress report, the next tasks are:

1. `[FEATURE:01]` Enhance streaming support for query responses
2. `[TEST:01]` Set up unit tests for client functionality
3. `[TEST:02]` Create integration tests for MCP tools
4. `[DOCS:01]` Add detailed API documentation
5. `[DOCS:02]` Create usage examples
6. `[DOCS:03]` Document error codes and troubleshooting

## Status Reporting

After any significant work session:

1. Update progress.md with completed tasks
2. Document any new issues in the "Known Issues" section
3. Adjust upcoming tasks as priorities shift
4. Commit changes to the memory bank

## Activation Verification

To verify successful activation:

1. Check server console for startup messages
2. Test basic repository information retrieval
3. Confirm memory bank files are accessible and up-to-date
4. Validate successful API communication

The system is considered active when all verification steps pass and the server responds to basic requests.
