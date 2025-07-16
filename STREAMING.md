# Greptile MCP Streaming Implementation

This document explains the enhanced streaming capabilities in the Greptile MCP server.

## Overview

The Greptile MCP server now supports **real-time streaming** with Server-Sent Events (SSE), providing:
- **Live text chunks** as they're generated
- **Real-time citations** with file locations and line numbers
- **Session management** for conversational continuity
- **Performance metadata** for monitoring and optimization

## What's Special About Streaming

### 🌊 **Real-Time Response Building**
Instead of waiting 10-20 seconds for a complete response, users see content as it's generated:
```
User: "Explain this codebase"
Stream: "This repository..." 
Stream: "contains a Node.js..." 
Stream: "application that handles..."
Stream: "user authentication and..."
```

### 🎯 **Better User Experience**
- **Perceived Performance**: Users see progress immediately
- **Engagement**: Keeps users engaged during long-running queries
- **Interruptible**: Can be cancelled if needed
- **Progressive**: Shows partial results even if request fails

### 🔧 **Technical Benefits**
- **Lower Memory**: Process chunks as they arrive
- **Timeout Handling**: Detect stalled requests quickly
- **Citation Tracking**: Real-time file and line number references
- **Session Continuity**: Maintain conversation context

## API Changes

### Enhanced `query_repository` Tool

The `query_repository` tool now supports streaming with enhanced metadata:

```python
# Enable streaming
result = await query_repository(
    query="What is this repository about?",
    repositories='[{"remote": "github", "repository": "owner/repo", "branch": "main"}]',
    stream=True,  # Enable streaming
    genius=True,
    session_id="conversation-123"
)
```

### Response Structure

#### Streaming Response (`stream=True`)
```json
{
  "message": "Complete assembled message from all chunks",
  "session_id": "conversation-123",
  "sources": [
    {
      "file": "src/main.py",
      "lines": "45-67",
      "timestamp": 1672531200.123
    }
  ],
  "streamed": true,
  "streaming_metadata": {
    "text_chunks": 24,
    "citations_received": 3,
    "duration": 12.45,
    "time_to_first_chunk": 1.23,
    "started_at": 1672531200.000,
    "completed_at": 1672531212.450,
    "session_id": "conversation-123"
  }
}
```

#### Non-Streaming Response (`stream=False`)
```json
{
  "message": "Complete response message",
  "session_id": "conversation-123",
  "sources": [
    {
      "file": "src/main.py",
      "lines": "45-67"
    }
  ],
  "streamed": false
}
```

## Implementation Details

### Server-Sent Events (SSE) Processing

The streaming implementation processes SSE chunks in real-time:

```python
# Internal streaming flow
async for chunk in client.stream_query_repositories(...):
    chunk_type = chunk.get("type")
    
    if chunk_type == "text":
        # Process text content immediately
        content = chunk.get("content", "")
        message_parts.append(content)
        
    elif chunk_type == "citation":
        # Process citations as they arrive
        citation = {
            "file": chunk.get("file"),
            "lines": chunk.get("lines"),
            "timestamp": chunk.get("timestamp")
        }
        citations.append(citation)
        
    elif chunk_type == "session":
        # Update session information
        session_id = chunk.get("sessionId")
```

### Structured Chunk Types

The streaming implementation recognizes several chunk types:

1. **Text Chunks**: `type: "text"`
   - Contains `content` field with text
   - Assembled into final message
   - Timestamped for performance tracking

2. **Citation Chunks**: `type: "citation"`
   - Contains `file` and `lines` fields
   - Added to sources array
   - Timestamped for tracking

3. **Session Chunks**: `type: "session"`
   - Contains `sessionId` field
   - Updates session tracking
   - Enables conversation continuity

4. **Other Chunks**: `type: "other"`
   - Forwards additional metadata
   - Preserves unknown chunk types

### Performance Tracking

Streaming includes comprehensive performance metadata:

- **Duration**: Total streaming time
- **Time to First Chunk**: Latency before first response
- **Chunk Counts**: Text chunks and citations received
- **Timestamps**: Start, completion, and first chunk times

## Usage Examples

### Basic Streaming Query

