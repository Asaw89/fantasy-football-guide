import json
import os

_cache = None


def _normalize(name):
    n = name.lower().replace(".", "").replace("'", "")
    for suffix in (" jr", " sr", " iii", " ii"):
        n = n.replace(suffix, "")
    return n.strip()


def load_espn_ranks():
    """Load ESPN rankings from the JSON file, keyed by normalized name."""
    global _cache
    if _cache is not None:
        return _cache
    path = os.path.join(os.path.dirname(__file__), "espn_rankings.json")
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        _cache = {}
        return _cache
    _cache = {_normalize(r["name"]): r["espn_rank"] for r in data}
    return _cache


def attach_espn_ranks(board):
    """Add espn_rank, consensus rank, and disagreement flag to each player."""
    espn = load_espn_ranks()

    # First, give each player their Sleeper rank (their VOR order on the board)
    by_vor = sorted(board, key=lambda p: p.get("vor", 0), reverse=True)
    for i, p in enumerate(by_vor, start=1):
        p["sleeper_rank"] = i

    for p in board:
        e_rank = espn.get(_normalize(p["name"]))
        p["espn_rank"] = e_rank
        if e_rank is not None:
            # Consensus = average of the two ranks
            p["consensus"] = round((p["sleeper_rank"] + e_rank) / 2, 1)
            gap = abs(p["sleeper_rank"] - e_rank)
            p["rank_gap"] = gap
            p["disagreement"] = gap >= 15  # 15+ spots apart = real split
        else:
            # No ESPN rank (e.g. defenses, or players outside their top 300)
            p["consensus"] = p["sleeper_rank"]
            p["rank_gap"] = 0
            p["disagreement"] = False
    return board
