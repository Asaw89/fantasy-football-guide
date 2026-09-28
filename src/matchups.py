import os
from database import get_connection

"""
Record weekly matchup results into the database, building head-to-head
history over the season. Teams are keyed on ESPN team_id, not name, so
mid-season renames don't split a team's history.
"""


def record_week(league, league_id, season, week):
    """Pull a completed week's matchups from ESPN and store them."""
    matchups = league.box_scores(week)

    rows = []
    for m in matchups:
        if not m.home_team or not m.away_team:
            continue  # bye week

        home_id = m.home_team.team_id
        away_id = m.away_team.team_id
        home_name = m.home_team.team_name
        away_name = m.away_team.team_name
        home_score = m.home_score
        away_score = m.away_score

        if home_score == 0 and away_score == 0:
            raise ValueError(
                f"Week {week}: {home_name} vs {away_name} both scored 0 — "
                "either the week hasn't been played or the attribute names are wrong."
            )

        winner_id = (
            home_id
            if home_score > away_score
            else away_id
            if away_score > home_score
            else None
        )
        rows.append(
            (
                str(league_id),
                season,
                week,
                home_id,
                away_id,
                home_name,
                away_name,
                home_score,
                away_score,
                winner_id,
            )
        )

    conn = get_connection()
    try:
        conn.executemany(
            """
            INSERT OR REPLACE INTO matchups
            (league_id, season, week, team_a_id, team_b_id,
            team_a, team_b, score_a, score_b, winner_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()
    return len(rows)


def get_head_to_head(league_id, season, team_a_id, team_b_id):
    """Return past matchups between two teams this season."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            SELECT week, team_a, team_b, score_a, score_b, winner_id FROM matchups
            WHERE league_id = ? AND season = ?
            AND ((team_a_id = ? AND team_b_id = ?) OR (team_a_id = ? AND team_b_id = ?))
            ORDER BY week
        """,
            (str(league_id), season, team_a_id, team_b_id, team_b_id, team_a_id),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
