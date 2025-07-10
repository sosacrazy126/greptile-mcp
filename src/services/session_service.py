"""
Session management service for handling conversation context.
"""

import json
import uuid
from typing import List, Dict, Any, Optional, Union
from src.utils import SessionManager, generate_session_id


class SessionService:
    """Service for managing conversation sessions and message formatting."""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
    
    def generate_session_id(self) -> str:
        """Generate a new unique session ID."""
        return generate_session_id()
    
    def format_messages_for_api(
        self, 
        messages: List[Union[Dict[str, Any], str]], 
        current_query: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Format messages to match the Greptile API specification.

        Args:
            messages: List of messages in various formats
            current_query: Optional current query to append

        Returns:
            List of properly formatted messages with id, content, and role
        """
        formatted_messages = []

        for idx, msg in enumerate(messages):
            if isinstance(msg, dict):
                # Ensure proper format
                formatted_msg = {
                    "id": msg.get("id", f"msg_{idx}"),
                    "content": msg.get("content", ""),
                    "role": msg.get("role", "user")
                }
                formatted_messages.append(formatted_msg)
            else:
                # Handle string messages
                formatted_messages.append({
                    "id": f"msg_{idx}",
                    "content": str(msg),
                    "role": "user"
                })

        # Add current query if provided
        if current_query:
            formatted_messages.append({
                "id": f"msg_{len(formatted_messages)}",
                "content": current_query,
                "role": "user"
            })

        return formatted_messages
    
    async def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        return await self.session_manager.get_history(session_id)
    
    async def add_message_to_session(
        self, 
        session_id: str, 
        message: Dict[str, Any]
    ) -> None:
        """Add a message to session history."""
        await self.session_manager.append_message(session_id, message)
    
    async def update_session_history(
        self, 
        session_id: str, 
        messages: List[Dict[str, Any]]
    ) -> None:
        """Update the complete session history."""
        await self.session_manager.set_history(session_id, messages)
    
    async def clear_session(self, session_id: str) -> None:
        """Clear a session's conversation history."""
        await self.session_manager.clear_session(session_id)
    
    def add_session_metadata(self, response_data: Dict[str, Any], session_id: str) -> str:
        """Add session metadata to response and return as JSON string."""
        if isinstance(response_data, dict):
            response_data["_session_id"] = session_id
        return json.dumps(response_data, indent=2)