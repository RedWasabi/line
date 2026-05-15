import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def list_models():
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not found.")
        return

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("Fetching available models...")
        models = client.models.list()
        for m in models:
            # Print the whole object to see available attributes
            print(f"Name: {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
