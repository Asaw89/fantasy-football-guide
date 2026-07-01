import requests
import json

SEASON = "2025"  # a completed season, so data is guaranteed to exist
POSITION = "RB"

url = f"https://api.sleeper.com/projections/nfl/{SEASON}"
params = {
    "season_type": "regular",
    "position[]": POSITION,
    "order_by": "pts_ppr",
}

resp = requests.get(url, params=params, timeout=30)
print("Status code:", resp.status_code)

data = resp.json()
print("Players returned:", len(data))

# Show the shape of one record so we know exactly what fields we have
print("\nFirst record:")
print(json.dumps(data[0], indent=2)[:1500])
