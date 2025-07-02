"""
Durable Object implementation for persistent session management in Cloudflare Workers.

This module provides a Durable Object class that persistently stores conversation
history across worker invocations, enabling stateful session management for the
Greptile MCP server.
"""

import json
import logging
from typing import Dict, Any, List, Optional

# Cloudflare Workers Python imports
from js import Response, Headers, JSON

# Configure logging
logger = logging.getLogger(__name__)

class SessionManagerDurableObject:
    """
    Durable Object for persistent session management.
    
    This class handles persistent storage of conversation history and session data
    for the Greptile MCP server. Each session gets its own durable object instance,
    providing strong consistency and persistence across worker invocations.
    """
    
    def __init__(self, state, env):
        """
        Initialize the Durable Object.
        
        Args:
            state: Durable Object state for persistent storage
            env: Environment bindings and configuration
        """
        self.state = state
        self.env = env
        self.session_data = {}
        self.initialized = False
    
    async def fetch(self, request):
        """
        Handle HTTP requests to this Durable Object.
        
        Args:
            request: The incoming HTTP request
            
        Returns:
            Response object with the requested data or operation result
        """
        try:
            # Parse the request
            url = request.url
            method = request.method
            
            # Initialize session data if not already done
            if not self.initialized:
                await self._initialize_session()
            
            # Handle different operations
            if method == "GET":
                return await self._handle_get_request(request)
            elif method == "POST":
                return await self._handle_post_request(request)
            elif method == "DELETE":
                return await self._handle_delete_request(request)
            else:
                return Response.new(
                    JSON.stringify({"error": f"Method {method} not supported"}),
                    status=405,
                    headers=Headers.new({"Content-Type": "application/json"})
                )
                
        except Exception as e:
            logger.error(f"Error in SessionManagerDurableObject.fetch: {str(e)}")
            return Response.new(
                JSON.stringify({"error": f"Internal server error: {str(e)}"}),
                status=500,
                headers=Headers.new({"Content-Type": "application/json"})
            )
    
    async def _initialize_session(self):
        """Initialize session data from persistent storage."""
        try:
            # Load existing session data from durable storage
            stored_data = await self.state.storage.get("session_data")
            if stored_data:
                self.session_data = json.loads(stored_data) if isinstance(stored_data, str) else stored_data
            else:
                self.session_data = {
                    "messages": [],
                    "metadata": {},
                    "created_at": None,
                    "last_updated": None
                }
            
            self.initialized = True
            logger.info("Session data initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing session data: {str(e)}")
            # Initialize with empty data on error
            self.session_data = {
                "messages": [],
                "metadata": {},
                "created_at": None,
                "last_updated": None
            }
            self.initialized = True
    
    async def _handle_get_request(self, request):
        """Handle GET requests (retrieve session data)."""
        try:
            # Parse URL to determine what to retrieve
            url_parts = request.url.split('/')
            operation = url_parts[-1] if url_parts else "history"
            
            if operation == "history":
                # Return conversation history
                messages = self.session_data.get("messages", [])
                return Response.new(
                    JSON.stringify({
                        "success": True,
                        "data": messages,
                        "metadata": self.session_data.get("metadata", {})
                    }),
                    status=200,
                    headers=Headers.new({"Content-Type": "application/json"})
                )
            
            elif operation == "metadata":
                # Return session metadata
                metadata = self.session_data.get("metadata", {})
                return Response.new(
                    JSON.stringify({
                        "success": True,
                        "data": metadata
                    }),
                    status=200,
                    headers=Headers.new({"Content-Type": "application/json"})
                )
            
            else:
                return Response.new(
                    JSON.stringify({"error": f"Unknown operation: {operation}"}),
                    status=400,
                    headers=Headers.new({"Content-Type": "application/json"})
                )
                
        except Exception as e:
            logger.error(f"Error handling GET request: {str(e)}")
            return Response.new(
                JSON.stringify({"error": f"Error retrieving data: {str(e)}"}),
                status=500,
                headers=Headers.new({"Content-Type": "application/json"})
            )
    
    async def _handle_post_request(self, request):
        """Handle POST requests (update session data)."""
        try:
            # Parse request body
            body_text = await request.text()
            body = json.loads(body_text) if body_text else {}
            
            operation = body.get("operation")
            
            if operation == "append_message":
                # Append a single message to the conversation
                message = body.get("message")
                if not message:
                    return Response.new(
                        JSON.stringify({"error": "Message is required"}),
                        status=400,
                        headers=Headers.new({"Content-Type": "application/json"})
                    )
                
                await self._append_message(message)
                return Response.new(
                    JSON.stringify({"success": True, "message": "Message appended"}),
                    status=200,
                    headers=Headers.new({"Content-Type": "application/json"})
                )
            
            elif operation == "set_history":
                # Replace entire conversation history
                messages = body.get("messages", [])
                await self._set_history(messages)
                return Response.new(
                    JSON.stringify({"success": True, "message": "History updated"}),
                    status=200,
                    headers=Headers.new({"Content-Type": "application/json"})
                )
            
            elif operation == "update_metadata":
                # Update session metadata
                metadata = body.get("metadata", {})
                await self._update_metadata(metadata)
                return Response.new(
                    JSON.stringify({"success": True, "message": "Metadata updated"}),
                    status=200,
                    headers=Headers.new({"Content-Type": "application/json"})
                )
            
            else:
                return Response.new(
                    JSON.stringify({"error": f"Unknown operation: {operation}"}),
                    status=400,
                    headers=Headers.new({"Content-Type": "application/json"})
                )
                
        except Exception as e:
            logger.error(f"Error handling POST request: {str(e)}")
            return Response.new(
                JSON.stringify({"error": f"Error updating data: {str(e)}"}),
                status=500,
                headers=Headers.new({"Content-Type": "application/json"})
            )
    
    async def _handle_delete_request(self, request):
        """Handle DELETE requests (clear session data)."""
        try:
            # Clear all session data
            await self._clear_session()
            return Response.new(
                JSON.stringify({"success": True, "message": "Session cleared"}),
                status=200,
                headers=Headers.new({"Content-Type": "application/json"})
            )
            
        except Exception as e:
            logger.error(f"Error handling DELETE request: {str(e)}")
            return Response.new(
                JSON.stringify({"error": f"Error clearing session: {str(e)}"}),
                status=500,
                headers=Headers.new({"Content-Type": "application/json"})
            )
    
    async def _append_message(self, message: Dict[str, Any]):
        """Append a message to the conversation history."""
        import time
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = time.time()
        
        # Append to messages
        if "messages" not in self.session_data:
            self.session_data["messages"] = []
        
        self.session_data["messages"].append(message)
        self.session_data["last_updated"] = time.time()
        
        # Persist to durable storage
        await self.state.storage.put("session_data", json.dumps(self.session_data))
        logger.debug(f"Appended message to session, total messages: {len(self.session_data['messages'])}")
    
    async def _set_history(self, messages: List[Dict[str, Any]]):
        """Set the complete conversation history."""
        import time
        
        # Add timestamps to messages if not present
        current_time = time.time()
        for i, message in enumerate(messages):
            if "timestamp" not in message:
                message["timestamp"] = current_time + i * 0.001  # Slightly offset timestamps
        
        # Set messages and update timestamps
        self.session_data["messages"] = list(messages)
        if not self.session_data.get("created_at"):
            self.session_data["created_at"] = current_time
        self.session_data["last_updated"] = current_time
        
        # Persist to durable storage
        await self.state.storage.put("session_data", json.dumps(self.session_data))
        logger.debug(f"Set session history with {len(messages)} messages")
    
    async def _update_metadata(self, metadata: Dict[str, Any]):
        """Update session metadata."""
        import time
        
        if "metadata" not in self.session_data:
            self.session_data["metadata"] = {}
        
        self.session_data["metadata"].update(metadata)
        self.session_data["last_updated"] = time.time()
        
        # Persist to durable storage
        await self.state.storage.put("session_data", json.dumps(self.session_data))
        logger.debug("Updated session metadata")
    
    async def _clear_session(self):
        """Clear all session data."""
        import time
        
        self.session_data = {
            "messages": [],
            "metadata": {},
            "created_at": None,
            "last_updated": time.time()
        }
        
        # Persist to durable storage
        await self.state.storage.put("session_data", json.dumps(self.session_data))
        logger.info("Cleared session data")

# Export the Durable Object class for Cloudflare Workers
SessionManager = SessionManagerDurableObject