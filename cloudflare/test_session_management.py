#!/usr/bin/env python3
"""
Test script for session management implementation.

This script tests both the in-memory session manager (for local development)
and validates the structure of the Durable Objects implementation.
"""

import asyncio
import json
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cloudflare.shared_utils import InMemorySessionManager, SessionManager

async def test_in_memory_session_manager():
    """Test the in-memory session manager implementation."""
    print("Testing InMemorySessionManager...")
    
    manager = InMemorySessionManager()
    session_id = "test-session-123"
    
    # Test 1: Get empty history
    history = await manager.get_history(session_id)
    assert history == [], f"Expected empty history, got {history}"
    print("✓ Empty history test passed")
    
    # Test 2: Append message
    message1 = {"role": "user", "content": "Hello, world!"}
    await manager.append_message(session_id, message1)
    
    history = await manager.get_history(session_id)
    assert len(history) == 1, f"Expected 1 message, got {len(history)}"
    assert history[0] == message1, f"Expected {message1}, got {history[0]}"
    print("✓ Append message test passed")
    
    # Test 3: Append another message
    message2 = {"role": "assistant", "content": "Hello! How can I help you?"}
    await manager.append_message(session_id, message2)
    
    history = await manager.get_history(session_id)
    assert len(history) == 2, f"Expected 2 messages, got {len(history)}"
    assert history[1] == message2, f"Expected {message2}, got {history[1]}"
    print("✓ Multiple message append test passed")
    
    # Test 4: Set complete history
    new_history = [
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": "Python is a programming language."},
        {"role": "user", "content": "Thanks!"}
    ]
    await manager.set_history(session_id, new_history)
    
    history = await manager.get_history(session_id)
    assert len(history) == 3, f"Expected 3 messages, got {len(history)}"
    assert history == new_history, f"Expected {new_history}, got {history}"
    print("✓ Set history test passed")
    
    # Test 5: Clear session
    await manager.clear_session(session_id)
    history = await manager.get_history(session_id)
    assert history == [], f"Expected empty history after clear, got {history}"
    print("✓ Clear session test passed")
    
    # Test 6: Multiple sessions
    session_a = "session-a"
    session_b = "session-b"
    
    await manager.append_message(session_a, {"role": "user", "content": "Message A"})
    await manager.append_message(session_b, {"role": "user", "content": "Message B"})
    
    history_a = await manager.get_history(session_a)
    history_b = await manager.get_history(session_b)
    
    assert len(history_a) == 1, f"Expected 1 message in session A, got {len(history_a)}"
    assert len(history_b) == 1, f"Expected 1 message in session B, got {len(history_b)}"
    assert history_a[0]["content"] == "Message A", f"Expected 'Message A', got {history_a[0]['content']}"
    assert history_b[0]["content"] == "Message B", f"Expected 'Message B', got {history_b[0]['content']}"
    print("✓ Multiple sessions test passed")
    
    print("All InMemorySessionManager tests passed! ✓")

async def test_session_manager_factory():
    """Test the SessionManager factory."""
    print("\nTesting SessionManager factory...")
    
    # Test without Cloudflare environment (should use in-memory)
    manager = SessionManager()
    assert isinstance(manager._manager, InMemorySessionManager), "Expected InMemorySessionManager"
    print("✓ SessionManager defaults to InMemorySessionManager")
    
    # Test basic functionality through the factory
    session_id = "factory-test-session"
    message = {"role": "user", "content": "Factory test message"}
    
    await manager.append_message(session_id, message)
    history = await manager.get_history(session_id)
    
    assert len(history) == 1, f"Expected 1 message, got {len(history)}"
    assert history[0] == message, f"Expected {message}, got {history[0]}"
    print("✓ SessionManager factory functionality test passed")
    
    print("All SessionManager factory tests passed! ✓")

