import os
from dotenv import load_dotenv
from espn_api.football import League

load_dotenv()

league = League(
    league_id=int(os.getenv("LEAGUE_ID")),
    year=int(os.getenv("YEAR")),
    espn_s2=os.getenv("ESPN_S2"),
    swid=os.getenv("SWID"),
)

my_name = os.getenv("MY_TEAM_NAME", "")

# Confirm you're connected — list every team
print("Teams in league:")
for t in league.teams:
    print(f"  - {t.team_name}")

# Find and print your roster
my_team = next(
    (t for t in league.teams if my_name.lower() in t.team_name.lower()),
    None,
)
if my_team:
    print(f"\nYour roster ({my_team.team_name}):")
    for p in my_team.roster:
        status = getattr(p, "injuryStatus", "ACTIVE")
        print(f"  {p.position:4} {p.name:24} {p.proTeam:4} [{status}]")

# Waiver teaser — top available running backs
print("\nTop free-agent RBs:")
for p in league.free_agents(size=5, position="RB"):
    print(f"  {p.name} ({p.proTeam})")
