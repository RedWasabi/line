import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GIST_ID = os.environ.get("GIST_ID")
GH_PAT = os.environ.get("GH_PAT")

if not GIST_ID or not GH_PAT:
    print("❌ Error: GIST_ID or GH_PAT not found in environment or .env file.")
    exit()

GIST_API_URL = f"https://api.github.com/gists/{GIST_ID}"

def reset_state():
    """Overwrites the watchlist.json in Gist with an empty dictionary."""
    headers = {
        "Authorization": f"token {GH_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    # Empty state
    data = {
        "files": {
            "watchlist.json": {
                "content": json.dumps({}, indent=2)
            }
        }
    }
    
    print(f"🔄 Attempting to reset Gist {GIST_ID}...")
    try:
        response = requests.patch(GIST_API_URL, headers=headers, json=data)
        if response.status_code == 200:
            print("✅ Success! watchlist.json has been reset to a fresh start.")
        else:
            print(f"❌ Failed to reset Gist: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    reset_state()
