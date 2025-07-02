# OAuth Configuration Examples

This document provides configuration examples for setting up OAuth authentication with different providers for the Greptile MCP server running on Cloudflare Workers.

## Table of Contents

- [General Configuration](#general-configuration)
- [GitHub OAuth](#github-oauth)
- [Google OAuth](#google-oauth)
- [Auth0 OAuth](#auth0-oauth)
- [Environment Variables Reference](#environment-variables-reference)
- [Deployment Examples](#deployment-examples)

## General Configuration

### Required Base Configuration

```bash
# Enable OAuth
OAUTH_ENABLED=true

# JWT Secret (generate a secure random string)
OAUTH_JWT_SECRET=your_secure_jwt_secret_here

# JWT Token expiration (hours)
OAUTH_JWT_EXPIRATION_HOURS=24

# Whether to require authentication for all requests
OAUTH_REQUIRE_AUTH=false

# Admin users (comma-separated list of user IDs or usernames)
OAUTH_ADMIN_USERS=user123,admin_user,github_username

# Allowed repositories (comma-separated, empty means all allowed)
OAUTH_ALLOWED_REPOSITORIES=owner/repo1,owner/repo2
```

## GitHub OAuth

### 1. Create GitHub OAuth App

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Fill in the application details:
   - **Application name**: Your MCP Server
   - **Homepage URL**: `https://your-worker.your-subdomain.workers.dev`
   - **Authorization callback URL**: `https://your-worker.your-subdomain.workers.dev/auth/callback?provider=github`

### 2. Environment Variables

```bash
# GitHub OAuth Configuration
OAUTH_GITHUB_CLIENT_ID=your_github_client_id
OAUTH_GITHUB_CLIENT_SECRET=your_github_client_secret
OAUTH_GITHUB_REDIRECT_URI=https://your-worker.your-subdomain.workers.dev/auth/callback
```

### 3. Wrangler Secrets

```bash
# Set secrets using Wrangler CLI
wrangler secret put OAUTH_GITHUB_CLIENT_SECRET
wrangler secret put OAUTH_JWT_SECRET
```

### 4. Usage Example

```javascript
// Client-side authentication flow
const authResponse = await fetch('https://your-worker.your-subdomain.workers.dev/auth/login?provider=github');
const { auth_url } = await authResponse.json();

// Redirect user to GitHub
window.location.href = auth_url;

// After callback, exchange code for token
const callbackResponse = await fetch('https://your-worker.your-subdomain.workers.dev/auth/callback', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ code, state, provider: 'github' })
});

const { token } = await callbackResponse.json();

// Use token for MCP requests
const mcpResponse = await fetch('https://your-worker.your-subdomain.workers.dev/mcp', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    method: 'query_repository',
    params: {
      query: 'How does authentication work?',
      repositories: [{ remote: 'github', repository: 'owner/repo', branch: 'main' }]
    }
  })
});
```

## Google OAuth

### 1. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Configure OAuth consent screen
6. Set authorized redirect URI: `https://your-worker.your-subdomain.workers.dev/auth/callback`

### 2. Environment Variables

```bash
# Google OAuth Configuration
OAUTH_GOOGLE_CLIENT_ID=your_google_client_id.googleusercontent.com
OAUTH_GOOGLE_CLIENT_SECRET=your_google_client_secret
OAUTH_GOOGLE_REDIRECT_URI=https://your-worker.your-subdomain.workers.dev/auth/callback
```

### 3. Wrangler Secrets

```bash
wrangler secret put OAUTH_GOOGLE_CLIENT_SECRET
wrangler secret put OAUTH_JWT_SECRET
```

### 4. Usage Example

```javascript
// Initiate Google OAuth
const authResponse = await fetch('https://your-worker.your-subdomain.workers.dev/auth/login?provider=google');
const { auth_url } = await authResponse.json();
window.location.href = auth_url;
```

## Auth0 OAuth

### 1. Create Auth0 Application

1. Go to [Auth0 Dashboard](https://manage.auth0.com/)
2. Create a new application (Single Page Application)
3. Configure allowed callback URLs: `https://your-worker.your-subdomain.workers.dev/auth/callback`
4. Configure allowed logout URLs: `https://your-worker.your-subdomain.workers.dev`

### 2. Environment Variables

```bash
# Auth0 OAuth Configuration
OAUTH_AUTH0_CLIENT_ID=your_auth0_client_id
OAUTH_AUTH0_CLIENT_SECRET=your_auth0_client_secret
OAUTH_AUTH0_DOMAIN=your-tenant.auth0.com
OAUTH_AUTH0_REDIRECT_URI=https://your-worker.your-subdomain.workers.dev/auth/callback
```

### 3. Wrangler Secrets

```bash
wrangler secret put OAUTH_AUTH0_CLIENT_SECRET
wrangler secret put OAUTH_JWT_SECRET
```

### 4. Usage Example

```javascript
// Initiate Auth0 OAuth
const authResponse = await fetch('https://your-worker.your-subdomain.workers.dev/auth/login?provider=auth0');
const { auth_url } = await authResponse.json();
window.location.href = auth_url;
```

## Environment Variables Reference

### Core OAuth Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OAUTH_ENABLED` | No | `false` | Enable/disable OAuth authentication |
| `OAUTH_JWT_SECRET` | Yes* | N/A | Secret key for JWT token signing |
| `OAUTH_JWT_EXPIRATION_HOURS` | No | `24` | JWT token expiration time |
| `OAUTH_REQUIRE_AUTH` | No | `false` | Require authentication for all requests |

### Permission Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OAUTH_ADMIN_USERS` | No | Empty | Comma-separated admin user IDs/usernames |
| `OAUTH_ALLOWED_REPOSITORIES` | No | Empty | Comma-separated allowed repositories |

### GitHub Provider

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OAUTH_GITHUB_CLIENT_ID` | Yes* | N/A | GitHub OAuth app client ID |
| `OAUTH_GITHUB_CLIENT_SECRET` | Yes* | N/A | GitHub OAuth app client secret |
| `OAUTH_GITHUB_REDIRECT_URI` | No | Auto-generated | OAuth callback URL |

### Google Provider

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OAUTH_GOOGLE_CLIENT_ID` | Yes* | N/A | Google OAuth client ID |
| `OAUTH_GOOGLE_CLIENT_SECRET` | Yes* | N/A | Google OAuth client secret |
| `OAUTH_GOOGLE_REDIRECT_URI` | No | Auto-generated | OAuth callback URL |

### Auth0 Provider

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OAUTH_AUTH0_CLIENT_ID` | Yes* | N/A | Auth0 application client ID |
| `OAUTH_AUTH0_CLIENT_SECRET` | Yes* | N/A | Auth0 application client secret |
| `OAUTH_AUTH0_DOMAIN` | Yes* | N/A | Auth0 tenant domain |
| `OAUTH_AUTH0_REDIRECT_URI` | No | Auto-generated | OAuth callback URL |

*Required only if OAuth is enabled and the provider is being used.

## Deployment Examples

### Development Environment (.dev.vars)

```bash
# .dev.vars file for local development
OAUTH_ENABLED=true
OAUTH_JWT_SECRET=dev_jwt_secret_change_in_production
OAUTH_REQUIRE_AUTH=false
OAUTH_GITHUB_CLIENT_ID=your_github_client_id
OAUTH_GITHUB_CLIENT_SECRET=your_github_client_secret
OAUTH_GITHUB_REDIRECT_URI=http://localhost:8787/auth/callback
```

### Production Deployment

```bash
# Set production secrets
wrangler secret put OAUTH_JWT_SECRET
wrangler secret put OAUTH_GITHUB_CLIENT_SECRET
wrangler secret put OAUTH_GOOGLE_CLIENT_SECRET
wrangler secret put OAUTH_AUTH0_CLIENT_SECRET

# Deploy with production environment
wrangler deploy --env production
```

### Staging Environment

```bash
# wrangler.toml configuration for staging
[env.staging.vars]
OAUTH_ENABLED = "true"
OAUTH_REQUIRE_AUTH = "false"
OAUTH_GITHUB_REDIRECT_URI = "https://your-staging-worker.your-subdomain.workers.dev/auth/callback"

# Set staging secrets
wrangler secret put OAUTH_JWT_SECRET --env staging
wrangler secret put OAUTH_GITHUB_CLIENT_SECRET --env staging

# Deploy to staging
wrangler deploy --env staging
```

## Security Best Practices

### 1. JWT Secret Management

- Generate a strong, random JWT secret (minimum 32 characters)
- Use different secrets for different environments
- Never commit secrets to version control
- Rotate secrets regularly

```bash
# Generate a secure JWT secret
openssl rand -base64 32
```

### 2. OAuth App Security

- Use HTTPS for all redirect URIs in production
- Restrict redirect URIs to your actual domains
- Enable state parameter validation
- Monitor OAuth app usage

### 3. Permission Management

- Follow principle of least privilege
- Regularly audit admin users list
- Use repository-level restrictions when possible
- Monitor authentication logs

### 4. Rate Limiting

The OAuth middleware includes built-in rate limiting:
- Authenticated users: 100 requests/minute, 1000 requests/hour
- Unauthenticated users: 10 requests/minute, 100 requests/hour

### 5. CORS Configuration

Configure appropriate CORS settings in your wrangler.toml:

```toml
[env.production.vars]
CORS_ORIGIN = "https://your-frontend-domain.com"

[env.development.vars]
CORS_ORIGIN = "*"
```

## Troubleshooting

### Common Issues

1. **Invalid redirect_uri error**
   - Ensure the redirect URI in your OAuth app matches exactly
   - Check for trailing slashes and HTTP vs HTTPS

2. **JWT verification fails**
   - Verify JWT secret is set correctly
   - Check token expiration time
   - Ensure consistent secret across deployments

3. **Permission denied errors**
   - Check user is in admin list if required
   - Verify repository access permissions
   - Check rate limiting status

4. **CORS errors**
   - Configure CORS_ORIGIN environment variable
   - Ensure preflight OPTIONS requests are handled

### Debug Mode

Enable debug logging by setting:

```bash
LOG_LEVEL=debug
```

This will provide detailed OAuth flow information in Cloudflare Workers logs.