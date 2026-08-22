import requests

for pos in ["QB", "RB", "WR", "TE"]:
    url = f"https://api.sleeper.com/stats/nfl/2024?season_type=regular&position[]={pos}&order_by=pts_ppr"
    data = requests.get(url, timeout=30).json()
    if data:
        stats = data[0].get("stats", {})
        print(f"\n=== {pos} — {len(stats)} fields ===")
        for k in sorted(stats.keys()):
            print(f"  {k}")
