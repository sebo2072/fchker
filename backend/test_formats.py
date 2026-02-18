import os
from google import genai
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.append(os.getcwd())

from config import settings

def test_identifier_formats():
    if settings.credentials_path.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(settings.credentials_path)
    
    client = genai.Client(
        vertexai=True,
        project=settings.gcp_project_id,
        location=settings.gcp_location
    )
    
    formats = [
        "gemini-3-flash-preview",
        "publishers/google/models/gemini-3-flash-preview",
        "gemini-2.0-flash-thinking-exp-01-21",
        "gemini-2.0-flash-thinking-preview-0121",
    ]
    
    print(f"Testing identifiers in {settings.gcp_location}...")
    
    for fmt in formats:
        try:
            print(f"  Checking '{fmt}'...", end=" ", flush=True)
            response = client.models.generate_content(model=fmt, contents="hi")
            print(f"SUCCESS - Response: {response.text[:20]}...")
            return fmt
        except Exception as e:
            print(f"FAILED - {e}")
    
    return None

if __name__ == "__main__":
    test_identifier_formats()
