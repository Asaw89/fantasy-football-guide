from config import POS_COLORS


def badge(pos, tier=""):
    c = POS_COLORS.get(pos, "#94a3b8")
    return f"<span class='badge' style='background:{c}22;color:{c};border:1px solid {c}55;'>{pos}{tier}</span>"


def sleeper_photo(player_id):
    if not player_id:
        return None
    return f"https://sleepercdn.com/content/nfl/players/{player_id}.jpg"


def espn_photo(player_id):
    if not player_id:
        return None
    return f"https://a.espncdn.com/i/headshots/nfl/players/full/{player_id}.png"


def player_key(p):
    return f"{p['name']}|{p['team']}|{p['position']}"
