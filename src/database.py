import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "fantasy.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            player_id   TEXT PRIMARY KEY,
            name        TEXT,
            position    TEXT,
            team        TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_game_stats (
            player_id       TEXT,
            season          INTEGER,
            week            INTEGER,
            team            TEXT,
            position        TEXT,
            pts_ppr         REAL,
            pts_half_ppr    REAL,
            pts_std         REAL,
            snaps           REAL,
            team_snaps      REAL,
            snap_share      REAL,
            rush_att        REAL,
            rush_yd         REAL,
            rush_td         REAL,
            rush_rz_att     REAL,
            rush_yac        REAL,
            rush_btkl       REAL,
            targets         REAL,
            team_targets    REAL,
            target_share    REAL,
            rec             REAL,
            rec_yd          REAL,
            rec_td          REAL,
            rec_rz_tgt      REAL,
            rec_air_yd      REAL,
            air_yard_share  REAL,
            rec_yar         REAL,
            pass_att        REAL,
            pass_yd         REAL,
            pass_td         REAL,
            pass_int        REAL,
            pass_air_yd     REAL,
            pass_rz_att     REAL,
            gp              REAL,
            raw_json        TEXT,
            PRIMARY KEY (player_id, season, week)
        )
    """)

    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_pgs_player ON player_game_stats(player_id)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_pgs_season_week ON player_game_stats(season, week)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_pgs_team ON player_game_stats(season, week, team)"
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database ready.")
