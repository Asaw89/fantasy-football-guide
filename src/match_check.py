import json
from draft_board import build_board

with open("src/espn_rankings.json") as f:
    espn = json.load(f)

board = build_board("pts_ppr", 10)


def normalize(name):
    n = name.lower().replace(".", "").replace("'", "")
    for suffix in (" jr", " sr", " iii", " ii"):
        n = n.replace(suffix, "")
    return n.strip()


sleeper_norm = {normalize(p["name"]): p["name"] for p in board}

matched, unmatched = [], []
for r in espn:
    if r["position"] == "DST":
        continue
    if normalize(r["name"]) in sleeper_norm:
        matched.append(r)
    else:
        unmatched.append(r)

total = len([r for r in espn if r["position"] != "DST"])
print(f"Matched: {len(matched)} / {total}")
print(f"Unmatched ({len(unmatched)}):")
for r in unmatched:
    print(f"  {r['espn_rank']}. {r['name']} ({r['position']}) {r['team']}")
