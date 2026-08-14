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


def get_waiver_targets(league, my_team_name="", size=50, position=None):
    """Rank available free agents by projected value, flagging needs and injuries."""
    fas = league.free_agents(size=size, position=position)

    # Figure out my roster needs (empty until you've drafted)
    my_team = next(
        (t for t in league.teams if my_team_name.lower() in t.team_name.lower()), None
    )
    my_positions = [p.position for p in my_team.roster] if my_team else []
    counts = {pos: my_positions.count(pos) for pos in STARTERS}
    needs = {pos: max(0, STARTERS[pos] - counts.get(pos, 0)) for pos in STARTERS}

    targets = []
    for p in fas:
        proj = getattr(p, "projected_total_points", 0) or 0
        status = getattr(p, "injuryStatus", "ACTIVE")
        fills_need = needs.get(p.position, 0) > 0
        # Rank score: projection, boosted if it fills a starting need
        score = proj + (25 if fills_need else 0)
        targets.append(
            {
                "name": p.name,
                "player_id": getattr(p, "playerId", None),
                "position": p.position,
                "team": p.proTeam,
                "proj": round(proj, 1),
                "owned": round(getattr(p, "percent_owned", 0), 1),
                "status": status,
                "fills_need": fills_need,
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
