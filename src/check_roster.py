import os
from dotenv import load_dotenv
from espn_api.football import League

load_dotenv()


def show_team(league_id, team_name):
    league = League(
        league_id=int(league_id),
        year=int(os.getenv("YEAR")),
        espn_s2=os.getenv("ESPN_S2"),
        swid=os.getenv("SWID"),
    )
    team = next(
        (t for t in league.teams if team_name.lower() in t.team_name.lower()), None
    )
    if team:
        print(f"\n✓ {team.team_name} ({len(team.roster)} players):")
        for p in team.roster:
            print(f"  {p.name:24} {p.position:4} {p.proTeam}")
    else:
        print(f"\n✗ No team matched '{team_name}' in league {league_id}")
        print("  Teams found:", [t.team_name for t in league.teams])


show_team(os.getenv("LEAGUE_ID_1"), os.getenv("TEAM_NAME_1"))
show_team(os.getenv("LEAGUE_ID_2"), os.getenv("TEAM_NAME_2"))
