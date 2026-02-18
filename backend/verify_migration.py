import os
import asyncio
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.append(os.getcwd())

from utils.vertex_client import vertex_client
from config import settings

async def verify_sdk_migration():
    print(f"Verifying migration to google-genai SDK...")
    print(f"Project: {settings.gcp_project_id}")
    print(f"Model: {settings.gemini_model}")
    
    try:
        # 1. Test standard generation with grounding
        print("\n--- Testing Single Generation ---")
        prompt = "What is the capital of France and what is its current population?"
        result = await vertex_client.generate_with_grounding(prompt, use_grounding=True)
        
        print(f"Text: {result['text'][:100]}...")
        if result['thought']:
            print(f"Thought: {result['thought'][:100]}...")
        else:
            print("No thoughts found (might be expected for this prompt).")
            
        print(f"Citations: {len(result['citations'])} found")
        for i, cite in enumerate(result['citations'][:2]):
            print(f"  {i+1}: {cite['title']} ({cite['uri']})")
            
        # 2. Test streaming generation
        print("\n--- Testing Streaming Generation ---")
        prompt = "Explain quantum entanglement in simple terms."
        has_thought = False
        has_text = False
        
        async for chunk in vertex_client.generate_streaming(prompt, use_grounding=False):
            if chunk['type'] == 'thought':
                if not has_thought:
                    print("Thought process started...", end="", flush=True)
                    has_thought = True
            elif chunk['type'] == 'text':
                if not has_text:
                    if has_thought: print("\n", end="")
                    print("Final response started: ", end="", flush=True)
                    has_text = True
                print(chunk['text'], end="", flush=True)
        
        print("\n\nVERIFICATION COMPLETE")
        
    except Exception as e:
        print(f"\nVERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_sdk_migration())
