import os
from dotenv import load_dotenv
from espn_api.football import League

load_dotenv()
league = League(
    league_id=int(os.getenv("LEAGUE_ID_1")),
    year=int(os.getenv("YEAR")),
    espn_s2=os.getenv("ESPN_S2"),
    swid=os.getenv("SWID"),
)

print("Current week:", league.current_week)
matchups = league.box_scores(1)  # Week 1
print(f"Matchups found: {len(matchups)}")
for m in matchups:
    home = m.home_team.team_name if m.home_team else "?"
    away = m.away_team.team_name if m.away_team else "?"
    print(f"  {home} ({m.home_score}) vs {away} ({m.away_score})")
