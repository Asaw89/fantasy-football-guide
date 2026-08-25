# 🏈 Fantasy Football Command Center

A full-stack Python application for fantasy football that combines a **value-based draft assistant** with **live in-season tools**. It blends projections and rankings from multiple sources, live league data, AI-generated analysis, and a historical stats database into one dark-themed "command center" for draft day and the season beyond.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-app-red)
![Tests](https://img.shields.io/badge/tests-pytest-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

<!-- Add a screenshot named screenshot.png to your repo root and it will render here -->
![Command Center](screenshot.png)

---

## Overview

Most fantasy tools rank players by projected points — which is misleading, because it ignores positional scarcity. This app is built around **Value Over Replacement (VOR)**: how much better a player is than a freely available replacement at the same position. That correctly values an elite running back over a higher-scoring quarterback when startable quarterbacks are plentiful.

The app runs in two modes via a sidebar toggle:

- **Draft mode** — a live, value-based draft board with recommendations, tiers, scarcity tracking, a three-source consensus, and a draft grader.
- **In-Season mode** — tools that read your real ESPN league: live waiver-wire targets, with start/sit and trade evaluation on the roadmap.

An AI analyst and player-news feature run in both modes.

## Features

### Draft mode
- **Value-based rankings (VOR)** with automatic tiering, both within-position and global.
- **Three-source consensus** — blends Sleeper-based VOR, ESPN rankings, and Matthew Berry's rankings, with **disagreement flags** highlighting players the sources rate very differently (your cue to apply your own judgment).
- **Sort toggle** — order the board by VOR, Consensus, ESPN, or Berry.
- **Value scouting** — flags 💎 VALUE and ⚠️ REACH players by comparing VOR rank to ADP.
- **Injury tags and filter** — live injury designations on players, with a Show all / Healthy / Injured filter.
- **Manual player tags** — ride-or-die, breakout, and value tags, with a filter to show only tagged players.
- **Interactive draft board** — mark players Mine/Taken; a quick-entry box marks picks by partial name to keep pace with the draft clock.
- **Roster-aware recommendations** weighted by the starting positions you still need.
- **Positional scarcity panel** — tiers remaining per position, so you can spot runs before they happen.
- **QB–WR/TE stack highlighting** and **bye-week collision warnings**.
- **Positional strength flags** in the sidebar (where you're deep and valuable — trade capital).
- **Draft insight tabs** — Sleepers, Top Rookies, Boom/Ceiling, High Floor.
- **Draft grader** — grades a roster on value, completeness, and balance (calibrated against real rosters).
- Configurable **scoring** (PPR / Half / Standard) and **league size** (8/10/12/14).

### In-Season mode
- **Live waiver-wire targets** — real free agents from your ESPN league, ranked by projection and roster need, with injury flags.
- **Start/Sit and Trade Evaluator** — scaffolded, unlocking after the draft (see Roadmap).

### Both modes
- **AI player news** — current, fantasy-focused summaries sourced across the web (Anthropic Claude API with web search), **with source links** for verification.
- **AI "Ask the Analyst"** — answers aware of your league size, scoring, and roster, using real draft-strategy frameworks (Zero RB, Hero RB, etc.).
- **Top stories feed** — on-demand latest fantasy news.
- **Player headshots** on the recommendation card, news panel, and waiver list.

### Stats database
- A **SQLite database** stores per-game player stats for the 2023–2024 seasons (~23K rows), with **computed advanced metrics** — snap share, target share, and air-yard share — calculated at ingestion for fast queries.
- The same ingestion pipeline is built to load live weekly data as the season progresses.

## How It Works

The core methodology is **Value Over Replacement (VOR)**:

1. Pull season-long projections for every position from the Sleeper API.
2. Establish a *replacement level* per position — the last realistically startable player, scaled to league size.
3. Compute each player's VOR as `projected_points − replacement_level`.
4. Rank across positions by VOR, so positional scarcity is baked in.
5. Group players into tiers where scoring drops off sharply.

For **consensus rankings**, ESPN and Berry ranks are matched to the board by player and blended with the Sleeper VOR rank; large gaps between sources are flagged as disagreements.

## Architecture

The app is organized into focused modules rather than a single script:

```
src/
├── draft_app.py     # thin entry point: session setup, board prep, mode dispatch
├── config.py        # constants + CSS
├── helpers.py       # shared helper functions
├── sidebar.py       # sidebar UI (search, analyst, roster, news)
├── draft_view.py    # draft-mode UI
├── season_view.py   # in-season UI
├── draft_board.py   # VOR ranking engine + Sleeper data
├── espn_ranks.py    # three-source consensus + disagreement flags
├── categories.py    # draft-insight logic
├── grader.py        # draft grader
├── news.py          # Claude API news + analyst
├── waivers.py       # live ESPN waiver targets
├── player_tags.py   # manual player tags
├── database.py      # SQLite schema
├── ingest.py        # stats ingestion pipeline
└── connect.py       # ESPN connection
```

## Testing

A `pytest` suite covers the core logic — the ranking engine, the multi-source consensus, and the grader:

```bash
pip install pytest
pytest
```

Tests cover the VOR calculation (including the fewer-players-than-rank edge case), the consensus/disagreement blending (with mocked data loaders to isolate the logic from the JSON files), and the grader (including a regression guard for a calibration bug found during development).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python |
| Web UI | Streamlit |
| Projections / stats | Sleeper API |
| League data | ESPN (`espn-api`) |
| AI features | Anthropic Claude API (with web search) |
| Database | SQLite |
| Data parsing | pdfplumber (ESPN cheat sheet), numbers-parser (Berry rankings) |
| Testing | pytest |
| Tooling | Git/GitHub, virtual environments, `.env` secrets |

## Getting Started

### Prerequisites
- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com) *(for AI features; the draft board runs without it)*
- ESPN cookies *(optional — only for live in-season tools)*

### Installation

```bash
git clone https://github.com/<your-username>/fantasy-football-guide.git
cd fantasy-football-guide

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
LEAGUE_ID=your_league_id
YEAR=2026
ESPN_S2="your_espn_s2_cookie"
SWID={your-swid-with-braces}
MY_TEAM_NAME=YourTeamName
```

> The core draft board runs entirely on the free Sleeper API — **no keys needed** to start. The Anthropic key powers the AI features; the ESPN cookies power the in-season tools.
>
> `ESPN_S2` should be wrapped in quotes, since the cookie contains characters that can break `.env` parsing.

### Run

```bash
streamlit run src/draft_app.py
```

Opens at `http://localhost:8501`.

### Load the stats database (optional)

```bash
python src/database.py        # create the tables
python src/load_history.py    # ingest 2023–2024 game stats
```

## Roadmap

The in-season side is built out in dependency order — see `IN_SEASON_ROADMAP.md` and `SQL_DATA_ROADMAP.md` for the full plans. Highlights:

- **Roster sync** — pull your drafted team from ESPN; the prerequisite that unlocks the rest.
- **Start/Sit** and **Trade evaluator** — post-draft, once there's a real roster.
- **Stat dashboard** — player profiles (snap share, target share, red-zone usage, air yards) built on the database.
- **Team profiles** and **trend analysis** — as live game data accrues.

Some advanced metrics (routes run, yards per route run) require charted data not available in the current sources, and are noted honestly rather than faked.

## Notes

- Projections, ADP, and schedule/bye data come from the Sleeper public API; live roster and free-agent data from ESPN.
- ESPN and Berry rankings are extracted from published sources into JSON; refreshed periodically.
- AI features use the Anthropic Claude API with web search; results are cached and loaded on demand to keep the app responsive.
- Secrets (API keys, ESPN cookies) live in a gitignored `.env` and are never committed.

---

*Built as a portfolio project and a practical draft-day and in-season tool.*
