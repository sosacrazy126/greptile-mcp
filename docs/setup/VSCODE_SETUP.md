# Adding Greptile MCP to VS Code

## Method 1: Using Cline Extension (Recommended)

1. Install the Cline extension from VS Code marketplace
2. Open VS Code settings (Ctrl+,)
3. Search for "cline.mcpServers"
4. Click "Edit in settings.json"
5. Add this configuration:

```json
{
  "cline.mcpServers": {
    "greptile-mcp": {
      "command": "/home/evilbastardxd/Desktop/tools/grep-mcp/.venv/bin/python",
      "args": ["-m", "src.main"],
      "cwd": "/home/evilbastardxd/Desktop/tools/grep-mcp",
      "env": {
        "GREPTILE_API_KEY": "YOUR_GREPTILE_API_KEY",
        "GITHUB_TOKEN": "YOUR_GITHUB_TOKEN",
        "TRANSPORT": "sse",
        "PORT": "8050"
      }
    }
  }
}
```

## Method 2: Using Continue Extension

1. Install Continue extension
2. Open the Continue config file: `~/.continue/config.json`
3. Add the greptile-mcp server to the mcpServers section

## Method 3: Using MCP Extension (if available)

Some VS Code extensions might support MCP directly. Check for:
- "MCP Client"
- "Model Context Protocol"
- Extensions that mention MCP support

## Usage in VS Code

Once configured, you can use greptile commands in the extension's chat interface:
- "Use greptile_help to show documentation"
- "Index the repository facebook/react"
- "Search for useState implementation in React"

## Troubleshooting

1. Make sure the Python virtual environment is activated
2. Check that the paths are correct
3. Verify API keys are valid
4. Restart VS Code after configuration changes

## Alternative: Run as HTTP Server

You can also run the Smithery HTTP server and connect via HTTP:

```bash
cd /home/evilbastardxd/Desktop/tools/grep-mcp
PORT=8088 .venv/bin/python -m src.smithery_server
```

Then configure your VS Code extension to connect to `http://localhost:8088/mcp`
