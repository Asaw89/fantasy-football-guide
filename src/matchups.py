import os
from database import get_connection

"""
Record weekly matchup results into the database, building head-to-head
history over the season.

NOTE: The ESPN matchup data shape is based on the espn-api library's
box_scores/scoreboard methods. This must be VERIFIED against real results
after Week 1 completes — the exact attributes may need adjusting.
"""


def record_week(league, league_id, season, week):
    """Pull a completed week's matchups from ESPN and store them."""
    conn = get_connection()
    cur = conn.cursor()
    recorded = 0

    # box_scores(week) returns the matchups for that week
    try:
        matchups = league.box_scores(week)
    except Exception as e:
        conn.close()
        return f"Couldn't fetch week {week}: {e}"

    for m in matchups:
        # These attribute names are the expected shape — verify after Week 1
        home = getattr(m.home_team, "team_name", None) if m.home_team else None
        away = getattr(m.away_team, "team_name", None) if m.away_team else None
        home_score = getattr(m, "home_score", 0)
        away_score = getattr(m, "away_score", 0)
        if not home or not away:
            continue
        winner = (
            home
            if home_score > away_score
            else away
            if away_score > home_score
            else "TIE"
        )

        cur.execute(
            """
            INSERT OR REPLACE INTO matchups
            (league_id, season, week, team_a, team_b, score_a, score_b, winner)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (str(league_id), season, week, home, away, home_score, away_score, winner),
        )
        recorded += 1

    conn.commit()
    conn.close()
    return f"Recorded {recorded} matchups for week {week}"


def get_head_to_head(league_id, season, team_a, team_b):
    """Return past matchups between two teams this season."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT week, team_a, team_b, score_a, score_b, winner FROM matchups
        WHERE league_id = ? AND season = ?
        AND ((team_a = ? AND team_b = ?) OR (team_a = ? AND team_b = ?))
        ORDER BY week
    """,
        (str(league_id), season, team_a, team_b, team_b, team_a),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