```python
import json
from your_mcp_client import query_repository

# Enable streaming for better UX
result = await query_repository(
    query="How does authentication work in this codebase?",
    repositories='[{"remote": "github", "repository": "myorg/myapp", "branch": "main"}]',
    stream=True,
    genius=True
)

data = json.loads(result)
print(f"Message: {data['message']}")
print(f"Sources: {len(data['sources'])}")
print(f"Duration: {data['streaming_metadata']['duration']:.2f}s")
```

### Conversational Streaming

```python
# Maintain session for conversation
session_id = "user-conversation-123"

# First query
result1 = await query_repository(
    query="What is this repository about?",
    repositories='[{"remote": "github", "repository": "myorg/myapp", "branch": "main"}]',
    stream=True,
    session_id=session_id
)

# Follow-up query using same session
result2 = await query_repository(
    query="Show me the main API endpoints",
    repositories='[{"remote": "github", "repository": "myorg/myapp", "branch": "main"}]',
    stream=True,
    session_id=session_id,  # Reuse session for context
    previous_messages=f'[{{"role": "user", "content": "What is this repository about?"}}, {{"role": "assistant", "content": "{json.loads(result1)["message"]}"}}]'
)
```

### Performance Monitoring

```python
result = await query_repository(
    query="Complex analysis query...",
    repositories='[{"remote": "github", "repository": "large/repo", "branch": "main"}]',
    stream=True
)

data = json.loads(result)
metadata = data['streaming_metadata']

print(f"Performance Metrics:")
print(f"  • Total duration: {metadata['duration']:.2f}s")
print(f"  • Time to first chunk: {metadata['time_to_first_chunk']:.2f}s")
print(f"  • Text chunks: {metadata['text_chunks']}")
print(f"  • Citations: {metadata['citations_received']}")
```

## Benefits for Conversational Tools

### 1. **Real-Time Feedback**
- Users see progress immediately
- Better engagement during long queries
- Perceived performance improvement

### 2. **Progressive Enhancement**
- Can show partial results if connection fails
- Citations appear as they're discovered
- Session information updates dynamically

### 3. **Resource Efficiency**
- Process chunks as they arrive
- Lower memory usage
- Better timeout handling

### 4. **Monitoring & Debugging**
- Comprehensive performance metrics
- Chunk-level timing information
- Session tracking for debugging

## Migration from Previous Implementation

### Before (Collected Chunks)
```python
# Old implementation collected all chunks
chunks = []
async for chunk in stream:
    chunks.append(chunk)
return {"message": "".join(chunks)}
```

### After (Real-Time Processing)
```python
# New implementation processes chunks in real-time
message_parts = []
citations = []
async for chunk in stream:
    if chunk["type"] == "text":
        message_parts.append(chunk["content"])
    elif chunk["type"] == "citation":
        citations.append({
            "file": chunk["file"],
            "lines": chunk["lines"]
        })
```

## Best Practices

### 1. **Use Streaming for Long Queries**
Enable streaming for queries that might take >5 seconds:
```python
stream = len(query) > 100 or "detailed" in query.lower()
```

### 2. **Maintain Session Context**
Keep session IDs for conversational interfaces:
```python
session_id = session_id or str(uuid.uuid4())
```

### 3. **Handle Citations Gracefully**
Process citations as they arrive:
```python
for citation in data.get("sources", []):
    print(f"📎 {citation['file']}:{citation['lines']}")
```

### 4. **Monitor Performance**
Use streaming metadata for optimization:
```python
if metadata["duration"] > 30:
    print("⚠️ Query took longer than expected")
```

## Troubleshooting

### Common Issues

1. **No Streaming Data**: Repository may not be indexed
2. **Empty Chunks**: Check network connectivity
3. **Missing Citations**: Repository may lack indexed files
4. **Session Issues**: Ensure consistent session ID usage

### Debug Information

Enable detailed logging:
```python
import logging
logging.getLogger("greptile-mcp").setLevel(logging.DEBUG)
```

## Future Enhancements

- **Real-time streaming to clients** (WebSocket support)
- **Chunk-level caching** for repeated queries
- **Stream compression** for bandwidth optimization
- **Multi-repository parallel streaming**
- **Custom chunk types** for specialized use cases

---

The enhanced streaming implementation provides a foundation for building responsive, conversational code search tools that feel natural and engaging to users.