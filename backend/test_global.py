import os
from google import genai
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.append(os.getcwd())

from config import settings

def test_global_location():
    if settings.credentials_path.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(settings.credentials_path)
    
    # Force global location
    client = genai.Client(
        vertexai=True,
        project=settings.gcp_project_id,
        location='global'
    )
    
    print(f"Testing 'gemini-3-flash-preview' in location 'global'...")
    
    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview', 
            contents="hi",
            config={'thinking_config': {'include_thoughts': True}}
        )
        print(f"SUCCESS - Response: {response.text[:20]}...")
        if response.candidates[0].content.parts:
            has_thoughts = any(p.thought for p in response.candidates[0].content.parts)
            print(f"Has thoughts: {has_thoughts}")
    except Exception as e:
        print(f"FAILED - {e}")

if __name__ == "__main__":
    test_global_location()
