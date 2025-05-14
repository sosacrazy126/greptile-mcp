#!/usr/bin/env /home/evilbastardxd/anaconda3/bin/python
"""
Test script for Full Message History Support feature - standalone version
"""

import json
from typing import List, Dict, Union

def format_messages_for_api(messages: List[Union[Dict, str]], current_query: str = None) -> List[Dict[str, str]]:
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

def test_format_messages_for_api():
    """Test the message formatting function"""
    
    print("Testing format_messages_for_api function...")
    
    # Test 1: Mixed format messages
    test_messages = [
        {"content": "Hello", "role": "user"},  # Missing id
        {"id": "msg_1", "content": "World", "role": "assistant"},  # Complete
        "Plain string message",  # String format
        {"id": "msg_3", "content": "Test", "role": "user", "extra": "field"}  # Extra field
    ]
    
    formatted = format_messages_for_api(test_messages)
    
    print("\nTest 1 - Mixed format messages:")
    print("Input:", json.dumps(test_messages, indent=2))
    print("Output:", json.dumps(formatted, indent=2))
    
    # Verify formatting
    assert len(formatted) == 4
    assert formatted[0]["id"] == "msg_0"  # Auto-generated id
    assert formatted[1]["id"] == "msg_1"  # Preserved id
    assert formatted[2]["id"] == "msg_2"  # Auto-generated for string
    assert formatted[2]["content"] == "Plain string message"
    assert formatted[2]["role"] == "user"  # Default role
    assert "extra" not in formatted[3]  # Extra field removed
    
    # Test 2: With current query
    test_messages_2 = [
        {"id": "msg_0", "content": "Previous message", "role": "user"},
        {"id": "msg_1", "content": "Previous response", "role": "assistant"}
    ]
    current_query = "New query"
    
    formatted_with_query = format_messages_for_api(test_messages_2, current_query)
    
    print("\nTest 2 - With current query:")
    print("Input messages:", json.dumps(test_messages_2, indent=2))
    print("Current query:", current_query)
    print("Output:", json.dumps(formatted_with_query, indent=2))
    
    assert len(formatted_with_query) == 3
    assert formatted_with_query[2]["content"] == "New query"
    assert formatted_with_query[2]["role"] == "user"
    assert formatted_with_query[2]["id"] == "msg_2"
    
    # Test 3: Empty messages
    empty_messages = []
    formatted_empty = format_messages_for_api(empty_messages, "Only query")
    
    print("\nTest 3 - Empty messages with query:")
    print("Input messages:", empty_messages)
    print("Current query: Only query")
    print("Output:", json.dumps(formatted_empty, indent=2))
    
    assert len(formatted_empty) == 1
    assert formatted_empty[0]["content"] == "Only query"
    
    print("\n✅ All tests passed!")

def test_message_structure():
    """Test the expected message structure for Greptile API"""
    
    print("\n\nTesting Greptile API message structure...")
    
    # Expected format for Greptile API
    greptile_messages = [
        {
            "id": "msg_0",
            "content": "What is the authentication system in this codebase?",
            "role": "user"
        },
        {
            "id": "msg_1", 
            "content": "The authentication system uses JWT tokens...",
            "role": "assistant"
        },
        {
            "id": "msg_2",
            "content": "How does it handle refresh tokens?",
            "role": "user"
        }
    ]
    
    print("Greptile API expected format:")
    print(json.dumps(greptile_messages, indent=2))
    
    # Test that our format matches
    our_messages = [
        {"content": "What is the authentication system in this codebase?"},
        {"id": "msg_1", "content": "The authentication system uses JWT tokens...", "role": "assistant"}
    ]
    
    formatted = format_messages_for_api(our_messages, "How does it handle refresh tokens?")
    
    print("\nOur formatted output:")
    print(json.dumps(formatted, indent=2))
    
    # Verify structure matches
    for msg in formatted:
        assert "id" in msg
        assert "content" in msg
        assert "role" in msg
        assert len(msg) == 3  # Only these three fields
    
    print("✅ Message structure matches Greptile API requirements!")

def demonstrate_api_usage():
    """Demonstrate the three different ways to use the API"""
    
    print("\n\n=== API Usage Demonstration ===")
    
    print("\n1. Simple Query (query_simple):")
    print("   - Single query, no history")
    print("   - Best for: One-off questions")
    print("   Example:")
    print("   await query_simple(ctx, 'What is the main function?', repositories)")
    
    print("\n2. Standard Query (query_repository):")
    print("   - Supports conversation history with backward compatibility")
    print("   - Best for: Most use cases, maintains session")
    print("   Example:")
    simple_messages = [
        {"content": "Previous question", "role": "user"},
        {"content": "Previous answer", "role": "assistant"}
    ]
    print(f"   await query_repository(ctx, 'Follow-up question', repositories, messages={simple_messages})")
    
    print("\n3. Advanced Query (query_repository_advanced):")
    print("   - Full Greptile API format with message IDs")
    print("   - Best for: Complex conversations, full API control")
    print("   Example:")
    advanced_messages = [
        {"id": "msg_0", "content": "Question 1", "role": "user"},
        {"id": "msg_1", "content": "Answer 1", "role": "assistant"},
        {"id": "msg_2", "content": "Question 2", "role": "user"}
    ]
    print(f"   await query_repository_advanced(ctx, messages={json.dumps(advanced_messages, indent=6)}, repositories)")

if __name__ == "__main__":
    test_format_messages_for_api()
    test_message_structure()
    demonstrate_api_usage()
    print("\n🎉 All tests completed successfully!")
