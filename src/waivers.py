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


def get_waiver_targets(league, my_team_name="", size=50, position=None):
    """Rank free agents by your team's actual need — injuries and thin spots —
    and flag likely handcuffs (same-team replacements for injured players)."""
    fas = league.free_agents(size=size, position=position)
    wk = league.current_week

    # Analyze MY roster: what positions am I thin at, and who's injured?
    my_team = next(
        (t for t in league.teams if my_team_name.lower() in t.team_name.lower()), None
    )
    my_positions = []
    injured_teams_by_pos = {}  # {position: set of NFL teams where my starter is hurt}
    if my_team:
        for p in my_team.roster:
            my_positions.append(p.position)
            status = getattr(p, "injuryStatus", "ACTIVE")
            if status not in ("ACTIVE", "NORMAL", None):
                injured_teams_by_pos.setdefault(p.position, set()).add(p.proTeam)

    from collections import Counter

    counts = Counter(my_positions)
    # Need score per position: how short of a healthy starting count am I?
    need_level = {}
    for pos, req in STARTERS.items():
        have = counts.get(pos, 0)
        injured_here = len(injured_teams_by_pos.get(pos, set()))
        # thin if below starter requirement; urgent if a starter is injured
        thin = max(0, req - (have - injured_here))
        need_level[pos] = thin + (injured_here * 2)  # injury weighted heavier

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

        # Handcuff flag: this free agent is at a position where my starter is
        # injured AND plays for the same NFL team as my injured player
        is_handcuff = p.proTeam in injured_teams_by_pos.get(p.position, set())

        # Ranking score: weekly projection, boosted by need and handcuff status
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


if __name__ == "__main__":
    league = get_league()
    my_name = os.getenv("MY_TEAM_NAME", "")
    for t in get_waiver_targets(league, my_name, size=15):
        flag = " ⚠️" if t["status"] != "ACTIVE" else ""
        need = " ★NEED" if t["fills_need"] else ""
        print(
            f"{t['position']:4} {t['name']:22} {t['team']:4} "
            f"proj={t['proj']:6}  owned={t['owned']}%{need}{flag}"
        )
