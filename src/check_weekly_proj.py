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

team = next(
    (
        t
        for t in league.teams
        if os.getenv("TEAM_NAME_1", "").lower() in t.team_name.lower()
    ),
    None,
)

if team:
    print(f"\nRoster for {team.team_name}:")
    for p in team.roster[:5]:
        # Look for weekly projection data
        print(f"\n{p.name} ({p.position}):")
        print(
            f"  projected_total_points: {getattr(p, 'projected_total_points', 'N/A')}"
        )
        print(f"  stats keys: {list(getattr(p, 'stats', {}).keys())[:5]}")
        # ESPN often stores per-week stats in p.stats keyed by week
        stats = getattr(p, "stats", {})
        wk = league.current_week
        if wk in stats:
            print(f"  week {wk} data: {stats[wk]}")
