#!/usr/bin/env python3
"""
Debug script to understand the FastMCP structure - async version
"""
import asyncio
from src.main import mcp as greptile_mcp

async def debug_mcp():
    # Debug the MCP object structure
    print("MCP type:", type(greptile_mcp))
    print("\nMCP attributes:")
    for attr in dir(greptile_mcp):
        if not attr.startswith('__'):
            print(f"  {attr}: {type(getattr(greptile_mcp, attr))}")

    # Try to access tools
    try:
        tool_manager = greptile_mcp._tool_manager
        print("\nTool manager type:", type(tool_manager))
        print("Tool manager attributes:", dir(tool_manager))
        
        # Try accessing _tools instead of tools
        if hasattr(tool_manager, '_tools'):
            print("\n_tools found:", tool_manager._tools.keys())
        
        # Try list_tools method (async)
        tools_list = await greptile_mcp.list_tools()
        print("\nlist_tools() result:")
        print(tools_list)
        
        # Also try the tool_manager's list_tools
        if hasattr(tool_manager, 'list_tools'):
            tm_tools = await tool_manager.list_tools()
            print("\ntool_manager.list_tools() result:")
            print(tm_tools)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

# Run the async function
asyncio.run(debug_mcp())
