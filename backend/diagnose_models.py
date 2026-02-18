import os
import vertexai
from vertexai.generative_models import GenerativeModel
import sys

# Add backend to sys.path
sys.path.append(os.getcwd())

from config import settings

def find_working_config():
    if settings.credentials_path.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(settings.credentials_path)
    
    locations = ['us-central1', 'us-east1', 'europe-west4', 'asia-northeast1']
    models = [
        'gemini-2.0-flash-thinking-exp-01-21',
        'gemini-2.0-flash-thinking-exp-1219',
        'gemini-3-flash-preview',
        'gemini-2.0-flash-thinking-exp'
    ]
    
    for loc in locations:
        print(f"\n--- Testing in {loc} ---")
        try:
            vertexai.init(project=settings.gcp_project_id, location=loc)
            for m in models:
                try:
                    print(f"  Checking {m}...", end=" ", flush=True)
                    model = GenerativeModel(m)
                    response = model.generate_content("Thinking about 2+2, show me your thoughts.")
                    has_thoughts = any(hasattr(p, 'thought') and p.thought for p in response.candidates[0].content.parts)
                    print(f"SUCCESS (Has thoughts: {has_thoughts})")
                    return loc, m
                except Exception as e:
                    if "404" in str(e):
                        print("404")
                    else:
                        print(f"FAILED - {e}")
        except Exception as e:
            print(f"Could not init in {loc}: {e}")
    
    return None, None

if __name__ == "__main__":
    loc, model = find_working_config()
    if loc and model:
        print(f"\nWORKING THINKING CONFIG FOUND: Location={loc}, Model={model}")
    else:
        print("\nNO WORKING THINKING CONFIG FOUND.")