def validate_durable_object_structure():
    """Validate the structure of the Durable Object implementation."""
    print("\nValidating Durable Object structure...")
    
    try:
        # Check if the file exists and can be read
        import os
        do_file_path = os.path.join(os.path.dirname(__file__), 'session_durable_object.py')
        
        if not os.path.exists(do_file_path):
            print("✗ session_durable_object.py file not found")
            return False
        
        with open(do_file_path, 'r') as f:
            content = f.read()
        
        # Check for required class and methods in the source code
        required_elements = [
            'class SessionManagerDurableObject',
            'def __init__(self, state, env)',
            'async def fetch(self, request)',
            'async def _initialize_session(self)',
            'async def _handle_get_request(self, request)',
            'async def _handle_post_request(self, request)',
            'async def _handle_delete_request(self, request)',
            'async def _append_message(self, message',
            'async def _set_history(self, messages',
            'async def _clear_session(self)',
            'SessionManager = SessionManagerDurableObject'
        ]
        
        for element in required_elements:
            if element not in content:
                print(f"✗ Missing required element: {element}")
                return False
        
        print("✓ Durable Object class structure is valid")
        print("✓ Durable Object export alias is correct")
        
        # Check for proper error handling
        error_handling_elements = [
            'try:',
            'except Exception as e:',
            'logger.error',
            'Response.new'
        ]
        
        for element in error_handling_elements:
            if element not in content:
                print(f"✗ Missing error handling element: {element}")
                return False
        
        print("✓ Durable Object error handling is present")
        
        # Check for proper JSON handling
        json_elements = [
            'json.loads',
            'json.dumps',
            'JSON.stringify'
        ]
        
        json_count = sum(1 for element in json_elements if element in content)
        if json_count < 2:
            print("✗ Insufficient JSON handling")
            return False
        
        print("✓ Durable Object JSON handling is present")
        
        print("All Durable Object structure validations passed! ✓")
        print("Note: Runtime validation skipped (requires Cloudflare Workers environment)")
        
    except Exception as e:
        print(f"✗ Error validating Durable Object structure: {e}")
        return False
    
    return True

def validate_wrangler_config():
    """Validate the wrangler.toml configuration."""
    print("\nValidating wrangler.toml configuration...")
    
    try:
        # Read wrangler.toml
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'wrangler.toml')
        
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        # Check for required sections
        required_sections = [
            'durable_objects.bindings',
            'SESSION_MANAGER',
            'SessionManager',
            'migrations'
        ]
        
        for section in required_sections:
            assert section in config_content, f"Missing section in wrangler.toml: {section}"
        
        print("✓ wrangler.toml contains required Durable Object configuration")
        
        # Check specific configuration values
        assert 'name = "SESSION_MANAGER"' in config_content, "Missing SESSION_MANAGER binding name"
        assert 'class_name = "SessionManager"' in config_content, "Missing SessionManager class name"
        assert 'new_classes = ["SessionManager"]' in config_content, "Missing SessionManager in migrations"
        
        print("✓ wrangler.toml configuration values are correct")
        print("All wrangler.toml validations passed! ✓")
        
    except FileNotFoundError:
        print("✗ wrangler.toml not found")
        return False
    except Exception as e:
        print(f"✗ Error validating wrangler.toml: {e}")
        return False
    
    return True

async def main():
    """Run all tests."""
    print("Running Greptile MCP Server Session Management Tests")
    print("=" * 60)
    
    try:
        # Test in-memory session manager
        await test_in_memory_session_manager()
        
        # Test session manager factory
        await test_session_manager_factory()
        
        # Validate Durable Object structure
        durable_object_valid = validate_durable_object_structure()
        
        # Validate wrangler configuration
        wrangler_valid = validate_wrangler_config()
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY:")
        print("✓ InMemorySessionManager: PASSED")
        print("✓ SessionManager Factory: PASSED")
        print(f"{'✓' if durable_object_valid else '✗'} Durable Object Structure: {'PASSED' if durable_object_valid else 'FAILED'}")
        print(f"{'✓' if wrangler_valid else '✗'} Wrangler Configuration: {'PASSED' if wrangler_valid else 'FAILED'}")
        
        if durable_object_valid and wrangler_valid:
            print("\n🎉 All tests passed! The Durable Objects session management implementation is ready.")
            print("\nTo deploy:")
            print("1. Set your secrets: wrangler secret put GREPTILE_API_KEY")
            print("2. Set your secrets: wrangler secret put GITHUB_TOKEN")
            print("3. Deploy: wrangler deploy")
        else:
            print("\n❌ Some tests failed. Please check the implementation.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)