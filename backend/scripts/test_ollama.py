#!/usr/bin/env python3
"""Test backend can reach Ollama"""
import httpx
import asyncio
import sys

async def test_ollama():
    try:
        print("🔗 Testing Backend → Ollama connection...")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                'http://ollama:11434/api/generate',
                json={
                    'model': 'llama3.2:3b',
                    'prompt': 'Say hello in one sentence',
                    'stream': False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Ollama is reachable from backend!")
                print(f"📝 Response: {data.get('response', 'No response')[:100]}")
                return True
            else:
                print(f"❌ Ollama returned status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_ollama())
    sys.exit(0 if result else 1)
