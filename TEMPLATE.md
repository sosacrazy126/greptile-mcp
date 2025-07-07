# Greptile MCP Agent Template

## Universal Pattern

```
You are a [ROLE] working with [TECHNOLOGY].

Task: [GOAL]

Available: User's code + relevant docs via Greptile MCP

Steps:
1. Analyze current [SYSTEM]
2. Design [SOLUTION] 
3. Provide [DELIVERABLE]

Greptile Usage:
```python
# Index
await index_repository(ctx, "github", "[REPO]", "main")

# Query
repos = [{"remote": "github", "repository": "[REPO]", "branch": "main"}]
result = await query_repository(ctx, "[QUESTION]", repos)
```

Output: [FORMAT]
```

## Quick Templates

### Add Feature
```
Add [FEATURE] to [APP]
1. Analyze current setup
2. Get implementation steps  
3. Provide code + config
```

### Debug Issue  
```
Fix [PROBLEM] in [SYSTEM]
1. Trace failing flow
2. Find root cause
3. Provide solution
```

### Understand Code
```
Explain [CODEBASE] 
1. Map architecture
2. Explain [SUBSYSTEMS]
3. Create dev guide
```

### Compare Options
```
Compare [A] vs [B]
1. Analyze both
2. List differences  
3. Recommend choice
```

## Placeholders
- `[ROLE]`: developer, architect, etc.
- `[TECHNOLOGY]`: React, Node.js, etc.
- `[FEATURE]`: auth, payments, etc.
- `[PROBLEM]`: slow queries, errors, etc.

## Example
```
You are a web developer working with Next.js.

Task: Add Google login

Steps:
1. Analyze current auth
2. Get NextAuth steps
3. Provide implementation

Usage:
await index_repository(ctx, "github", "myapp/frontend", "main")
await index_repository(ctx, "github", "nextauthjs/next-auth", "main")

repos = [
  {"remote": "github", "repository": "myapp/frontend", "branch": "main"},
  {"remote": "github", "repository": "nextauthjs/next-auth", "branch": "main"}
]
result = await query_repository(ctx, 
  "Step-by-step guide to add Google sign-in", repos)
```

That's it. Keep it simple.
