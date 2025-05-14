#!/bin/bash
# Start script for Greptile MCP Server

# Default values
TRANSPORT=${TRANSPORT:-sse}
PORT=${PORT:-8050}
HOST=${HOST:-0.0.0.0}

# Display banner
echo "===================================================="
echo "  Greptile MCP Server"
echo "===================================================="
echo "Transport: $TRANSPORT"
if [ "$TRANSPORT" = "sse" ]; then
  echo "Host: $HOST"
  echo "Port: $PORT"
fi
echo "===================================================="

# Check for essential environment variables
if [ -z "$GREPTILE_API_KEY" ]; then
  echo "❌ ERROR: GREPTILE_API_KEY environment variable is not set"
  echo "Please set it in your .env file or export it in your shell"
  exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
  echo "⚠️ WARNING: GITHUB_TOKEN environment variable is not set"
  echo "This may cause issues when accessing private repositories"
fi

# Load environment variables if .env exists
if [ -f .env ]; then
  echo "📁 Loading environment from .env file"
  export $(grep -v '^#' .env | xargs)
fi

# Activate virtual environment if exists
if [ -d .venv ]; then
  echo "🔄 Activating virtual environment"
  source .venv/bin/activate
fi

# Start the server with appropriate transport
if [ "$TRANSPORT" = "sse" ]; then
  echo "🚀 Starting MCP server with SSE transport on $HOST:$PORT"
  python -m src.main
else
  echo "🚀 Starting MCP server with stdio transport"
  python -m src.main
fi