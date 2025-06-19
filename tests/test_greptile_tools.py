#!/usr/bin/env python3
"""
Interactive test for greptile-mcp tools
"""
import asyncio
import sys
import os
from pathlib import Path

# Set up the path
sys.path.insert(0, '/home/evilbastardxd/Desktop/tools/grep-mcp')
os.environ['GREPTILE_API_KEY'] = 'YOUR_GREPTILE_API_KEY'
os.environ['GITHUB_TOKEN'] = 'YOUR_GITHUB_TOKEN'

from src.main import mcp as greptile_mcp, greptile_lifespan

async def test_greptile_tools():
    """Test the greptile-mcp tools interactively"""
    
    print("=== Greptile MCP Tools Test ===\n")
    
    # Create context
    async with greptile_lifespan(greptile_mcp) as context:
        # Create a mock context for tools
        class MockContext:
            def __init__(self, lifespan_context):
                self.request_context = type('RequestContext', (), {
                    'lifespan_context': lifespan_context
                })()
        
        ctx = MockContext(context)
        
        print("1. Testing greptile_help tool...")
        print("-" * 40)
        
        # Get help
        help_tool = greptile_mcp._tool_manager._tools['greptile_help']
        help_result = await help_tool.fn(ctx)
        print(help_result[:500] + "...\n")
        
        print("2. Testing get_repository_info tool...")
        print("-" * 40)
        
        # Get repo info
        info_tool = greptile_mcp._tool_manager._tools['get_repository_info']
        try:
            info_result = await info_tool.fn(
                ctx,
                remote="github",
                repository="facebook/react",
                branch="main"
            )
            print(f"Repository info:\n{info_result}\n")
        except Exception as e:
            print(f"Error: {e}\n")
        
        print("3. Available tools:")
        print("-" * 40)
        
        # List all tools
        for tool_name, tool in greptile_mcp._tool_manager._tools.items():
            print(f"- {tool_name}: {tool.description.split('.')[0]}")
        
        print("\n✓ All tests completed!")
        print("\nThese tools are now available in Claude Desktop.")
        print("Restart Claude Desktop to use them.")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_greptile_tools())
