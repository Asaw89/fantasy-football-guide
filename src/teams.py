import os
from dotenv import load_dotenv
from espn_api.football import League

load_dotenv()

# Define the configured teams from .env
TEAMS = [
    {
        "label": os.getenv("TEAM_LABEL_1") or os.getenv("TEAM_NAME_1", "Team 1"),
        "league_id": os.getenv("LEAGUE_ID_1"),
        "team_id": int(os.getenv("TEAM_ID_1")) if os.getenv("TEAM_ID_1") else None,
        "team_name": os.getenv("TEAM_NAME_1", ""),
    },
    {
        "label": os.getenv("TEAM_LABEL_2") or os.getenv("TEAM_NAME_2", "Team 2"),
        "league_id": os.getenv("LEAGUE_ID_2"),
        "team_id": int(os.getenv("TEAM_ID_2")) if os.getenv("TEAM_ID_2") else None,
        "team_name": os.getenv("TEAM_NAME_2", ""),
    },
]
TEAMS = [t for t in TEAMS if t["league_id"]]


def get_league_for(team_config):
    """Build an ESPN League object for a given team config."""
    return League(
        league_id=int(team_config["league_id"]),
        year=int(os.getenv("YEAR")),
        espn_s2=os.getenv("ESPN_S2"),
        swid=os.getenv("SWID"),
    )


def get_my_roster(team_config):
    """Return the list of players on the user's team for the given config."""
    league = get_league_for(team_config)
    team_id = team_config.get("team_id")
    if team_id is not None:
        team = next((t for t in league.teams if t.team_id == team_id), None)
    else:
        name = team_config["team_name"].lower()
        team = next((t for t in league.teams if name in t.team_name.lower()), None)
    if not team:
        return None, league
    roster = [
        {
            "name": p.name,
            "position": p.position,
            "team": p.proTeam,
            "player_id": getattr(p, "playerId", None),
            "injury_status": getattr(p, "injuryStatus", "ACTIVE"),
            "proj": getattr(p, "projected_total_points", 0),
        }
        for p in team.roster
    ]
    return roster, league
