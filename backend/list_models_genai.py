import os
from google import genai
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.append(os.getcwd())

from config import settings

def list_models_genai():
    if settings.credentials_path.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(settings.credentials_path)
    
    print(f"Listing models via google-genai SDK...")
    print(f"Project: {settings.gcp_project_id}")
    print(f"Location: {settings.gcp_location}")
    
    client = genai.Client(
        vertexai=True,
        project=settings.gcp_project_id,
        location=settings.gcp_location
    )
    
    try:
        # Note: list_models might be on the client or under models
        # In current google-genai, it's client.models.list()
        print("\nAvailable models:")
        for model in client.models.list():
            print(f"- {model.name}")
    except Exception as e:
        print(f"Failed to list models: {e}")

if __name__ == "__main__":
    list_models_genai()
