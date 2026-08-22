# Manually curated player tags. Add or remove names anytime — just match the
# spelling to how the player appears on your board (first + last name).

RIDE_OR_DIE = [
    "DeVonta Smith",
    "Colston Loveland",
    # add Berry's ride-or-die guys here
]

BREAKOUTS = [
    "Chase Brown",
    "Ladd McConkey",
    "Kenneth Walker",
    "Luther Burden III",
    # add analyst breakout picks here
]

VALUE = [
    "Chris Godwin",
    "Quentin Johnston",
    # players going later that can have an impact
]

# Maps each tag to its display label, emoji, and color
TAG_STYLES = {
    "ride_or_die": {"label": "RIDE OR DIE", "color": "#78f472"},
    "breakout": {"label": "BREAKOUT", "color": "#facc15"},
    "value": {"label": "VALUE", "color": "#3441d3"},
}


def _normalize(name):
    n = name.lower().replace(".", "").replace("'", "")
    for suffix in (" jr", " sr", " iii", " ii"):
        n = n.replace(suffix, "")
    return n.strip()


# Build lookup sets once
_ride = {_normalize(n) for n in RIDE_OR_DIE}
_break = {_normalize(n) for n in BREAKOUTS}
_value = {_normalize(n) for n in VALUE}


def get_tags(player_name):
    """Return a list of tag keys for a given player name."""
    key = _normalize(player_name)
    tags = []
    if key in _ride:
        tags.append("ride_or_die")
    if key in _break:
        tags.append("breakout")
    if key in _value:
        tags.append("value")
    return tags
