#!/usr/bin/env python3
"""
Launcher script for greptile-mcp that ensures proper module resolution
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Now import and run the main module
from src.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
