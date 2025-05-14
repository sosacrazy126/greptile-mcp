# 🚀 Greptile MCP Template Quick Guide

## Core Template Structure

```
You are a [ROLE] specializing in [DOMAIN].

You have access to:
1. [CODEBASE_TYPE] via Greptile MCP ([CODEBASE_REF])
2. [DOCUMENTATION_TYPE] via Greptile MCP ([DOC_REF])

Task: [SPECIFIC_GOAL]

**Phase 1: Analysis**
- Examine [CODEBASE_REF] for [ANALYSIS_FOCUS]
- Identify [KEY_ELEMENTS]
- Map [RELATIONSHIPS/FLOWS]

**Phase 2: Solution Development**
- Based on analysis of [CODEBASE_REF]
- Using patterns from [DOC_REF]
- Create [DELIVERABLE_TYPE]

**Phase 3: Implementation**
- Provide [OUTPUT_FORMAT]
- Include [REQUIRED_ELEMENTS]
- Address [SPECIFIC_CONCERNS]

**Greptile MCP Workflow:**
```python
# 1. Index repositories
await index_repository(ctx, "[REMOTE]", "[REPO]", "[BRANCH]")

# 2. Analyze current state
repos = [{"remote": "[REMOTE]", "repository": "[REPO]", "branch": "[BRANCH]"}]
analysis = await query_repository(ctx, "[ANALYSIS_QUERY]", repos)

# 3. Get solution
solution = await query_repository(ctx, "[SOLUTION_QUERY]", repos)
```

**Output Requirements:**
1. [SECTION_1]: [DESCRIPTION]
2. [SECTION_2]: [DESCRIPTION]
3. [SECTION_3]: [DESCRIPTION]
```

## Quick Templates

### 1. Feature Addition
```
Task: Add [FEATURE] to [APPLICATION]

Phase 1: Analyze current [RELATED_SYSTEM]
Phase 2: Design [FEATURE] integration
Phase 3: Provide implementation steps

Greptile queries:
- "How does [RELATED_SYSTEM] currently work?"
- "Best practices for implementing [FEATURE]"
- "Step-by-step guide to add [FEATURE]"
```

### 2. Debug Issue
```
Task: Diagnose and fix [ISSUE_DESCRIPTION]

Phase 1: Trace [AFFECTED_FLOW]
Phase 2: Identify failure points
Phase 3: Provide fix strategy

Greptile queries:
- "Trace [PROCESS] flow where [ISSUE] occurs"
- "Common causes of [ISSUE_PATTERN]"
- "How to fix [SPECIFIC_PROBLEM]"
```

### 3. Code Understanding
```
Task: Understand [CODEBASE] for [PURPOSE]

Phase 1: Map architecture
Phase 2: Deep dive [FOCUS_AREAS]
Phase 3: Create guide for [AUDIENCE]

Greptile queries:
- "Explain architecture of [SYSTEM]"
- "How does [SUBSYSTEM] work?"
- "Developer guide for [TASKS]"
```

### 4. System Comparison
```
Task: Compare [SYSTEM_A] vs [SYSTEM_B]

Phase 1: Analyze both implementations
Phase 2: Compare [ASPECTS]
Phase 3: Provide recommendations

Greptile queries:
- "How does [SYSTEM_A] handle [FEATURE]?"
- "Compare [ASPECT] between systems"
- "Which approach is better for [USE_CASE]?"
```

### 5. Performance Analysis
```
Task: Optimize [PERFORMANCE_ASPECT]

Phase 1: Identify bottlenecks
Phase 2: Find optimization opportunities  
Phase 3: Create optimization plan

Greptile queries:
- "Analyze [PERFORMANCE_METRIC] patterns"
- "Find inefficient [OPERATIONS]"
- "Optimization strategy for [AREA]"
```

## Variable Placeholders

**Roles:**
- `[ROLE]`: developer, architect, security expert, performance engineer
- `[DOMAIN]`: web apps, APIs, mobile, distributed systems, ML

**Codebases:**
- `[CODEBASE_TYPE]`: application code, library source, framework internals
- `[REMOTE]`: github, gitlab, bitbucket
- `[BRANCH]`: main, master, develop, feature/x

**Tasks:**
- `[FEATURE]`: authentication, payments, notifications, search
- `[ISSUE]`: memory leak, slow queries, auth failures, race conditions
- `[SYSTEM]`: database layer, API gateway, state management, routing

**Outputs:**
- `[OUTPUT_FORMAT]`: step-by-step guide, code snippets, architecture diagram
- `[DELIVERABLE]`: implementation plan, debug strategy, migration guide

## Best Practices

1. **Start Broad**: Begin with architecture/overview queries
2. **Get Specific**: Drill down into exact implementations
3. **Cross-Reference**: Query multiple repos for context
4. **Iterate**: Refine queries based on responses
5. **Validate**: Test proposed solutions against codebase

## Example: Add Google Auth

```
You are a web developer specializing in authentication.

You have access to:
1. User's Next.js app via Greptile MCP
2. NextAuth.js documentation via Greptile MCP

Task: Add Google Sign-in to the application

**Phase 1: Analysis**
```python
# Index repos
await index_repository(ctx, "github", "user/app", "main")
await index_repository(ctx, "github", "nextauthjs/next-auth", "main")

# Analyze current auth
repos = [{"remote": "github", "repository": "user/app", "branch": "main"}]
current_auth = await query_repository(ctx, 
    "How is authentication currently implemented?", repos)
```

**Phase 2: Solution Development**
```python
# Get implementation guide
all_repos = [
    {"remote": "github", "repository": "user/app", "branch": "main"},
    {"remote": "github", "repository": "nextauthjs/next-auth", "branch": "main"}
]
guide = await query_repository(ctx,
    "Step-by-step guide to add Google Sign-in with NextAuth", all_repos)
```

**Phase 3: Implementation**
Provide:
1. Required packages to install
2. Configuration code with file paths
3. Environment variables needed
4. UI integration steps
5. Testing instructions
```

## Template Chaining

Combine templates for complex tasks:

1. **Understand** → **Implement** → **Test**
2. **Debug** → **Fix** → **Prevent**
3. **Analyze** → **Compare** → **Decide**
4. **Audit** → **Optimize** → **Monitor**

Each phase can use a different template pattern!
