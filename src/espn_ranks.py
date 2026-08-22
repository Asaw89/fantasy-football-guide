import json
import os

_espn_cache = None
_berry_cache = None


def _normalize(name):
    n = name.lower().replace(".", "").replace("'", "")
    for suffix in (" jr", " sr", " iii", " ii"):
        n = n.replace(suffix, "")
    return n.strip()


def _load(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def load_espn_ranks():
    global _espn_cache
    if _espn_cache is None:
        _espn_cache = {
            _normalize(r["name"]): r["espn_rank"] for r in _load("espn_rankings.json")
        }
    return _espn_cache


def load_berry_ranks():
    global _berry_cache
    if _berry_cache is None:
        _berry_cache = {
            _normalize(r["name"]): r["berry_rank"] for r in _load("berry_rankings.json")
        }
    return _berry_cache


def attach_ranks(board):
    """Attach ESPN + Berry ranks, a three-source consensus, and disagreement flags."""
    espn = load_espn_ranks()
    berry = load_berry_ranks()

    # Sleeper rank = each player's VOR order on the board
    by_vor = sorted(board, key=lambda p: p.get("vor", 0), reverse=True)
    for i, p in enumerate(by_vor, start=1):
        p["sleeper_rank"] = i

    by_vor = sorted(board, key=lambda p: p.get("vor", 0), reverse=True)
    for i, p in enumerate(by_vor, start=1):
        p["sleeper_rank"] = i

        # ADP rank: position when sorted by ADP (lower ADP = earlier = better)
    by_adp = sorted([p for p in board if p.get("adp")], key=lambda p: p["adp"])
    for i, p in enumerate(by_adp, start=1):
        p["adp_rank"] = i
    # Value gap: how much later a player is drafted than your model ranks them.
    # Positive = VALUE (drafted later than deserved). Negative = REACH.
    for p in board:
        if p.get("adp_rank"):
            p["value_gap"] = p["adp_rank"] - p["sleeper_rank"]
        else:
            p["value_gap"] = 0

    for p in board:
        key = _normalize(p["name"])
        p["espn_rank"] = espn.get(key)
        p["berry_rank"] = berry.get(key)

        # Consensus = average of whatever sources are available for this player
        ranks = [p["sleeper_rank"]]
        if p["espn_rank"] is not None:
            ranks.append(p["espn_rank"])
        if p["berry_rank"] is not None:
            ranks.append(p["berry_rank"])
        p["consensus"] = round(sum(ranks) / len(ranks), 1)

        # Disagreement = the spread between the highest and lowest ranking
        p["rank_spread"] = max(ranks) - min(ranks)
        p["disagreement"] = p["rank_spread"] >= 15
    return board


# Backwards-compatible alias, in case draft_board still calls the old name
attach_espn_ranks = attach_ranks
