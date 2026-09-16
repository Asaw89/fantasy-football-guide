import os
import sys
from dotenv import load_dotenv
from espn_api.football import League
from matchups import record_week

load_dotenv()
week = int(sys.argv[1]) if len(sys.argv) > 1 else 1

league = League(
    league_id=int(os.getenv("LEAGUE_ID_1")),
    year=int(os.getenv("YEAR")),
    espn_s2=os.getenv("ESPN_S2"),
    swid=os.getenv("SWID"),
)
print(record_week(league, os.getenv("LEAGUE_ID_1"), 2026, week))
