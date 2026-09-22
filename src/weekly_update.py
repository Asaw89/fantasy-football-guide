"""
Run Every Tuesday for Weekly in-season update: ingest player stats + record matchups.
Run from src/:  python weekly_update.py        (auto-detects last completed week)
            or: python weekly_update.py n       (specific week)
"""

import os
import sys
from dotenv import load_dotenv
from espn_api.football import League
from ingest import ingest_week
from matchups import record_week
from database import get_connection

load_dotenv()
season = int(os.getenv("YEAR", 2026))

league = League(
    league_id=int(os.getenv("LEAGUE_ID_1")),
    year=season,
    espn_s2=os.getenv("ESPN_S2"),
    swid=os.getenv("SWID"),
)

# Use the week passed in, or auto-detect the last completed week
if len(sys.argv) >= 2:
    week = int(sys.argv[1])
else:
    week = league.current_week - 1  # the week that just finished
    if week < 1:
        print("No completed weeks yet.")
        sys.exit(0)

print(f"=== Weekly update for {season} Week {week} ===\n")

print("Ingesting player stats...")
n = ingest_week(season, week)
print(f"  {n} player rows ingested\n")

print("Recording matchups...")
print("  " + record_week(league, os.getenv("LEAGUE_ID_1"), season, week) + "\n")

conn = get_connection()
count = conn.execute(
    "SELECT COUNT(*) FROM player_game_stats WHERE season=? AND week=?", (season, week)
).fetchone()[0]
conn.close()
print(f"=== Done. {count} rows in database for Week {week}. ===")
