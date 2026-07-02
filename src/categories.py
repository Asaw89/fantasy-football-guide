def _with_value_rank(board):
    """Rank every player 1..N by value over replacement (1 = best)."""
    ranked = sorted(board, key=lambda p: p["vor"], reverse=True)
    for i, p in enumerate(ranked, start=1):
        p["value_rank"] = i
    return ranked


def sleepers(board, min_adp=40, limit=15):
    """Players drafted later than their value — good late-round targets."""
    ranked = _with_value_rank(board)
    picks = []
    for p in ranked:
        adp = p.get("adp")
        if not adp or adp >= 300 or adp < min_adp:
            continue  # skip undrafted, no-ADP, and early picks (not "sleepers")
        p["value_gap"] = round(adp - p["value_rank"], 1)  # positive = good value
        if p["value_gap"] > 0:
            picks.append(p)
    picks.sort(key=lambda p: p["value_gap"], reverse=True)
    return picks[:limit]


def top_rookies(board, limit=15):
    """Best first-year players by value over replacement."""
    rookies = [p for p in board if p.get("years_exp") == 0]
    rookies.sort(key=lambda p: p["vor"], reverse=True)
    return rookies[:limit]


def boom_ceiling(board, limit=15):
    """Skill players whose scoring leans on TDs and long plays — high ceiling, volatile."""
    skill = [
        p for p in board if p["position"] in ("RB", "WR", "TE") and p["points"] > 50
    ]
    for p in skill:
        td_share = (p.get("tds", 0) * 6) / p["points"]
        big_share = (
            (p.get("big_plays", 0) / p["receptions"]) if p.get("receptions") else 0
        )
        p["boom_score"] = round(td_share + big_share, 3)
    skill.sort(key=lambda p: p["boom_score"], reverse=True)
    return skill[:limit]


def high_floor(board, limit=15):
    """High-volume players — touches are the best predictor of a safe weekly floor."""
    skill = [p for p in board if p["position"] in ("RB", "WR", "TE")]
    skill.sort(key=lambda p: p.get("touches", 0), reverse=True)
    return skill[:limit]
