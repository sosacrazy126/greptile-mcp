#!/usr/bin/env python3
"""
Greptile Streaming Demo

Shows how Server-Sent Events (SSE) streaming works with the Greptile API
"""

import os
import httpx
import json
import asyncio
from typing import Dict, Any

async def demo_streaming_vs_blocking():
    """Compare streaming vs non-streaming responses"""
    
    api_key = os.getenv("GREPTILE_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN", os.getenv("X_GITHUB_TOKEN"))
    
    if not api_key or not github_token:
        print("❌ Need GREPTILE_API_KEY and GITHUB_TOKEN environment variables")
        return
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-GitHub-Token": github_token,
        "Content-Type": "application/json"
    }
    
    # Test query payload
    query_payload = {
        "messages": [{"role": "user", "content": "What is this repository about? Give me a detailed explanation."}],
        "repositories": [{"remote": "github", "repository": "octocat/Hello-World", "branch": "master"}],
        "genius": True
    }
    
    print("🚀 GREPTILE STREAMING DEMO")
    print("=" * 50)
    
    # 1. NON-STREAMING REQUEST
    print("\n1️⃣ NON-STREAMING REQUEST:")
    print("⏳ Waiting for complete response...")
    
    start_time = asyncio.get_event_loop().time()
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        query_payload["stream"] = False
        response = await client.post(
            "https://api.greptile.com/v2/query",
            json=query_payload,
            headers=headers
        )
        
        if response.status_code == 200:
            end_time = asyncio.get_event_loop().time()
            result = response.json()
            
            print(f"✅ Complete response received in {end_time - start_time:.2f}s")
            print(f"📄 Response length: {len(result.get('message', ''))}")
            print(f"📝 Message preview: {result.get('message', '')[:200]}...")
            print(f"🔗 Sources: {len(result.get('sources', []))}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    
    print("\n" + "=" * 50)
    
    # 2. STREAMING REQUEST  
    print("\n2️⃣ STREAMING REQUEST:")
    print("📡 Streaming response in real-time...")
    
    start_time = asyncio.get_event_loop().time()
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        query_payload["stream"] = True
        
        async with client.stream(
            "POST",
            "https://api.greptile.com/v2/query",
            json=query_payload,
            headers={**headers, "Accept": "text/event-stream"}
        ) as response:
            
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code} - {await response.aread()}")
                return
            
            message_chunks = []
            sources = []
            session_id = None
            chunk_count = 0
            
            async for chunk in response.aiter_text():
                if chunk.strip():
                    lines = chunk.strip().split('\n')
                    
                    for line in lines:
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])  # Remove 'data: ' prefix
                                chunk_count += 1
                                
                                if data.get('type') == 'text':
                                    content = data.get('content', '')
                                    message_chunks.append(content)
                                    print(content, end='', flush=True)
                                
                                elif data.get('type') == 'citation':
                                    sources.append({
                                        'file': data.get('file'),
                                        'lines': data.get('lines', 'N/A')
                                    })
                                
                                elif 'sessionId' in data:
                                    session_id = data['sessionId']
                                    
                            except json.JSONDecodeError:
                                continue
            
            end_time = asyncio.get_event_loop().time()
            
            print(f"\n\n✅ Streaming completed in {end_time - start_time:.2f}s")
            print(f"📦 Total chunks: {chunk_count}")
            print(f"📄 Message length: {len(''.join(message_chunks))}")
            print(f"🔗 Sources found: {len(sources)}")
            print(f"🎫 Session ID: {session_id}")
            
            if sources:
                print(f"\n📚 Citations:")
                for source in sources[:3]:  # Show first 3
                    print(f"  • {source['file']}:{source['lines']}")
    
    print("\n" + "=" * 50)
    print("🎯 KEY DIFFERENCES:")
    print("• Streaming: See progress in real-time, better UX")
    print("• Non-streaming: Wait for complete response, simpler parsing")
    print("• Both: Same final content, citations, and session support")

if __name__ == "__main__":
    asyncio.run(demo_streaming_vs_blocking())