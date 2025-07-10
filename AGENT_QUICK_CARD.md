# 🚀 Greptile MCP - Agent Quick Card

## What is this?
AI-powered code search and analysis across multiple repositories. Ask questions in natural language, get answers with code references.

## First Time? Start Here:
```python
# 1. Get complete guide
await greptile_help(ctx)

# 2. See real examples
# Check OBJECTIVES_GUIDE.md
```

## Basic Flow (3 steps):
```python
# 1. Index repository
await index_repository(ctx, "github", "facebook/react", "main")

# 2. Create repo list
repos = [{"remote": "github", "repository": "facebook/react", "branch": "main"}]

# 3. Ask question
result = await query_simple(ctx, "How does useState work?", repos)
```

## Common Tasks:

### Understand Code
```python
await query_repository(ctx, "Explain the authentication flow", repos)
```

### Add Features  
```python
await query_repository(ctx, "How do I add Google Sign-in?", repos)
```

### Compare Implementations
```python
await compare_repositories(ctx, "Compare error handling", [repo1, repo2])
```

### Find Patterns
```python
await search_repository(ctx, "WebSocket usage", repos)
```

## Repository Format (IMPORTANT!)
```json
{
    "remote": "github",
    "repository": "owner/repo",  // NOT just "repo"
    "branch": "main"
}
```

## Key Tools:
- `greptile_help()` - Full documentation
- `index_repository()` - Make repo searchable
- `query_simple()` - Quick questions  
- `query_repository()` - Full analysis
- `compare_repositories()` - Compare code
- `search_repository()` - Find patterns

## Common Mistakes:
❌ Wrong: "https://github.com/owner/repo"
✅ Right: "owner/repo"

❌ Wrong: Query without indexing
✅ Right: Index first, then query

## Real Example:
```python
# Add auth to your app
await index_repository(ctx, "github", "myapp/backend", "main")
await index_repository(ctx, "github", "nextauthjs/next-auth", "main")

repos = [
    {"remote": "github", "repository": "myapp/backend", "branch": "main"},
    {"remote": "github", "repository": "nextauthjs/next-auth", "branch": "main"}
]

result = await query_repository(ctx, 
    "How do I add Google Sign-in to my app?", 
    repos
)
```

Remember: Always index before querying!
