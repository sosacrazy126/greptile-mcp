# OAuth Authentication for Greptile MCP Server

This document describes the OAuth authentication system implemented for the Greptile MCP server running on Cloudflare Workers. The implementation provides secure, multi-tenant access control with support for multiple OAuth providers.

## Features

- **Multiple OAuth Providers**: GitHub, Google, Auth0 support
- **JWT Token Management**: Secure session handling with configurable expiration
- **User Permissions**: Role-based access control with admin and user levels  
- **Rate Limiting**: Built-in protection against abuse
- **Backward Compatibility**: Optional authentication maintains existing API compatibility
- **Multi-tenant Support**: User-scoped sessions and repository access control
- **Production Ready**: Comprehensive error handling and security best practices

## Quick Start

### 1. Enable OAuth

Set the following environment variable in your Cloudflare Workers:

```bash
OAUTH_ENABLED=true
```

### 2. Configure JWT Secret

Generate and set a secure JWT secret:

```bash
# Generate a secure secret
openssl rand -base64 32

# Set it as a Cloudflare Workers secret
wrangler secret put OAUTH_JWT_SECRET
```

### 3. Configure OAuth Provider

#### GitHub Example:

1. Create a GitHub OAuth App at https://github.com/settings/developers
2. Set the callback URL to: `https://your-worker.workers.dev/auth/callback`
3. Configure the environment variables:

```bash
wrangler secret put OAUTH_GITHUB_CLIENT_SECRET
```

Add to `wrangler.toml`:
```toml
[env.production.vars]
OAUTH_GITHUB_CLIENT_ID = "your_github_client_id"
```

### 4. Deploy

```bash
wrangler deploy --env production
```

## Authentication Flow

### 1. Login Initiation

```http
GET /auth/login?provider=github
```

Response:
```json
{
  "success": true,
  "data": {
    "auth_url": "https://github.com/login/oauth/authorize?client_id=...",
    "state": "csrf_protection_token",
    "provider": "github"
  }
}
```

### 2. OAuth Callback

After user authorizes, GitHub redirects to:
```
https://your-worker.workers.dev/auth/callback?code=...&state=...
```

### 3. Token Exchange

```http
POST /auth/callback
Content-Type: application/json

{
  "code": "oauth_authorization_code",
  "state": "csrf_protection_token",
  "provider": "github"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "token": "jwt_token_here",
    "user": {
      "id": 12345,
      "login": "username",
      "email": "user@example.com",
      "name": "User Name",
      "avatar_url": "https://...",
      "provider": "github"
    },
    "permissions": {
      "query_repository": true,
      "search_repository": true,
      "get_repository_info": true,
      "index_repository": false
    }
  }
}
```

### 4. Authenticated API Calls

```http
POST /mcp
Authorization: Bearer jwt_token_here
Content-Type: application/json

{
  "method": "query_repository",
  "params": {
    "query": "How does authentication work?",
    "repositories": [
      {
        "remote": "github",
        "repository": "owner/repo",
        "branch": "main"
      }
    ]
  }
}
```

## API Endpoints

### Authentication Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | GET | Initiate OAuth login flow |
| `/auth/callback` | POST | Handle OAuth callback |
| `/auth/logout` | POST | Logout (client-side token invalidation) |
| `/auth/user` | GET | Get current user info and permissions |

### MCP Endpoints (Enhanced)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mcp` | POST | Execute MCP tools with user context |
| `/sse` | POST | Server-sent events endpoint with auth |
| `/` | GET | Server info including OAuth status |

## User Permissions

### Default Permissions

- **query_repository**: ✅ Allowed for all authenticated users
- **search_repository**: ✅ Allowed for all authenticated users  
- **get_repository_info**: ✅ Allowed for all authenticated users
- **index_repository**: ❌ Requires admin privileges

### Admin Users

Configure admin users via environment variable:

```bash
OAUTH_ADMIN_USERS=github_username,user_id_123,another_user
```

Admin users get full permissions including repository indexing.

### Repository Access Control

Restrict access to specific repositories:

