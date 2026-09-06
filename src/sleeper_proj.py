import requests

_cache = {}


def _normalize(name):
    n = name.lower().replace(".", "").replace("'", "")
    for suffix in (" jr", " sr", " iii", " ii"):
        n = n.replace(suffix, "")
    return n.strip()


def get_weekly_projections(season, week, scoring="pts_ppr"):
    """Return {normalized_name: projected_points} for a given week from Sleeper."""
    cache_key = (season, week, scoring)
    if cache_key in _cache:
        return _cache[cache_key]

    proj = {}
    for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
        url = f"https://api.sleeper.com/projections/nfl/{season}/{week}"
        params = {"season_type": "regular", "position[]": pos, "order_by": "pts_ppr"}
        try:
            data = requests.get(url, params=params, timeout=30).json()
        except Exception:
            continue
        for r in data:
            p = r.get("player", {})
            name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
            pts = (r.get("stats") or {}).get(scoring)
            if name and pts is not None:
                proj[_normalize(name)] = round(pts, 1)

    _cache[cache_key] = proj
    return proj
