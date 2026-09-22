import os
from dotenv import load_dotenv
from espn_api.football import League

load_dotenv()

STARTERS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}


def get_league():
    return League(
        league_id=int(os.getenv("LEAGUE_ID")),
        year=int(os.getenv("YEAR")),
        espn_s2=os.getenv("ESPN_S2"),
        swid=os.getenv("SWID"),
    )


STARTERS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}

# Injury severity ladder — higher = more urgent need to replace
INJURY_SEVERITY = {
    "ACTIVE": 0,
    "NORMAL": 0,
    "PROBABLE": 0,
    "QUESTIONABLE": 1,
    "DOUBTFUL": 2,
    "OUT": 3,
    "SUSPENSION": 3,
    "IR": 4,
    "INJURY_RESERVE": 4,
    "PUP": 4,
    "NA": 3,
}


def get_waiver_targets(league, my_team_name="", size=50, position=None):
    """Rank free agents by roster need, weighting injured starters by severity."""
    fas = league.free_agents(size=size, position=position)
    wk = league.current_week

    my_team = next(
        (t for t in league.teams if my_team_name.lower() in t.team_name.lower()), None
    )

    # Build per-position: how many healthy starters, and injury urgency
    from collections import defaultdict

    pos_players = defaultdict(list)  # position -> list of (severity, proTeam)
    injured_teams_by_pos = defaultdict(set)
    if my_team:
        for p in my_team.roster:
            status = (getattr(p, "injuryStatus", "ACTIVE") or "ACTIVE").upper()
            sev = INJURY_SEVERITY.get(status, 0)
            pos_players[p.position].append(sev)
            if sev >= 2:  # DOUBTFUL or worse = a real hole
                injured_teams_by_pos[p.position].add(p.proTeam)

    # Need level per position: short of starters, PLUS injury urgency
    need_level = {}
    for pos, req in STARTERS.items():
        sevs = pos_players.get(pos, [])
        healthy = sum(
            1 for s in sevs if s <= 1
        )  # active or questionable = playable-ish
        thin = max(0, req - healthy)
        # add the worst injury severity at this position as extra urgency
        worst_injury = max(sevs) if sevs else 0
        injury_urgency = worst_injury if worst_injury >= 2 else 0
        need_level[pos] = thin + injury_urgency

    targets = []
    for p in fas:
        stats = getattr(p, "stats", {})
        weekly = 0
        if wk in stats and "projected_points" in stats[wk]:
            weekly = round(stats[wk]["projected_points"], 1)
        season = round(getattr(p, "projected_total_points", 0) or 0, 1)
        status = getattr(p, "injuryStatus", "ACTIVE")

        pos_need = need_level.get(p.position, 0)
        fills_need = pos_need > 0
        is_handcuff = p.proTeam in injured_teams_by_pos.get(p.position, set())

        # Score: weekly projection + need (now injury-weighted) + handcuff bonus
        score = weekly + (pos_need * 15) + (25 if is_handcuff else 0)

        targets.append(
            {
                "name": p.name,
                "player_id": getattr(p, "playerId", None),
                "position": p.position,
                "team": p.proTeam,
                "proj": weekly,
                "season": season,
                "owned": round(getattr(p, "percent_owned", 0), 1),
                "status": status,
                "fills_need": fills_need,
                "is_handcuff": is_handcuff,
                "score": round(score, 1),
            }
        )

    targets.sort(key=lambda x: x["score"], reverse=True)
    return targets
