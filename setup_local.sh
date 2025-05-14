#!/bin/bash
# Setup script for Greptile MCP

echo "===================================================="
echo "  Greptile MCP Local Setup"
echo "===================================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e .

# Check for .env file
if [ ! -f ".env" ]; then
  echo "Creating .env file from template..."
  cp .env.example .env
  echo ""
  echo "⚠️  IMPORTANT: Edit the .env file and add your API keys:"
  echo "   - GREPTILE_API_KEY: Get from https://app.greptile.com/settings/api"
  echo "   - GITHUB_TOKEN: Your GitHub personal access token"
  echo ""
fi

echo ""
echo "===================================================="
echo "  Setup complete! 🎉"
echo "===================================================="
echo ""
echo "To use Greptile MCP, you have two options:"
echo ""
echo "1. Run as SSE server (when using from Claude Desktop or other clients):"
echo "   source .venv/bin/activate"
echo "   python -m src.main"
echo ""
echo "2. Run as HTTP server (for Smithery/web deployment):"
echo "   source .venv/bin/activate"
echo "   python -m src.smithery_server"
echo ""
echo "===================================================="
