import os
from dotenv import load_dotenv
from espn_api.football import League
from draft_board import build_board

load_dotenv()


def normalize(name):
    n = name.lower().replace(".", "").replace("'", "")
    for suffix in (" jr", " sr", " iii", " ii"):
        n = n.replace(suffix, "")
    return n.strip()


# Build VOR lookup from your board
board = build_board("pts_ppr", 10)
vor_lookup = {normalize(p["name"]): p["vor"] for p in board}

# Get all rostered players across your league
league = League(
    league_id=int(os.getenv("LEAGUE_ID_1")),
    year=int(os.getenv("YEAR")),
    espn_s2=os.getenv("ESPN_S2"),
    swid=os.getenv("SWID"),
)

matched, unmatched = 0, []
for t in league.teams:
    for p in t.roster:
        if normalize(p.name) in vor_lookup:
            matched += 1
        else:
            unmatched.append(f"{p.name} ({p.position})")

total = matched + len(unmatched)
print(f"Matched to VOR: {matched} / {total}")
print(f"Unmatched ({len(unmatched)}):")
for u in unmatched:
    print(f"  {u}")
