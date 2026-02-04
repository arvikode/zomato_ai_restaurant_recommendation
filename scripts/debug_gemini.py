
import os
import httpx
from dotenv import load_dotenv

# Load .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

print(f"--- Debug Gemini API Key ---")
if not api_key:
    print("ERROR: GEMINI_API_KEY is None or empty in environment.")
else:
    masked = api_key[:5] + "..." + api_key[-4:]
    print(f"Found API Key: {masked}")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [{"parts": [{"text": "Hello, simply say 'API Key Works' if you receive this."}]}],
        "generationConfig": {"temperature": 0},
    }

    try:
        print(f"Sending request to {url}...")
        response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Success! Response body:")
            print(response.text)
        else:
            print("Failed. Response body:")
            print(response.text)
            
    except Exception as e:
        print(f"Exception during request: {e}")
