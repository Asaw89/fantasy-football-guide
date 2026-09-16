# Fantasy Football Command Center

A full-stack Python application for fantasy football — a value-based **draft assistant** and a live **in-season management platform** in one. It blends projections and rankings from multiple sources, syncs real ESPN leagues, runs AI-powered analysis, and is backed by a SQLite stats pipeline with automated tests and CI.

Built solo, from data pipeline to UI, and used to manage real fantasy teams during the live season.

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-app-red)
![Tests](https://img.shields.io/badge/tests-pytest-green)
![CI](https://img.shields.io/badge/CI-GitHub_Actions-brightgreen)

<!-- Add screenshot.png to the repo root and it renders here -->
![Command Center](screenshot.png)

---

## Why this project

Most fantasy tools rank players by projected points, which ignores **positional scarcity** — the single most important idea in roster building. This app is built around **Value Over Replacement (VOR)**: how much better a player is than a freely available replacement at the same position. That correctly values an elite running back over a higher-scoring quarterback when startable quarterbacks are plentiful.

Beyond the methodology, the project was an exercise in **building software the right way**: integrating real external APIs, designing a database around actual data, blending multiple sources instead of trusting one, writing tests around the core logic, and refactoring toward a clean, modular architecture as it grew.

## What it does

The app runs in two modes via a sidebar toggle.

### Draft mode
- **Value-based rankings (VOR)** with automatic tiering, within-position and global.
- **Three-source consensus** — blends Sleeper VOR, ESPN, and Matthew Berry rankings, and flags where the sources disagree (a signal to apply your own judgment).
- **Value scouting** — flags VALUE and REACH players by comparing VOR rank to average draft position.
- **Live draft board** — mark players drafted, with a quick-entry box to keep pace with the clock.
- **Roster-aware recommendations**, positional **scarcity tracking**, **QB–WR stack** highlighting, **bye-week collision** warnings, injury tags, and a **draft grader**.

### In-Season mode (live from real ESPN leagues)
- **Roster sync** across multiple leagues, with a team switcher.
- **Start/Sit** — blends ESPN + Sleeper weekly projections into a consensus, with **FLEX optimization** (picks the best remaining RB/WR/TE) and disagreement flags.
- **Trade suite** — evaluate any proposed trade by VOR, get **balanced trade recommendations** for a specific team, or **scan the entire league** for mutually beneficial deals.
- **Waiver targets** ranked by *your* roster's actual needs — an injured starter pushes that position up and flags the likely **handcuff** (same-team replacement).
- **League roster grid**, **matchup history** recording (for head-to-head rivalries), and an AI-generated **matchup preview**.

### Throughout
- **AI analyst** (Anthropic Claude API) — mode-aware (draft strategy vs. in-season management), grounded in your real roster, with live web search for current news.
- **Stats dashboard** — position-aware player stat history (passing for QBs, receiving for WRs, etc.) served from a local database.

## How VOR works

1. Pull season-long projections for every position from the Sleeper API.
2. Establish a **replacement level** per position — the last realistically startable player, scaled to league size.
3. Compute each player's VOR as `projected_points − replacement_level`.
4. Rank across positions by VOR, baking positional scarcity into the board.
5. Group players into tiers where scoring drops off sharply.

Multi-source **consensus** matches players across sources by normalized name and blends their ranks; large gaps are flagged as disagreements.

## Architecture

Refactored from a single 800-line script into focused modules:

```
src/
├── draft_app.py     # entry point: session state, mode dispatch
├── config.py        # constants + styling
├── helpers.py       # shared utilities
├── sidebar.py       # sidebar UI (search, AI analyst, news)
├── draft_view.py    # draft-mode UI
├── season_view.py   # in-season UI
├── draft_board.py   # VOR ranking engine + Sleeper data
├── espn_ranks.py    # multi-source consensus + disagreement flags
├── trades.py        # trade evaluation + recommendation engine
├── teams.py         # multi-league ESPN connection + roster sync
├── sleeper_proj.py  # weekly projection fetcher
├── waivers.py       # need-aware waiver targeting
├── grader.py        # draft grader
├── categories.py    # draft-insight logic
├── news.py          # Claude API analyst + matchup previews
├── player_tags.py   # manual player tags
├── database.py      # SQLite schema + queries
├── ingest.py        # stats ingestion pipeline
├── matchups.py      # matchup-history recording
└── connect.py       # ESPN connection helpers
tests/               # pytest suite (VOR, consensus, grader)
.github/workflows/   # CI: runs tests on every push
```

## Data & pipeline

A **SQLite database** stores per-game player stats across multiple seasons, with **computed advanced metrics** — snap share, target share, air-yard share — calculated at ingestion so dashboard queries stay fast. The same ingestion pipeline that loaded historical seasons runs weekly on live data during the season. Matchup results are recorded each week to build head-to-head history.

## Testing & CI

The core logic — the VOR engine, the multi-source consensus, and the grader — is covered by a **pytest** suite, including edge cases (fewer players than the replacement rank) and mocked data loaders to isolate logic from external files. **GitHub Actions** runs the full suite on every push.

```bash
pytest
```

## Tech stack

| Layer | Technology |
|-------|-----------|
| Language | Python |
| Web UI | Streamlit |
| Data sources | Sleeper API, ESPN (`espn-api`) |
| AI | Anthropic Claude API (with web search) |
| Database | SQLite |
| Data parsing | pdfplumber, numbers-parser |
| Testing / CI | pytest, GitHub Actions |
| Tooling | Git/GitHub, virtual environments, `.env` secrets |

## Getting started

### Prerequisites
- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com) *(for AI features; the draft board runs without it)*
- ESPN cookies *(optional — only for live in-season tools)*

### Install & run

```bash
git clone https://github.com/Asaw89/fantasy-football-guide.git
cd fantasy-football-guide

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

streamlit run src/draft_app.py
```

### Configuration

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
LEAGUE_ID_1=your_first_league_id
TEAM_NAME_1=Your Team Name
LEAGUE_ID_2=your_second_league_id
TEAM_NAME_2=Your Second Team
YEAR=2026
ESPN_S2="your_espn_s2_cookie"
SWID={your-swid-with-braces}
```

> The core draft board runs on the free Sleeper API — no keys needed to start. The Anthropic key powers AI features; ESPN cookies power the live in-season tools. Secrets live in a gitignored `.env` and are never committed.

### Load historical stats (optional)

```bash
python src/database.py
python src/load_history.py
```

## Engineering highlights

- **Multi-source data blending** with name normalization achieving a 278/278 match rate across ranking sources.
- **Database designed around real data** — inspected the API's actual fields before designing the schema; computed advanced shares at ingestion for fast reads.
- **Refactored a monolith into modules** one piece at a time, testing and committing at each step.
- **Tested the core logic and automated it in CI** — including a regression test written after catching a real calibration bug.
- **Honest scoping** — where data wasn't available (routes run, defense-vs-position rankings), the limitation is documented rather than faked.

---

*Built as a portfolio project and a practical draft-day and in-season tool — running live during the season.*
