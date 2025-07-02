# 🚀 GitHub Actions Workflows for Greptile MCP Server

This directory contains comprehensive GitHub Actions workflows for automated deployment, monitoring, and management of the Greptile MCP Server on Cloudflare Workers.

## 📋 Available Workflows

### 1. 🚀 [Deploy to Cloudflare Workers](./deploy-cloudflare.yml)
**Primary deployment workflow with multi-environment support**

- **Triggers**: Push to main/master, manual dispatch, PR validation
- **Features**: 
  - Multi-environment deployment (staging → production)
  - Comprehensive code quality checks and testing
  - Automatic rollback on deployment failures
  - Production deployments require manual approval
  - Deployment notifications and status reporting

### 2. 🔐 [Manage Cloudflare Secrets](./manage-secrets.yml)  
**Secret rotation and validation workflow**

- **Triggers**: Manual dispatch, scheduled weekly validation
- **Features**:
  - Secure secret rotation for API keys and tokens
  - Environment-specific secret management
  - Format validation before deployment
  - Audit logging and issue creation on failures

### 3. 🏥 [Health Monitoring](./monitor-health.yml)
**Continuous service health monitoring**

- **Triggers**: Scheduled checks, post-deployment, manual dispatch
- **Features**:
  - Multi-level health checks (basic, deep, performance)
  - Automatic issue creation on service degradation
  - Performance benchmarking and SLA monitoring
  - Business hours vs off-hours monitoring frequency

## 🔧 Setup Instructions

### 1. Required GitHub Repository Secrets

#### Cloudflare Configuration
```bash
CLOUDFLARE_API_TOKEN     # API token with Workers:Edit permissions
CLOUDFLARE_ACCOUNT_ID    # Your Cloudflare account ID
```

#### Environment-Specific Secrets
```bash
# Staging Environment
GREPTILE_API_KEY_STAGING    # Greptile API key for staging
GITHUB_TOKEN_STAGING        # GitHub token for staging

# Production Environment  
GREPTILE_API_KEY_PRODUCTION # Greptile API key for production
GITHUB_TOKEN_PRODUCTION     # GitHub token for production
```

#### Optional Integrations
```bash
SLACK_WEBHOOK_URL          # Slack webhook for deployment notifications
```

### 2. Setting Up Secrets

#### Using GitHub CLI
```bash
# Cloudflare secrets
gh secret set CLOUDFLARE_API_TOKEN
gh secret set CLOUDFLARE_ACCOUNT_ID

# Staging secrets
gh secret set GREPTILE_API_KEY_STAGING
gh secret set GITHUB_TOKEN_STAGING

# Production secrets
gh secret set GREPTILE_API_KEY_PRODUCTION
gh secret set GITHUB_TOKEN_PRODUCTION

# Optional: Slack notifications
gh secret set SLACK_WEBHOOK_URL
```

#### Using GitHub Web Interface
1. Navigate to your repository
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each required secret with its corresponding value

### 3. Cloudflare Workers Configuration

#### Getting Your Cloudflare API Token
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens)
2. Create a **Custom Token** with:
   - **Permissions**: `Cloudflare Workers:Edit`
   - **Account Resources**: Include your account
   - **Zone Resources**: Not required for Workers

#### Getting Your Account ID
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Select your account
3. Copy the **Account ID** from the right sidebar

## 🚀 Usage Guide

### Deployment Workflows

#### Automatic Deployment
Deployments trigger automatically on push to `main` or `master` branch:

```bash
git push origin main  # Triggers staging → production deployment
```

#### Manual Deployment
```bash
# Deploy to staging only
gh workflow run deploy-cloudflare.yml -f environment=staging

# Deploy to production (requires approval)
gh workflow run deploy-cloudflare.yml -f environment=production

# Deploy to both environments
gh workflow run deploy-cloudflare.yml -f environment=both

# Emergency deployment (skip tests)
gh workflow run deploy-cloudflare.yml \
  -f environment=production \
  -f skip_tests=true \
  -f force_deploy=true
```

### Secret Management

#### Validate All Secrets
```bash
gh workflow run manage-secrets.yml -f operation=validate-secrets
```

#### Rotate Secrets
```bash
# Rotate Greptile API keys in staging
gh workflow run manage-secrets.yml \
  -f operation=rotate-greptile-keys \
  -f environment=staging

# Rotate all secrets in production
gh workflow run manage-secrets.yml \
  -f operation=rotate-all-secrets \
  -f environment=production

# Emergency rotation (skip validations)
gh workflow run manage-secrets.yml \
  -f operation=rotate-all-secrets \
  -f environment=production \
  -f emergency=true
```

### Health Monitoring

