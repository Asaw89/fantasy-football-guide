import requests

url = "https://api.sleeper.com/projections/nfl/2026"
params = {"season_type": "regular", "position[]": "RB", "order_by": "pts_ppr"}
data = requests.get(url, params=params, timeout=30).json()

with_injury = 0
statuses = {}
for r in data:
    p = r.get("player", {})
    inj = p.get("injury_status")
    if inj:
        with_injury += 1
        statuses[inj] = statuses.get(inj, 0) + 1

print(f"RBs with an injury_status set: {with_injury} / {len(data)}")
print(f"Status values seen: {statuses}")
# Show any that have one
for r in data[:40]:
    p = r.get("player", {})
    if p.get("injury_status"):
        print(
            f"  {p.get('first_name')} {p.get('last_name')}: "
            f"{p.get('injury_status')} ({p.get('injury_body_part')})"
        )
