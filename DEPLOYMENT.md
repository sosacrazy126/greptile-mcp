# Cloudflare Workers Deployment Guide

## Automatic GitHub Deployment Setup

Your Greptile MCP server is configured for automatic deployment to Cloudflare Workers via GitHub integration.

## Option 1: Deploy to Cloudflare Button (Recommended)

Click this button to automatically set up your repository with Cloudflare deployment:

[![Deploy to Workers](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/sosacrazy126/greptile-mcp)

This will:
- Fork/create a new repository in your GitHub account
- Set up automatic deployment on every push to main branch
- Configure Cloudflare Workers project with your repository
- Provide you with a live URL immediately

## Option 2: Manual GitHub Repository Import

1. **Go to Cloudflare Dashboard**
   - Navigate to Workers & Pages
   - Click "Create Application"
   - Select "Pages" tab
   - Choose "Connect to Git"

2. **Connect Your Repository**
   - Select GitHub as your Git provider
   - Choose your `greptile-mcp` repository
   - Configure the following settings:
     - **Project name**: `greptile-mcp-server`
     - **Production branch**: `main` (or `master`)
     - **Build command**: `npm run build` (optional)
     - **Build output directory**: Leave empty (we deploy directly)

3. **Set Environment Variables**
   In your Cloudflare project settings, add these environment variables:
   ```
   GREPTILE_API_KEY=your_greptile_api_key
   GITHUB_TOKEN=your_github_token
   GREPTILE_BASE_URL=https://api.greptile.com/v2
   ```

## Option 3: GitHub Actions Deployment

If you prefer using GitHub Actions, the repository includes a workflow file at `.github/workflows/cloudflare-deploy.yml`.

### Required GitHub Secrets

Add these secrets to your GitHub repository:
- `CLOUDFLARE_API_TOKEN` - Your Cloudflare API token
- `CLOUDFLARE_ACCOUNT_ID` - Your Cloudflare account ID
- `GREPTILE_API_KEY` - Your Greptile API key
- `GITHUB_TOKEN_MCP` - GitHub token for MCP access

### To set up GitHub Secrets:
1. Go to your repository on GitHub
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret" for each required secret

## Deployment Features

### Automatic Deployment
- **Triggers**: Every push to main/master branch
- **Build time**: ~2-3 minutes
- **Global deployment**: Available on Cloudflare's edge network
- **Zero downtime**: Rolling deployments with health checks

### Branch-based Environments
- **Main/Master branch** → Production deployment
- **Other branches** → Preview deployments (if configured)
- **Pull requests** → Preview deployments with unique URLs

### Deployment Status
- Check deployment status in Cloudflare Dashboard
- View logs and analytics in Workers Analytics
- Monitor performance and errors in real-time

## Post-Deployment Configuration

### 1. Verify Deployment
```bash
curl https://your-worker-name.your-account.workers.dev/health
```

### 2. Test MCP Tools
```bash
curl -X POST https://your-worker-name.your-account.workers.dev/sse \
  -H "Content-Type: application/json" \
  -d '{
    "method": "get_repository_info",
    "params": {
      "remote": "github",
      "repository": "microsoft/vscode",
      "branch": "main"
    }
  }'
```

### 3. Update MCP Clients
Update your MCP client configurations to use the new remote URL:

```json
{
  "mcpServers": {
    "greptile": {
      "transport": "sse",
      "url": "https://your-worker-name.your-account.workers.dev/sse"
    }
  }
}
```

## Custom Domain (Optional)

To use a custom domain:
1. Go to Workers & Pages → your project → Custom domains
2. Add your domain and follow DNS configuration steps
3. SSL certificates are automatically managed by Cloudflare

## Monitoring and Analytics

Cloudflare provides built-in monitoring:
- **Request analytics** - Volume, errors, latency
- **Real-time logs** - Debug issues as they happen
- **Geographic distribution** - See where requests come from
- **Performance metrics** - Response times and throughput

## Troubleshooting

### Common Issues
1. **Secrets not accessible** - Ensure environment variables are set in Cloudflare project settings
2. **Build failures** - Check GitHub Actions logs or Cloudflare deployment logs
3. **CORS errors** - The worker includes CORS headers for cross-origin requests

### Getting Help
- Check Cloudflare Workers documentation
- View deployment logs in Cloudflare Dashboard
- Monitor GitHub Actions workflow status
- Use the `/debug` endpoint to troubleshoot environment variables

## Benefits of Cloudflare Deployment

- **Global Edge Network**: Sub-50ms latency worldwide
- **Auto Scaling**: Handles traffic spikes automatically
- **Zero Maintenance**: No servers to manage
- **Built-in Security**: DDoS protection and WAF included
- **Cost Effective**: Pay only for requests (100k free requests/day)
- **High Availability**: 99.9%+ uptime SLA