```bash
OAUTH_ALLOWED_REPOSITORIES=owner/repo1,owner/repo2,org/private-repo
```

If not set, users can access any repository they authenticate for.

## Rate Limiting

Built-in rate limiting protects the service:

- **Authenticated Users**: 100 requests/minute, 1000 requests/hour
- **Unauthenticated Users**: 10 requests/minute, 100 requests/hour

Rate limit headers are included in responses:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

## Security Features

### JWT Security

- HMAC-SHA256 signature algorithm
- Configurable expiration (default 24 hours)
- Includes user context and permissions
- Secure secret management via Cloudflare Workers secrets

### CSRF Protection

- State parameter validation in OAuth flow
- Secure random state generation
- State verification on callback

### Input Validation

- Request parameter sanitization
- Token format validation
- Provider validation
- Permission enforcement

### Secure Headers

- CORS configuration
- Content-Type enforcement
- Authorization header validation

## Configuration Reference

### Core Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OAUTH_ENABLED` | boolean | `false` | Enable OAuth authentication |
| `OAUTH_JWT_SECRET` | string | - | JWT signing secret (required if enabled) |
| `OAUTH_JWT_EXPIRATION_HOURS` | number | `24` | Token expiration time |
| `OAUTH_REQUIRE_AUTH` | boolean | `false` | Require auth for all requests |

### Provider Settings

#### GitHub

| Variable | Type | Description |
|----------|------|-------------|
| `OAUTH_GITHUB_CLIENT_ID` | string | GitHub OAuth app client ID |
| `OAUTH_GITHUB_CLIENT_SECRET` | string | GitHub OAuth app client secret |
| `OAUTH_GITHUB_REDIRECT_URI` | string | OAuth callback URL (optional) |

#### Google

| Variable | Type | Description |
|----------|------|-------------|
| `OAUTH_GOOGLE_CLIENT_ID` | string | Google OAuth client ID |
| `OAUTH_GOOGLE_CLIENT_SECRET` | string | Google OAuth client secret |
| `OAUTH_GOOGLE_REDIRECT_URI` | string | OAuth callback URL (optional) |

#### Auth0

| Variable | Type | Description |
|----------|------|-------------|
| `OAUTH_AUTH0_CLIENT_ID` | string | Auth0 application client ID |
| `OAUTH_AUTH0_CLIENT_SECRET` | string | Auth0 application client secret |
| `OAUTH_AUTH0_DOMAIN` | string | Auth0 tenant domain |
| `OAUTH_AUTH0_REDIRECT_URI` | string | OAuth callback URL (optional) |

### Permission Settings

| Variable | Type | Description |
|----------|------|-------------|
| `OAUTH_ADMIN_USERS` | string | Comma-separated admin user IDs/usernames |
| `OAUTH_ALLOWED_REPOSITORIES` | string | Comma-separated allowed repositories |

## Deployment Guide

### Development Setup

1. Copy the example environment file:
```bash
cp .dev.vars.example .dev.vars
```

2. Fill in your OAuth provider credentials in `.dev.vars`

3. Start development server:
```bash
wrangler dev
```

### Production Deployment

1. Set production secrets:
```bash
wrangler secret put OAUTH_JWT_SECRET --env production
wrangler secret put OAUTH_GITHUB_CLIENT_SECRET --env production
```

2. Configure environment in `wrangler.toml`:
```toml
[env.production.vars]
OAUTH_ENABLED = "true"
OAUTH_GITHUB_CLIENT_ID = "your_client_id"
```

3. Deploy:
```bash
wrangler deploy --env production
```

## Client Integration

### JavaScript/TypeScript Example

```typescript
class GreptileMCPClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async login(provider: 'github' | 'google' | 'auth0') {
    // Step 1: Get authorization URL
    const response = await fetch(`${this.baseUrl}/auth/login?provider=${provider}`);
    const { data } = await response.json();
    
    // Step 2: Redirect to OAuth provider
    window.location.href = data.auth_url;
  }

  async handleCallback(code: string, state: string, provider: string) {
    const response = await fetch(`${this.baseUrl}/auth/callback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, state, provider })
    });
    
    const { data } = await response.json();
    this.token = data.token;
    
    return data;
  }

  async queryRepository(query: string, repositories: any[]) {
    if (!this.token) throw new Error('Not authenticated');

    const response = await fetch(`${this.baseUrl}/mcp`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        method: 'query_repository',
        params: { query, repositories }
      })
    });

    return response.json();
  }
}
```

### Python Client Example

```python
import requests
from typing import Dict, List, Any

class GreptileMCPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token = None
    
    def login_url(self, provider: str) -> str:
        """Get OAuth login URL"""
        response = requests.get(f"{self.base_url}/auth/login", params={"provider": provider})
        data = response.json()
        return data["data"]["auth_url"]
    
    def handle_callback(self, code: str, state: str, provider: str) -> Dict[str, Any]:
        """Handle OAuth callback and store token"""
        response = requests.post(f"{self.base_url}/auth/callback", json={
            "code": code,
            "state": state,
            "provider": provider
        })
        data = response.json()
        self.token = data["data"]["token"]
        return data["data"]
    
    def query_repository(self, query: str, repositories: List[Dict[str, str]]) -> Dict[str, Any]:
        """Query repositories with authentication"""
        if not self.token:
            raise ValueError("Not authenticated")
        
        response = requests.post(f"{self.base_url}/mcp", 
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "method": "query_repository",
                "params": {"query": query, "repositories": repositories}
            }
        )
        return response.json()
```

## Monitoring and Logging

### Key Metrics to Monitor

- Authentication success/failure rates
- Token generation and validation rates
- Rate limit violations
- Permission denied events
- OAuth provider response times

### Log Levels

Configure logging level via `LOG_LEVEL` environment variable:

- `ERROR`: Only errors and critical issues
- `WARN`: Warnings and errors  
- `INFO`: General operational information (default)
- `DEBUG`: Detailed authentication flow information

### Example Log Messages

```
INFO: User github_user123 authenticated via GitHub
INFO: User github_user123 querying repositories
WARN: Rate limit exceeded for user anonymous_user
ERROR: JWT token validation failed: token expired
DEBUG: OAuth callback received for provider GitHub
```

## Troubleshooting

### Common Issues

1. **"Invalid redirect_uri" error**
   - Ensure OAuth app redirect URI matches exactly
   - Check for HTTP vs HTTPS mismatch
   - Verify no trailing slashes

2. **JWT verification fails**
   - Check `OAUTH_JWT_SECRET` is set correctly
   - Verify token hasn't expired
   - Ensure secret consistency across deployments

3. **Permission denied**
   - Check user is in `OAUTH_ADMIN_USERS` if needed
   - Verify repository in `OAUTH_ALLOWED_REPOSITORIES`
   - Check rate limiting status

4. **CORS issues**
   - Configure `CORS_ORIGIN` environment variable
   - Ensure preflight requests handled correctly

### Debug Steps

1. Enable debug logging:
```bash
LOG_LEVEL=debug
```

2. Check Cloudflare Workers logs:
```bash
wrangler tail --env production
```

3. Verify OAuth app configuration matches environment variables

4. Test authentication flow step by step

## Migration from Non-Authenticated Setup

OAuth is fully backward compatible. Existing clients will continue to work without modification.

### Gradual Migration

1. Deploy with `OAUTH_ENABLED=true` and `OAUTH_REQUIRE_AUTH=false`
2. Update clients to use OAuth when ready
3. Set `OAUTH_REQUIRE_AUTH=true` when all clients migrated
4. Monitor logs for any remaining unauthenticated requests

### Testing

Test both authenticated and unauthenticated access:

```bash
# Unauthenticated (should work if OAUTH_REQUIRE_AUTH=false)
curl -X POST https://your-worker.workers.dev/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "query_repository", "params": {...}}'

# Authenticated  
curl -X POST https://your-worker.workers.dev/mcp \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"method": "query_repository", "params": {...}}'
```

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review Cloudflare Workers logs
3. Verify OAuth provider configuration
4. Test with minimal configuration first

For detailed configuration examples, see `cloudflare/oauth_config_examples.md`.