"""
Ingest Sleeper stats into the database.

Same code loads BOTH historical seasons and this year's live weeks —
that's the whole design goal. Computes team-level shares at ingestion time.
"""

import requests
from collections import defaultdict
from database import get_connection, init_db

POSITIONS = ["QB", "RB", "WR", "TE"]


def _num(stats, key):
    v = stats.get(key)
    return float(v) if v is not None else 0.0


def fetch_week(season, week):
    """Fetch all players' stats for one season/week from Sleeper."""
    records = []
    for pos in POSITIONS:
        url = f"https://api.sleeper.com/stats/nfl/{season}/{week}"
        params = {"season_type": "regular", "position[]": pos, "order_by": "pts_ppr"}
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        records.extend(r.json())
    return records


def ingest_week(season, week, verbose=False):
    """Fetch one week, compute shares, and store it."""
    records = fetch_week(season, week)
    if not records:
        return 0

    # First pass: compute team totals (for share denominators)
    team_targets = defaultdict(float)
    team_air_yd = defaultdict(float)
    for rec in records:
        stats = rec.get("stats") or {}
        team = (rec.get("player") or {}).get("team")
        if not team:
            continue
        team_targets[team] += _num(stats, "rec_tgt")
        team_air_yd[team] += _num(stats, "rec_air_yd")

    conn = get_connection()
    cur = conn.cursor()
    inserted = 0

    for rec in records:
        stats = rec.get("stats") or {}
        info = rec.get("player") or {}
        pid = rec.get("player_id")
        if not pid:
            continue
        team = info.get("team")
        name = f"{info.get('first_name', '')} {info.get('last_name', '')}".strip()
        pos = info.get("position")

        # Upsert player identity
        cur.execute(
            """
            INSERT INTO players (player_id, name, position, team)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(player_id) DO UPDATE SET name=excluded.name,
                position=excluded.position, team=excluded.team
        """,
            (pid, name, pos, team),
        )

        # Compute shares
        snaps = _num(stats, "off_snp")
        tm_snaps = _num(stats, "tm_off_snp")
        snap_share = round(snaps / tm_snaps, 3) if tm_snaps else None

        tgts = _num(stats, "rec_tgt")
        tm_tgts = team_targets.get(team, 0)
        target_share = round(tgts / tm_tgts, 3) if tm_tgts else None

        air = _num(stats, "rec_air_yd")
        tm_air = team_air_yd.get(team, 0)
        air_share = round(air / tm_air, 3) if tm_air else None

        cur.execute(
            """
            INSERT OR REPLACE INTO player_game_stats (
                player_id, season, week, team, position,
                pts_ppr, pts_half_ppr, pts_std,
                snaps, team_snaps, snap_share,
                rush_att, rush_yd, rush_td, rush_rz_att, rush_yac, rush_btkl,
                targets, team_targets, target_share, rec, rec_yd, rec_td,
                rec_rz_tgt, rec_air_yd, air_yard_share, rec_yar,
                pass_att, pass_yd, pass_td, pass_int, pass_air_yd, pass_rz_att,
                gp, raw_json
            ) VALUES (?,?,?,?,?, ?,?,?, ?,?,?, ?,?,?,?,?,?, ?,?,?,?,?,?, ?,?,?,?, ?,?,?,?,?,?, ?,?)
        """,
            (
                pid,
                season,
                week,
                team,
                pos,
                _num(stats, "pts_ppr"),
                _num(stats, "pts_half_ppr"),
                _num(stats, "pts_std"),
                snaps,
                tm_snaps,
                snap_share,
                _num(stats, "rush_att"),
                _num(stats, "rush_yd"),
                _num(stats, "rush_td"),
                _num(stats, "rush_rz_att"),
                _num(stats, "rush_yac"),
                _num(stats, "rush_btkl"),
                tgts,
                tm_tgts,
                target_share,
                _num(stats, "rec"),
                _num(stats, "rec_yd"),
                _num(stats, "rec_td"),
                _num(stats, "rec_rz_tgt"),
                air,
                air_share,
                _num(stats, "rec_yar"),
                _num(stats, "pass_att"),
                _num(stats, "pass_yd"),
                _num(stats, "pass_td"),
                _num(stats, "pass_int"),
                _num(stats, "pass_air_yd"),
                _num(stats, "pass_rz_att"),
                _num(stats, "gp"),
                __import__("json").dumps(stats),
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    if verbose:
        print(f"  {season} wk{week}: {inserted} players")
    return inserted


def ingest_season(season, weeks=range(1, 19), verbose=True):
    total = 0
    for wk in weeks:
        try:
            total += ingest_week(season, wk, verbose=verbose)
        except Exception as e:
            print(f"  {season} wk{wk} FAILED: {e}")
    return total


if __name__ == "__main__":
    init_db()
    print("Ingesting a test week (2024 week 1)...")
    n = ingest_week(2024, 1, verbose=True)
    print(f"Done. {n} rows.")
