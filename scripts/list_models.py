
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY is missing.")
else:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = httpx.get(url, timeout=10.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print("Available Models:")
            for m in models:
                if "generateContent" in m.get("supportedGenerationMethods", []):
                    print(f" - {m['name']} ({m['displayName']})")
        else:
            print(f"Error listing models: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Exception: {e}")
