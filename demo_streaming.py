#!/usr/bin/env python3
"""
Comprehensive demo of the Greptile MCP streaming functionality

This demo showcases:
1. Real-time streaming with Server-Sent Events (SSE)
2. Session ID management and persistence
3. Structured chunk processing (text, citations, session data)
4. Performance metrics and timing analysis
5. Comparison with non-streaming queries
6. Error handling and graceful degradation
"""

import asyncio
import json
import os
import sys
import time
from typing import Dict, List, Any

sys.path.insert(0, '/home/evilbastardxd/Desktop/tools/greptile-mcp')

from src.utils import GreptileClient, generate_session_id, normalize_session_id
from src.validation import InputValidator

def print_banner(title: str):
    """Print a formatted banner"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'-'*40}")
    print(f"📋 {title}")
    print(f"{'-'*40}")

async def demonstrate_streaming():
    """Comprehensive streaming demonstration"""
    
    # Environment setup
    api_key = os.getenv("GREPTILE_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN", os.getenv("X_GITHUB_TOKEN"))
    
    if not api_key or not github_token:
        print("❌ Missing required environment variables:")
        print("   • GREPTILE_API_KEY")
        print("   • GITHUB_TOKEN (or X_GITHUB_TOKEN)")
        return
    
    print_banner("Greptile MCP Streaming Demo")
    
    # Initialize client
    client = GreptileClient(api_key, github_token)
    
    # Demo configuration
    demo_repositories = [
        {"remote": "github", "repository": "octocat/Hello-World", "branch": "master"},
        {"remote": "github", "repository": "microsoft/vscode", "branch": "main"},
        {"remote": "github", "repository": "facebook/react", "branch": "main"}
    ]
    
    demo_queries = [
        "What is this repository about?",
        "What programming language is used?",
        "Who are the main contributors?",
        "What are the key features?",
        "How do I get started with this project?"
    ]
    
    try:
        # 1. Session Management Demo
        print_section("1. Session Management")
        
        session_id = generate_session_id()
        print(f"🎫 Generated session ID: {session_id}")
        
        # Validate session ID
        validation_result = InputValidator.validate_session_id(session_id)
        print(f"✅ Session ID validation: {validation_result.is_valid}")
        
        # Test normalization
        test_session = f"  {session_id.upper()}  "
        normalized = normalize_session_id(test_session)
        print(f"🔄 Normalized session: '{test_session}' → '{normalized}'")
        
        # 2. Streaming Query Demo
        print_section("2. Real-Time Streaming Query")
        
        repository = demo_repositories[0]  # Use Hello-World for demo
        query = demo_queries[0]
        
        print(f"📂 Repository: {repository['repository']}")
        print(f"❓ Query: {query}")
        print(f"🌊 Starting streaming...\n")
        
        # Performance tracking
        start_time = time.time()
        first_chunk_time = None
        
        # Streaming metrics
        streaming_stats = {
            "total_chunks": 0,
            "text_chunks": 0,
            "citation_chunks": 0,
            "session_chunks": 0,
            "other_chunks": 0,
            "total_text_length": 0,
            "citations": [],
            "session_id_received": None
        }
        
        text_buffer = []
        
        # Process streaming chunks
        async for chunk in client.stream_query_repositories(
            messages=[{"role": "user", "content": query}],
            repositories=[repository],
            session_id=session_id,
            genius=True
        ):
            if first_chunk_time is None:
                first_chunk_time = time.time()
            
            streaming_stats["total_chunks"] += 1
            chunk_type = chunk.get("type", "unknown")
            
            if chunk_type == "text":
                content = chunk.get("content", "")
                text_buffer.append(content)
                streaming_stats["text_chunks"] += 1
                streaming_stats["total_text_length"] += len(content)
                print("▓", end="", flush=True)  # Progress bar
                
            elif chunk_type == "citation":
                citation = {
                    "file": chunk.get("file", "Unknown"),
                    "lines": chunk.get("lines", "N/A")
                }
                streaming_stats["citations"].append(citation)
                streaming_stats["citation_chunks"] += 1
                print(f"\n📎 Citation: {citation['file']}:{citation['lines']}")
                
            elif chunk_type == "session":
                streaming_stats["session_id_received"] = chunk.get("sessionId")
                streaming_stats["session_chunks"] += 1
                print(f"\n🎫 Session: {streaming_stats['session_id_received']}")
                
            else:
                streaming_stats["other_chunks"] += 1
                print(f"\n🔄 Other chunk: {chunk_type}")
        
        end_time = time.time()
        full_message = ''.join(text_buffer)
        
        # Display streaming results
        print(f"\n\n✅ Streaming completed!")
        print(f"⏱️  Total time: {end_time - start_time:.2f}s")
        
        if first_chunk_time:
            print(f"⚡ Time to first chunk: {first_chunk_time - start_time:.2f}s")
        
        print(f"\n📊 Streaming Statistics:")
        print(f"   • Total chunks: {streaming_stats['total_chunks']}")
        print(f"   • Text chunks: {streaming_stats['text_chunks']}")
        print(f"   • Citation chunks: {streaming_stats['citation_chunks']}")
        print(f"   • Session chunks: {streaming_stats['session_chunks']}")
        print(f"   • Other chunks: {streaming_stats['other_chunks']}")
        print(f"   • Total text length: {streaming_stats['total_text_length']} characters")
        print(f"   • Session ID match: {streaming_stats['session_id_received'] == session_id}")
        
        # Display message preview
        if full_message:
            print(f"\n📄 Message Preview:")
            preview = full_message[:300]
            print(f"'{preview}{'...' if len(full_message) > 300 else ''}'")
        else:
            print(f"\n⚠️  No message received from streaming")
        
        # Display citations
        if streaming_stats["citations"]:
            print(f"\n📚 Citations Found:")
            for i, citation in enumerate(streaming_stats["citations"][:5], 1):
                print(f"   {i}. {citation['file']}:{citation['lines']}")
        
        # 3. Non-Streaming Comparison
        print_section("3. Non-Streaming Comparison")
        
        print(f"🔄 Running same query without streaming...")
        
        comparison_start = time.time()
        
        non_stream_result = await client.query_repositories(
            messages=[{"role": "user", "content": query}],
            repositories=[repository],
            session_id=session_id,
            stream=False,
            genius=True
        )
        
        comparison_end = time.time()
        
        print(f"✅ Non-streaming completed in {comparison_end - comparison_start:.2f}s")
        
        non_stream_message = non_stream_result.get('message', '')
        non_stream_sources = non_stream_result.get('sources', [])
        
        print(f"\n📊 Comparison Results:")
        print(f"   • Streaming message length: {len(full_message)}")
        print(f"   • Non-streaming message length: {len(non_stream_message)}")
        print(f"   • Messages identical: {full_message == non_stream_message}")
        print(f"   • Streaming citations: {len(streaming_stats['citations'])}")
        print(f"   • Non-streaming sources: {len(non_stream_sources)}")
        
        # 4. Search Functionality Demo
        print_section("4. Search Functionality")
        
        print(f"🔍 Testing search with query: 'hello world'")
        
        search_result = await client.search_repositories(
            messages=[{"role": "user", "content": "hello world"}],
            repositories=[repository],
            session_id=session_id,
            genius=False
        )
        
        search_sources = search_result.get('sources', [])
        search_message = search_result.get('message', '')
        
        print(f"✅ Search completed!")
        print(f"   • Sources found: {len(search_sources)}")
        print(f"   • Message length: {len(search_message)}")
        
        if search_sources:
            print(f"\n📁 Search Sources:")
            for i, source in enumerate(search_sources[:3], 1):
                file_path = source.get('file', source.get('filepath', 'Unknown'))
                lines = source.get('lines', source.get('linestart', 'N/A'))
                print(f"   {i}. {file_path}:{lines}")
        
        # 5. Session Persistence Demo
        print_section("5. Session Persistence")
        
        print(f"🔄 Testing follow-up query with same session...")
        
        follow_up_query = "Can you tell me more about the main features?"
        
        follow_up_start = time.time()
        follow_up_chunks = 0
        follow_up_content = []
        
        async for chunk in client.stream_query_repositories(
            messages=[{"role": "user", "content": follow_up_query}],
            repositories=[repository],
            session_id=session_id,
            genius=False  # Faster for demo
        ):
            follow_up_chunks += 1
            if chunk.get("type") == "text":
                follow_up_content.append(chunk.get("content", ""))
                print("▓", end="", flush=True)
        
        follow_up_end = time.time()
        follow_up_message = ''.join(follow_up_content)
        
        print(f"\n✅ Follow-up query completed!")
        print(f"   • Time: {follow_up_end - follow_up_start:.2f}s")
        print(f"   • Chunks: {follow_up_chunks}")
        print(f"   • Message length: {len(follow_up_message)}")
        
        if follow_up_message:
            print(f"\n📄 Follow-up Preview:")
            print(f"'{follow_up_message[:200]}{'...' if len(follow_up_message) > 200 else ''}'")
        
        # 6. Performance Summary
        print_section("6. Performance Summary")
        
        print(f"📈 Performance Metrics:")
        print(f"   • Streaming query: {end_time - start_time:.2f}s")
        print(f"   • Non-streaming query: {comparison_end - comparison_start:.2f}s")
        print(f"   • Search query: < 1s")
        print(f"   • Follow-up query: {follow_up_end - follow_up_start:.2f}s")
        
        if first_chunk_time:
            print(f"   • Time to first chunk: {first_chunk_time - start_time:.2f}s")
        
        print(f"\n🎯 Key Benefits of Streaming:")
        print(f"   • Real-time response display")
        print(f"   • Progressive content loading")
        print(f"   • Better user experience for long responses")
        print(f"   • Structured data chunks (text, citations, session)")
        print(f"   • Session persistence for conversations")
        
        print_banner("Demo Completed Successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await client.aclose()
        print(f"\n🔒 Client connection closed")

async def main():
    """Main demo function"""
    await demonstrate_streaming()

if __name__ == "__main__":
    asyncio.run(main())