import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("FANTASYPROS_API_KEY")
print("Key loaded:", "yes" if api_key else "NO — check .env")

# FantasyPros consensus rankings endpoint
url = "https://api.fantasypros.com/public/v2/json/nfl/2026/consensus-rankings"
params = {"position": "ALL", "scoring": "PPR", "type": "draft"}
headers = {"x-api-key": api_key}

resp = requests.get(url, params=params, headers=headers, timeout=30)
print("Status:", resp.status_code)

if resp.status_code == 200:
    data = resp.json()
    print("Top-level keys:", list(data.keys()))
    players = data.get("players", [])
    print(f"Players returned: {len(players)}")
    if players:
        print("\nFirst player's fields:", list(players[0].keys()))
        print("\nFirst 5 players:")
        for p in players[:5]:
            print(f"  {p}")
else:
    print("Response:", resp.text[:500])
