import requests

SEASON = "2026"  # switch to "2026" once projections populate
SCORING = "pts_ppr"  # "pts_ppr", "pts_half_ppr", or "pts_std" to match your league
NUM_TEAMS = 10
POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"]

# Roughly how many of each position get started across the whole league.
# This sets each position's "replacement level."
Rreplacement_rank = {
    "QB": NUM_TEAMS * 1,
    "RB": NUM_TEAMS * 2 + 6,
    "WR": NUM_TEAMS * 2 + 6,
    "TE": NUM_TEAMS * 1,
    "K": NUM_TEAMS * 1,
    "DEF": NUM_TEAMS * 1,
}

MIN_POINTS = 1.0  # drop inactive/depth players with negligible projections


def fetch_position(position, scoring="pts_ppr"):
    """Get all projected players for one position from Sleeper."""
    url = f"https://api.sleeper.com/projections/nfl/{SEASON}"
    params = {"season_type": "regular", "position[]": position, "order_by": scoring}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()

    players = []
    for rec in resp.json():
        stats = rec.get("stats") or {}
        points = stats.get(scoring)
        info = rec.get("player") or {}
        if points is None or points < MIN_POINTS:
            continue
        full_name = f"{info.get('first_name', '')} {info.get('last_name', '')}".strip()
        if not full_name:
            full_name = (
                f"{info.get('team') or 'FA'} DST"  # defenses have no personal name
            )

        players.append(
            {
                "name": f"{info.get('first_name', '')} {info.get('last_name', '')}".strip(),
                "position": position,
                "team": info.get("team") or "FA",
                "points": stats.get(scoring),
                "adp": stats.get("adp_ppr"),
                "years_exp": info.get("years_exp"),
                "touches": (stats.get("rush_att") or 0) + (stats.get("rec") or 0),
                "tds": (stats.get("rush_td") or 0) + (stats.get("rec_td") or 0),
                "big_plays": stats.get("rec_40p") or 0,
                "receptions": stats.get("rec") or 0,
            }
        )

    # Best projected first
    players.sort(key=lambda p: p["points"], reverse=True)
    return players


def add_value_over_replacement(players, position, replacement_rank):
    rank = replacement_rank[position]
    # If fewer players than the rank, use the last one as replacement
    idx = min(rank, len(players)) - 1
    replacement_points = players[idx]["points"] if players else 0
    for p in players:
        p["vor"] = round(p["points"] - replacement_points, 1)
    return players


def assign_tiers(players, gap=15.0):
    """Within a position, a new tier starts on a big scoring drop-off."""
    tier = 1
    for i, p in enumerate(players):
        if i > 0 and (players[i - 1]["points"] - p["points"]) > gap:
            tier += 1
        p["tier"] = tier
    return players


def build_board(scoring="pts_ppr", num_teams=12):
    replacement_rank = {
        "QB": num_teams * 1,
        "RB": num_teams * 2 + 6,
        "WR": num_teams * 2 + 6,
        "TE": num_teams * 1,
        "K": num_teams * 1,
        "DEF": num_teams * 1,
    }

    board = []
    for pos in POSITIONS:
        players = fetch_position(pos, scoring)
        players = add_value_over_replacement(players, pos, replacement_rank)
        players = assign_tiers(players)
        board.extend(players)

    board.sort(key=lambda p: p["vor"], reverse=True)

    global_tier = 1
    for i, p in enumerate(board):
        if i > 0 and (board[i - 1]["vor"] - p["vor"]) > 12:
            global_tier += 1
        p["global_tier"] = global_tier
    return board


if __name__ == "__main__":
    board = build_board()

    print(
        f"{'#':>3}  {'PLAYER':24} {'POS':4} {'TEAM':4} {'PROJ':>6} {'VOR':>6} {'TIER':>4}"
    )
    print("-" * 60)
    for i, p in enumerate(board[:60], start=1):
        tier_label = f"{p['position']}{p['tier']}"
        print(
            f"{i:>3}  {p['name']:24} {p['position']:4} {p['team']:4} "
            f"{p['points']:>6} {p['vor']:>6} {tier_label:>4}"
        )
