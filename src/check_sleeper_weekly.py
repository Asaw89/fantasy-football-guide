import requests

# Sleeper weekly projections — try current season, week 1
season = 2026
week = 1
url = f"https://api.sleeper.com/projections/nfl/{season}/{week}"
params = {"season_type": "regular", "position[]": "WR", "order_by": "pts_ppr"}
resp = requests.get(url, params=params, timeout=30)
print("Status:", resp.status_code)

data = resp.json()
print(f"Players returned: {len(data)}")
if data:
    # Find Ja'Marr Chase to compare against ESPN's 19.95
    for r in data:
        p = r.get("player", {})
        name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
        if "Chase" in name and p.get("team") == "CIN":
            stats = r.get("stats", {})
            print(f"\n{name}:")
            print(f"  pts_ppr (weekly proj): {stats.get('pts_ppr')}")
            print(f"  pts_half_ppr: {stats.get('pts_half_ppr')}")
            break
    # Show a few players' weekly projections
    print("\nFirst 5 WRs weekly proj:")
    for r in data[:5]:
        p = r.get("player", {})
        name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
        print(f"  {name}: {r.get('stats', {}).get('pts_ppr')}")
