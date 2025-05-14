#!/usr/bin/env python3
"""
Debug tool info structure
"""
from src.main import mcp as greptile_mcp

# Get tool info
tools = greptile_mcp._tool_manager._tools
for name, tool_info in tools.items():
    print(f"\nTool: {name}")
    print(f"  Type: {type(tool_info)}")
    print(f"  Attributes: {dir(tool_info)}")
    if hasattr(tool_info, 'func'):
        print(f"  Function: {tool_info.func}")
    break  # Just check the first one
