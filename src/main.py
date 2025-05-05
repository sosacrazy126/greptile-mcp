from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dotenv import load_dotenv
import asyncio
import json
import os
import logging
from typing import Dict, List, Optional, AsyncGenerator, Any, Union

from src.utils import get_greptile_client, GreptileClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create a dataclass for our application context
@dataclass
class GreptileContext:
    """Context for the Greptile MCP server."""
    greptile_client: GreptileClient  # The Greptile API client
    initialized: bool = False  # Track if initialization is complete

@asynccontextmanager
async def greptile_lifespan(server: FastMCP) -> AsyncIterator[GreptileContext]:
    """
    Manages the Greptile client lifecycle.
    
    Args:
        server: The FastMCP server instance

    Yields:
        GreptileContext: The context containing the initialized Greptile client.
    """
