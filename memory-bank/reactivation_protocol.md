# Greptile MCP Reactivation Protocol

## Quick Start

1. **Navigate to project directory**
   ```bash
   cd /home/evilbastardxd/Desktop/tools/grep-mcp
   ```

2. **Start the MCP server**
   ```bash
   python -m src.main
   ```

3. **Verify activation**
   - Check console for successful startup messages
   - Server should be running on port 8050 (default)

## Session Continuation Steps

1. **Review memory bank**
   - Check `/memory-bank/activeContext.md` for current status
   - Review `/memory-bank/task_log.md` for pending tasks
   - Examine `/memory-bank/progress.md` for project status

2. **Update active context**
   - Modify `/memory-bank/activeContext.md` with new session details
   - Record session start time and focus areas

3. **Pick up next task**
   - Select next task from task_log.md based on priority
   - Format: `[CATEGORY:ID] Task description`
   - Update task status as you progress

## Key Configuration

- **Environment**: Ensure `.env` file contains valid API keys:
  - `GREPTILE_API_KEY`: Your Greptile API key
  - `GITHUB_TOKEN`: GitHub personal access token

- **Persistence**: Session IDs are hardset - no manual configuration needed
  - Memory bank automatically maintains context between sessions
  - No need to specify session IDs in queries

## Project Structure Refresher

- `src/main.py`: Core MCP server implementation
- `src/utils.py`: Greptile client implementation
- `memory-bank/`: Persistent context storage
- `.env`: Configuration file (based on `.env.example`)

## Current Priorities

1. Enhance streaming support for query responses
2. Set up testing framework
3. Complete API documentation
4. Finalize deployment instructions

## Common Operations

- **Test repository indexing**:
  ```bash
  curl -X POST http://localhost:8050/tools/greptile/index_repository \
    -H "Content-Type: application/json" \
    -d '{"remote":"github","repository":"owner/repo","branch":"main"}'
  ```

- **Check repository status**:
  ```bash
  curl -X POST http://localhost:8050/tools/greptile/get_repository_info \
    -H "Content-Type: application/json" \
    -d '{"remote":"github","repository":"owner/repo","branch":"main"}'
  ```

- **Docker deployment** (alternative to direct Python):
  ```bash
  docker build -t greptile-mcp .
  docker run --rm --env-file .env -p 8050:8050 greptile-mcp
  ```

## Troubleshooting

- **Server won't start**: Check API keys in `.env` file
- **Connection errors**: Verify network connectivity to api.greptile.com
- **"Repository not found"**: Ensure correct repository name and branch
- **API rate limits**: Monitor console for rate limit messages

## Session Documentation

After each session, update:
1. Task progress in `/memory-bank/task_log.md`
2. Project status in `/memory-bank/progress.md`
3. Current context in `/memory-bank/activeContext.md`
