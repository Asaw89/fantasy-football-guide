from draft_board import build_board


def _normalize(name):
    n = name.lower().replace(".", "").replace("'", "")
    for suffix in (" jr", " sr", " iii", " ii"):
        n = n.replace(suffix, "")
    return n.strip()


_vor_cache = None


def get_vor_lookup():
    """Build {normalized_name: vor} from the draft board once."""
    global _vor_cache
    if _vor_cache is None:
        board = build_board("pts_ppr", 10)
        _vor_cache = {_normalize(p["name"]): p["vor"] for p in board}
    return _vor_cache


def player_vor(name):
    """VOR for a single player by name (0 if not found, e.g. defenses)."""
    return get_vor_lookup().get(_normalize(name), 0)


def evaluate_trade(give_players, get_players):
    """Compare total VOR on each side of a trade.
    give_players / get_players are lists of player-name strings."""
    give_vor = sum(player_vor(n) for n in give_players)
    get_vor = sum(player_vor(n) for n in get_players)
    diff = round(get_vor - give_vor, 1)
    return {
        "give_vor": round(give_vor, 1),
        "get_vor": round(get_vor, 1),
        "diff": diff,  # positive = you gain value
        "verdict": (
            "You gain value"
            if diff > 5
            else "You lose value"
            if diff < -5
            else "Roughly even"
        ),
    }


STARTERS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}


def analyze_roster(players):
    """Return {position: [players sorted by VOR desc]} and surplus/need info."""
    from collections import defaultdict

    by_pos = defaultdict(list)
    for p in players:
        by_pos[p["position"]].append({"name": p["name"], "vor": player_vor(p["name"])})
    for pos in by_pos:
        by_pos[pos].sort(key=lambda x: x["vor"], reverse=True)

    # Surplus = startable-value players beyond starting need; need = short of it
    surplus, need = {}, {}
    for pos, req in STARTERS.items():
        pool = by_pos.get(pos, [])
        # "startable value" = positive VOR
        valuable = [p for p in pool if p["vor"] > 0]
        if len(valuable) > req:
            surplus[pos] = valuable[req:]  # the extras beyond starters
        if len(valuable) < req:
            need[pos] = req - len(valuable)
    return by_pos, surplus, need


def recommend_trade(my_players, their_players):
    """Suggest a balanced trade: my surplus fills their need, theirs fills mine."""
    _, my_surplus, my_need = analyze_roster(my_players)
    _, their_surplus, their_need = analyze_roster(their_players)

    suggestions = []
    # Look for: a position I'm deep at that THEY need, paired with
    # a position they're deep at that I need.
    for give_pos, my_extras in my_surplus.items():
        if give_pos not in their_need:
            continue  # they don't need what I'm offering
        for get_pos, their_extras in their_surplus.items():
            if get_pos not in my_need:
                continue  # I don't need what they're offering
            # Pick the best available on each side, closest in value
            give_player = my_extras[0]
            # find their player closest in VOR to give_player (fair-ish)
            get_player = min(
                their_extras, key=lambda x: abs(x["vor"] - give_player["vor"])
            )
            diff = round(get_player["vor"] - give_player["vor"], 1)
            suggestions.append(
                {
                    "give": give_player["name"],
                    "give_pos": give_pos,
                    "give_vor": round(give_player["vor"], 1),
                    "get": get_player["name"],
                    "get_pos": get_pos,
                    "get_vor": round(get_player["vor"], 1),
                    "diff": diff,
                    "fairness": abs(diff),  # lower = fairer
                }
            )
    # Sort by fairness (most balanced first)
    suggestions.sort(key=lambda x: x["fairness"])
    return suggestions


def scan_all_teams(my_players, all_rosters, my_team_name):
    """Run recommend_trade against every other team, return the best opportunities."""
    opportunities = []
    for roster in all_rosters:
        if my_team_name.lower() in roster["team"].lower():
            continue  # skip my own team
        recs = recommend_trade(my_players, roster["players"])
        for r in recs:
            opportunities.append({**r, "team": roster["team"]})
    # Sort by fairness (most balanced trades first)
    opportunities.sort(key=lambda x: x["fairness"])
    return opportunities
