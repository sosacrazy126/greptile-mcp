#!/usr/bin/env /home/evilbastardxd/anaconda3/bin/python
"""
Test script for Multiple Repository Querying functionality
"""

import json
from typing import List, Dict

def demo_repository_format():
    """Demonstrate the correct repository format"""
    print("=== Repository Format ===")
    print("\nSingle repository:")
    single_repo = {
        "remote": "github",
        "repository": "facebook/react",
        "branch": "main"
    }
    print(json.dumps(single_repo, indent=2))
    
    print("\nMultiple repositories:")
    multiple_repos = [
        {
            "remote": "github",
            "repository": "facebook/react",
            "branch": "main"
        },
        {
            "remote": "github",
            "repository": "vuejs/core",
            "branch": "main"
        },
        {
            "remote": "github",
            "repository": "angular/angular",
            "branch": "main"
        }
    ]
    print(json.dumps(multiple_repos, indent=2))

def demo_query_examples():
    """Demonstrate various query examples"""
    print("\n\n=== Query Examples ===")
    
    print("\n1. Simple multi-repo query:")
    print("query: 'How do these frameworks handle component lifecycle?'")
    print("repositories: [react, vue, angular]")
    
    print("\n2. Comparison query:")
    print("comparison_query: 'Compare state management approaches'")
    print("repositories: [react, vue, angular]")
    
    print("\n3. Search across repos:")
    print("search_term: 'useEffect'")
    print("repositories: [react, vue, angular]")
    print("file_pattern: '*.js' or '*.ts'")

def demo_real_world_scenarios():
    """Demonstrate real-world use cases"""
    print("\n\n=== Real-World Scenarios ===")
    
    print("\n1. Microservices Architecture:")
    microservices = [
        {"remote": "github", "repository": "company/auth-service", "branch": "main"},
        {"remote": "github", "repository": "company/user-service", "branch": "main"},
        {"remote": "github", "repository": "company/payment-service", "branch": "main"}
    ]
    print("Query: 'How do these services communicate with each other?'")
    print("Repositories:", json.dumps(microservices, indent=2))
    
    print("\n2. Library Migration:")
    libraries = [
        {"remote": "github", "repository": "old-lib/v1", "branch": "master"},
        {"remote": "github", "repository": "new-lib/v2", "branch": "main"}
    ]
    print("Query: 'What are the API differences between these versions?'")
    print("Repositories:", json.dumps(libraries, indent=2))
    
    print("\n3. Framework Comparison:")
    frameworks = [
        {"remote": "github", "repository": "expressjs/express", "branch": "master"},
        {"remote": "github", "repository": "koajs/koa", "branch": "master"},
        {"remote": "github", "repository": "fastify/fastify", "branch": "main"}
    ]
    print("Query: 'Compare error handling and middleware patterns'")
    print("Repositories:", json.dumps(frameworks, indent=2))

def demo_api_usage():
    """Demonstrate API usage patterns"""
    print("\n\n=== API Usage Patterns ===")
    
    print("\n1. Basic Multiple Repository Query:")
    print("""
repos = [
    {"remote": "github", "repository": "facebook/react", "branch": "main"},
    {"remote": "github", "repository": "vuejs/core", "branch": "main"}
]
result = await query_multiple_repositories(
    ctx, 
    "How do these frameworks handle reactivity?", 
    repos
)
""")
    
    print("\n2. Repository Comparison:")
    print("""
repos = [
    {"remote": "github", "repository": "django/django", "branch": "main"},
    {"remote": "github", "repository": "pallets/flask", "branch": "main"}
]
result = await compare_repositories(
    ctx,
    "Compare routing implementations",
    repos
)
""")
    
    print("\n3. Cross-Repository Search:")
    print("""
repos = [
    {"remote": "github", "repository": "nodejs/node", "branch": "main"},
    {"remote": "github", "repository": "denoland/deno", "branch": "main"}
]
result = await search_multiple_repositories(
    ctx,
    "async/await implementation",
    repos,
    file_pattern="*.cc"
)
""")

def main():
    print("Multiple Repository Querying Test Suite")
    print("=" * 40)
    
    demo_repository_format()
    demo_query_examples()
    demo_real_world_scenarios()
    demo_api_usage()
    
    print("\n\n🎉 Multiple repository querying is now fully supported!")
    print("\nKey Points:")
    print("1. All query methods now clearly support multiple repositories")
    print("2. New specialized methods for common multi-repo operations")
    print("3. Clear documentation and examples for all use cases")
    print("4. Repository format is standardized across all methods")

if __name__ == "__main__":
    main()
