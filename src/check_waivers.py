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
fas = league.free_agents(size=20)
wk = league.current_week
print(f"Free agents: {len(fas)}, week {wk}")
for p in fas[:8]:
    stats = getattr(p, "stats", {})
    weekly = stats.get(wk, {}).get("projected_points", "no weekly data")
    print(
        f"  {p.name} ({p.position}) - weekly: {weekly} · season: {getattr(p, 'projected_total_points', 'N/A')}"
    )