#### Manual Health Checks
```bash
# Basic health check for both environments
gh workflow run monitor-health.yml

# Deep health check for production
gh workflow run monitor-health.yml \
  -f environment=production \
  -f deep_check=true

# Health check without creating issues
gh workflow run monitor-health.yml \
  -f create_issue=false
```

## 📊 Monitoring and Alerts

### Service URLs
- **Staging Health**: https://greptile-mcp-server-staging.workers.dev/health
- **Production Health**: https://greptile-mcp-server.workers.dev/health
- **Staging Info**: https://greptile-mcp-server-staging.workers.dev/mcp
- **Production Info**: https://greptile-mcp-server.workers.dev/mcp

### Monitoring Schedule
- **Business Hours** (8 AM - 8 PM UTC, Mon-Fri): Every 15 minutes
- **Off Hours & Weekends**: Every hour
- **Post-Deployment**: Automatic health checks
- **Weekly**: Secret validation on Mondays at 2 AM UTC

### Performance Thresholds
- **Excellent**: < 500ms response time
- **Good**: 500ms - 1000ms response time
- **Acceptable**: 1000ms - 2000ms response time  
- **Poor**: > 2000ms response time

### Automatic Alerting
- **GitHub Issues**: Created automatically for service degradation
- **Slack Notifications**: Optional integration for deployment status
- **Workflow Summaries**: Detailed reports in GitHub Actions interface

## 🔒 Security Best Practices

### Secret Management
1. **Regular Rotation**: Use the secret management workflow monthly
2. **Environment Separation**: Different secrets for staging/production
3. **Format Validation**: Automatic validation prevents invalid secrets
4. **Audit Trail**: All secret operations are logged

### Deployment Security
1. **Code Quality Gates**: Comprehensive linting, testing, security scans
2. **Staged Deployment**: Staging validation before production
3. **Manual Approval**: Production deployments require explicit approval
4. **Rollback Capability**: Automatic rollback on deployment failures

### Access Controls
1. **Branch Protection**: Protect main/master branches
2. **Required Reviews**: Require PR reviews for code changes
3. **Environment Protection**: Use GitHub environment protection rules
4. **Least Privilege**: API tokens with minimal required permissions

## 🐛 Troubleshooting

### Common Issues

#### Deployment Failures
1. **Check Secrets**: Ensure all required secrets are set correctly
2. **Validate Wrangler Config**: Verify `wrangler.toml` configuration
3. **Review Logs**: Check workflow logs for specific error messages
4. **Cloudflare Dashboard**: Check Workers dashboard for deployment status

#### Health Check Failures
1. **Service Status**: Check if the service is actually down
2. **Network Issues**: Temporary network problems may cause false positives
3. **Performance Degradation**: Slow responses may trigger timeout alerts
4. **Configuration Issues**: CORS or routing problems

#### Secret Management Issues
1. **Format Validation**: Ensure secrets match expected patterns
2. **Cloudflare Permissions**: Verify API token has Workers:Edit permissions
3. **Propagation Time**: Secrets may take up to 60 seconds to propagate
4. **Environment Mismatch**: Check that secrets are set for correct environment

### Recovery Procedures

#### Failed Deployment Recovery
```bash
# Check current deployments
wrangler deployments list --env production

# Manual rollback (if automated rollback failed)
wrangler rollback <deployment-id> --env production

# Emergency redeployment
gh workflow run deploy-cloudflare.yml \
  -f environment=production \
  -f skip_tests=true \
  -f force_deploy=true
```

#### Secret Recovery
```bash
# Validate current secrets
gh workflow run manage-secrets.yml -f operation=validate-secrets

# Emergency secret rotation
gh workflow run manage-secrets.yml \
  -f operation=rotate-all-secrets \
  -f environment=production \
  -f emergency=true
```

## 📚 Additional Resources

### Documentation
- [Cloudflare Workers Documentation](https://developers.cloudflare.com/workers/)
- [Wrangler CLI Documentation](https://developers.cloudflare.com/workers/wrangler/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

### Tools
- [GitHub CLI](https://cli.github.com/)
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/)
- [jq for JSON processing](https://stedolan.github.io/jq/)

### Monitoring
- [Cloudflare Workers Dashboard](https://dash.cloudflare.com/)
- [GitHub Actions Dashboard](https://github.com/features/actions)

## 🤝 Contributing

When modifying these workflows:

1. **Test Changes**: Always test workflow changes in a fork first
2. **Update Documentation**: Update this README for any significant changes
3. **Security Review**: Have security-related changes reviewed
4. **Backward Compatibility**: Ensure changes don't break existing deployments

## 📝 License

This workflow configuration is part of the Greptile MCP Server project and follows the same MIT license terms.

---

*For questions or issues with these workflows, please create a GitHub issue or contact the maintainers.*