#!/usr/bin/env python3
"""
Debug script to check why the default session ID isn't being used.
"""
import asyncio
from dataclasses import dataclass
from typing import Optional

# Mock the components to test the logic
@dataclass
class MockGreptileContext:
    default_session_id: str = "7dc8f451-9bf7-4262-a664-0865ac578e6c"

def test_session_logic():
    """Test the session ID logic in isolation."""
    print("Testing Session ID Logic")
    print("=" * 40)
    
    # Create mock context
    greptile_context = MockGreptileContext()
    print(f"Default session ID: {greptile_context.default_session_id}")
    print()
    
    # Test cases
    test_cases = [
        ("No session_id provided", None),
        ("Empty string", ""),
        ("Explicit session_id", "custom-session-123"),
    ]
    
    for description, session_id in test_cases:
        # This mirrors the logic in query_repository
        sid = session_id or greptile_context.default_session_id
        print(f"{description}: session_id={session_id}")
        print(f"  Result: sid={sid}")
        print()
    
    # Check edge cases
    print("Edge Cases:")
    print("-" * 20)
    
    # What if default_session_id is None? (shouldn't happen but...)
    broken_context = MockGreptileContext(default_session_id=None)
    session_id = None
    sid = session_id or broken_context.default_session_id
    print(f"Broken context (None default): sid={sid}")
    
    # What if default_session_id is empty string?
    empty_context = MockGreptileContext(default_session_id="")
    session_id = None
    sid = session_id or empty_context.default_session_id
    print(f"Empty default: sid={sid}")


if __name__ == "__main__":
    print("Session ID Default Logic Test")
    print()
    
    test_session_logic()
    
    print("\nNote: If the server is running, you need to restart it")
    print("for the hardcoded default session ID to take effect.")
    print("\nExpected behavior after restart:")
    print("- All queries without session_id should use: 7dc8f451-9bf7-4262-a664-0865ac578e6c")
    print("- Queries with explicit session_id should use the provided value")
