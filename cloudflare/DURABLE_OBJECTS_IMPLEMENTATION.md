# Durable Objects Session Management Implementation

This document describes the implementation of persistent session management using Cloudflare Durable Objects for the Greptile MCP server.

## Overview

The implementation provides persistent conversation history that survives across worker invocations, enabling stateful sessions for the MCP server. It includes comprehensive error handling, retry logic, and fallback mechanisms.

## Architecture

### Components

1. **SessionManagerDurableObject** (`session_durable_object.py`)
   - Implements the actual Durable Object class
   - Handles persistent storage of session data
   - Provides HTTP interface for session operations

2. **DurableSessionManager** (`shared_utils.py`)
   - Client-side interface to Durable Objects
   - Implements retry logic and fallback mechanisms
   - Manages communication with Durable Object instances

3. **SessionManager Factory** (`shared_utils.py`)
   - Automatically selects appropriate session manager
   - Uses Durable Objects in Cloudflare Workers
   - Falls back to in-memory storage for local development

4. **Updated Worker** (`worker.py`)
   - Integrates session management with environment bindings
   - Passes Durable Object bindings to session manager

## File Structure

```
cloudflare/
├── session_durable_object.py      # Durable Object implementation
├── shared_utils.py                # Session management classes
├── worker.py                      # Updated worker with DO integration
├── test_session_management.py     # Comprehensive test suite
└── DURABLE_OBJECTS_IMPLEMENTATION.md
```

## Session Data Structure

Each session maintains:

```json
{
  "messages": [
    {
      "role": "user|assistant",
      "content": "message content",
      "timestamp": 1234567890.123
    }
  ],
  "metadata": {
    "custom_key": "custom_value"
  },
  "created_at": 1234567890.123,
  "last_updated": 1234567890.123
}
```

## API Operations

### GET /history
Retrieves conversation history for the session.

**Response:**
```json
{
  "success": true,
  "data": [...messages...],
  "metadata": {...}
}
```

### POST /update
Updates session data with different operations.

**Request:**
```json
{
  "operation": "append_message|set_history|update_metadata",
  "message": {...},      // for append_message
  "messages": [...],     // for set_history
  "metadata": {...}      // for update_metadata
}
```

### DELETE /clear
Clears all session data.

## Error Handling & Resilience

### Retry Logic
- Maximum 3 retry attempts with exponential backoff
- Backoff starts at 0.1 seconds, doubles each attempt
- Logs warnings for failed attempts

### Fallback Mechanisms
- In-memory fallback for critical failures
- Automatic fallback activation after all retries fail
- Graceful degradation without service interruption

### Error Scenarios Handled
1. Durable Object unavailable
2. Network timeouts
3. Serialization errors
4. Storage failures
5. Binding configuration issues

## Configuration

### wrangler.toml
```toml
# Durable Objects for session management
[[durable_objects.bindings]]
name = "SESSION_MANAGER"
class_name = "SessionManager"
script_name = "greptile-mcp-server"

# Define the Durable Object classes
[[migrations]]
tag = "v1"
new_classes = ["SessionManager"]
```

### Environment Detection
The system automatically detects the runtime environment:
- **Cloudflare Workers**: Uses Durable Objects for persistence
- **Local Development**: Uses in-memory storage with asyncio locks

## Usage Examples

### Basic Session Management
```python
# Initialize session manager (automatic environment detection)
session_manager = SessionManager(env.SESSION_MANAGER)

# Append a message
await session_manager.append_message(session_id, {
    "role": "user",
    "content": "Hello, world!"
})

# Get conversation history
history = await session_manager.get_history(session_id)

# Set complete history
await session_manager.set_history(session_id, messages)

# Clear session
await session_manager.clear_session(session_id)
```

### With Error Handling
```python
try:
    history = await session_manager.get_history(session_id)
except Exception as e:
    logger.error(f"Failed to get session history: {e}")
    # Fallback mechanism handles this automatically
    history = []
```

## Testing

Run the comprehensive test suite:

```bash
python cloudflare/test_session_management.py
```

### Test Coverage
- ✅ In-memory session manager functionality
- ✅ Session manager factory behavior
- ✅ Durable Object class structure validation
- ✅ Configuration file validation
- ✅ Error handling and edge cases

## Deployment

### Prerequisites
1. Set required secrets:
   ```bash
   wrangler secret put GREPTILE_API_KEY
   wrangler secret put GITHUB_TOKEN
   ```

2. Optional: Set base URL
   ```bash
   wrangler secret put GREPTILE_BASE_URL
   ```

### Deploy to Cloudflare Workers
```bash
# Deploy to staging
wrangler deploy --env staging

# Deploy to production
wrangler deploy --env production
```

### Verify Deployment
1. Check health endpoint: `GET https://your-worker.your-subdomain.workers.dev/health`
2. Test session persistence across multiple requests
3. Monitor logs for any Durable Object errors

## Performance Considerations

### Session Isolation
- Each session gets its own Durable Object instance
- Strong consistency within a session
- Automatic geographic distribution
- Cold start mitigation through session stickiness

### Memory Usage
- Persistent storage reduces memory pressure on workers
- In-memory fallback only used during failures
- Efficient JSON serialization for session data

### Scaling
- Automatic scaling with user demand
- No manual capacity planning required
- Built-in redundancy and failover

## Monitoring & Debugging

### Logging
- Comprehensive logging at different levels
- Structured error messages with context
- Performance metrics for operations

### Health Checks
- Built-in health endpoint
- Session operation status tracking
- Fallback mechanism monitoring

### Common Issues
1. **"SESSION_MANAGER binding not available"**
   - Check wrangler.toml configuration
   - Verify deployment includes Durable Object bindings

2. **"All retries failed"**
   - Check Durable Object logs
   - Verify network connectivity
   - Monitor fallback mechanism activation

3. **"Session data not persisting"**
   - Verify session IDs are consistent
   - Check Durable Object storage operations
   - Monitor for serialization errors

## Security Considerations

### Session Isolation
- Each session ID creates a separate Durable Object
- No cross-session data leakage
- Secure session ID generation

### Data Protection
- Session data stored in Cloudflare's secure environment
- Automatic encryption at rest
- Network encryption for all communications

### Access Control
- Session data only accessible with correct session ID
- No public endpoints for session management
- Worker-level authentication required

## Future Enhancements

### Potential Improvements
1. **Session Expiration**: Automatic cleanup of old sessions
2. **Session Sharing**: Multi-user session support
3. **Backup & Recovery**: Cross-region session replication
4. **Analytics**: Session usage tracking and reporting
5. **Compression**: Optimize storage for large conversations

### Migration Path
The current implementation provides a solid foundation for future enhancements while maintaining backward compatibility.

---

## Summary

This implementation provides:
- ✅ Persistent session management across worker invocations
- ✅ Robust error handling with fallback mechanisms
- ✅ Automatic environment detection and configuration
- ✅ Comprehensive testing and validation
- ✅ Production-ready deployment configuration
- ✅ Detailed documentation and examples

The system is now ready for production deployment with Cloudflare Workers and provides a reliable foundation for stateful MCP server operations.