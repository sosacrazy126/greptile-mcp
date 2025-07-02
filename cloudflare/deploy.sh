#!/bin/bash

# Cloudflare Workers Deployment Script for Greptile MCP Server
# This script handles the deployment of the MCP server to Cloudflare Workers

set -e

echo "🚀 Deploying Greptile MCP Server to Cloudflare Workers..."

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "❌ Wrangler CLI not found. Installing..."
    npm install -g wrangler
fi

# Check if user is logged in to Cloudflare
if ! wrangler whoami &> /dev/null; then
    echo "🔐 Please log in to Cloudflare first:"
    wrangler login
fi

# Check for required environment variables in production
echo "🔍 Checking for required secrets..."

# Function to check and set secret if needed
check_and_set_secret() {
    local secret_name=$1
    local secret_description=$2
    
    if ! wrangler secret list | grep -q "$secret_name"; then
        echo "⚠️  Secret $secret_name not found. Please set it:"
        echo "   Description: $secret_description"
        read -p "   Enter value for $secret_name: " -s secret_value
        echo ""
        echo "$secret_value" | wrangler secret put "$secret_name"
        echo "✅ Secret $secret_name set successfully"
    else
        echo "✅ Secret $secret_name already exists"
    fi
}

# Check required secrets
check_and_set_secret "GREPTILE_API_KEY" "Your Greptile API key from https://app.greptile.com/settings/api"
check_and_set_secret "GITHUB_TOKEN" "GitHub Personal Access Token with repo permissions"

# Optional secrets
if ! wrangler secret list | grep -q "GREPTILE_BASE_URL"; then
    echo "ℹ️  GREPTILE_BASE_URL not set, using default: https://api.greptile.com/v2"
fi

# Choose deployment environment
echo ""
echo "🎯 Choose deployment target:"
echo "1) Development/Staging"
echo "2) Production"
read -p "Enter choice (1-2): " deploy_choice

case $deploy_choice in
    1)
        echo "🧪 Deploying to staging environment..."
        wrangler deploy --env staging
        ;;
    2)
        echo "🌟 Deploying to production environment..."
        wrangler deploy --env production
        ;;
    *)
        echo "📦 Deploying to default environment..."
        wrangler deploy
        ;;
esac

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Test your deployment with the health check endpoint"
echo "2. Update your MCP client configuration to use the new URL"
echo "3. Verify all tools are working correctly"
echo ""
echo "🔗 Your MCP server endpoints:"
echo "   Health: https://your-worker.your-account.workers.dev/health"
echo "   MCP: https://your-worker.your-account.workers.dev/sse"
echo ""
echo "📖 For client configuration examples, see the README.md file"