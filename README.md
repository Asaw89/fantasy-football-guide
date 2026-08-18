# 🏈 Fantasy Football Command Center

A full-stack Python web application for fantasy football, combining a **value-based draft assistant** with **live in-season tools** powered by your real ESPN league. It blends projections from multiple sources, live league data, and AI-generated analysis into one dark-themed "command center" you can run on draft day and throughout the season.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-app-red)
![Status](https://img.shields.io/badge/status-active-brightgreen)

<!-- Add a screenshot named screenshot.png to your repo root and it will render here -->
![Command Center](screenshot.png)

---

## Overview

Most fantasy tools just rank players by projected points — which is misleading, because it ignores positional scarcity. This app is built around **Value Over Replacement (VOR)**: how much better a player is than a freely available replacement at the same position. That correctly values an elite running back above a higher-scoring quarterback when startable quarterbacks are plentiful.

The app runs in two modes via a sidebar toggle:

- **Draft mode** — a live, value-based draft board with recommendations, tiers, scarcity tracking, consensus rankings, and a draft grader.
- **In-Season mode** — tools that read your real ESPN league: waiver-wire targets, with start/sit and trade evaluation on the roadmap.

An AI analyst and player-news feature run in both modes.

## Features

### Draft mode
- **Value-based rankings (VOR)** with automatic tiering by scoring drop-off, and both within-position and global tiers.
- **Consensus rankings** — blends the app's Sleeper-based VOR with ESPN's rankings, and flags **disagreements** where the two sources diverge, highlighting players who warrant your own judgment.
- **Interactive draft board** — mark players "Mine" or "Taken"; the board updates live and surfaces the best available pick.
- **Quick-entry box** — type a partial name and mark a pick instantly, to keep pace with a fast draft clock.
- **Roster-aware recommendations** weighted by the starting positions you still need.
- **Configurable scoring and league size** — PPR / Half-PPR / Standard and 8/10/12/14 teams; the whole board re-ranks to match.
- **Position filtering and scarcity panel** — see how many players remain in each tier per position, so you can spot positional runs before they happen.
- **QB–WR stack highlighting** — draft a QB (or pass-catcher) and their available teammates are flagged on the board.
- **Positional strength flags** and **bye-week collision warnings** in the sidebar.
- **Draft insight tabs** — Sleepers, Top Rookies, Boom/Ceiling, and High Floor.
- **Draft grader** — grades your roster on value, completeness, and balance.
- **Sort toggle** — order the board by VOR, Consensus, or ESPN rank.

### In-Season mode
- **Live waiver-wire targets** — pulls real free agents from your ESPN league, ranked by projection and roster need, with injury flags.
- **Start/Sit and Trade Evaluator** — scaffolded, unlocking after the draft (see Roadmap).

### Both modes
- **AI player news** — look up any player for a current, fantasy-focused summary sourced across the web (Anthropic Claude API with web search), **with source links** for verification.
- **AI "Ask the Analyst"** — ask open-ended questions and get answers aware of your league size, scoring, and current roster, using real draft-strategy frameworks (Zero RB, Hero RB, etc.).
- **Player headshots** on the recommendation card, news panel, and waiver list.

## How It Works

The core methodology is **Value Over Replacement (VOR)**:

1. Pull season-long projections for every position from the Sleeper API.
2. For each position, establish a *replacement level* — the projected points of the last player who would realistically start across the league (scaled to league size).
3. Compute each player's VOR as `projected_points − replacement_level`.
4. Rank all players across positions by VOR, so positional scarcity is baked in.
5. Group players into tiers where scoring drops off sharply.

For **consensus rankings**, ESPN's published ranks are matched to the board by player and blended with the Sleeper VOR rank; large gaps between the two are flagged as disagreements.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python |
| Web UI | Streamlit |
| Projections | Sleeper API (projections, ADP, trending, schedule/byes) |
| League data | ESPN (`espn-api`) — live roster and free-agent access |
| AI features | Anthropic Claude API (Haiku + Sonnet) with the web search tool |
| Data parsing | pdfplumber (ESPN cheat-sheet extraction) |
| HTTP / config | `requests`, `python-dotenv` |
| Tooling | Git/GitHub, virtual environments, `.env`-based secrets |

## Getting Started

### Prerequisites
- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com) *(for AI news and the analyst; the draft board runs without it)*
- ESPN cookies *(optional — only for the live in-season tools)*

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
# For AI news and the analyst
ANTHROPIC_API_KEY=sk-ant-your-key-here

# For ESPN in-season tools (waivers, live rosters)
LEAGUE_ID=your_league_id
YEAR=2026
ESPN_S2="your_espn_s2_cookie"
SWID={your-swid-with-braces}
MY_TEAM_NAME=YourTeamName
```

> The core draft board runs entirely on the free Sleeper API — **no keys needed** to get started. The Anthropic key powers the AI features; the ESPN cookies power the in-season tools.
>
> Note: `ESPN_S2` should be wrapped in quotes, since the cookie contains characters that can otherwise break `.env` parsing.

### Run

```bash
streamlit run src/draft_app.py
```

Opens at `http://localhost:8501`.

## Project Structure

```
fantasy-football-guide/
├── .streamlit/
│   └── config.toml         # dark theme configuration
├── src/
│   ├── draft_app.py        # Streamlit app — UI, both modes, sidebar
│   ├── draft_board.py      # VOR ranking engine, Sleeper data, byes
│   ├── categories.py       # draft-insight logic (sleepers, rookies, etc.)
│   ├── grader.py           # draft grader
│   ├── news.py             # Claude API news + "Ask the Analyst"
│   ├── waivers.py          # live ESPN waiver-wire targets
│   ├── connect.py          # ESPN league connection
│   ├── espn_ranks.py       # consensus rankings + disagreement flags
│   ├── espn_rankings.json  # extracted ESPN rankings data
│   ├── extract_espn.py     # PDF → rankings extractor (regenerate as needed)
│   └── test_cookies.py     # ESPN cookie diagnostic
├── requirements.txt
└── README.md
```

## Roadmap

The in-season side is built out in dependency order — see `IN_SEASON_ROADMAP.md` for the full plan. Highlights:

- **Roster sync** — pull your drafted team from ESPN into the app; the prerequisite that unlocks the rest.
- **Start/Sit** — weekly lineup calls from projections, matchup, and injury status.
- **Trade evaluator** — weigh value on each side of a proposed trade.
- **Rest-of-season rankings**, **player trends**, **matchup analysis**, and **playoff planning** — as live game data accrues through the season.

Some features (strength of schedule, richer start/sit stats) depend on data sources still being sourced, and are noted honestly in the roadmap rather than faked.

## Notes

- Projections, ADP, and schedule data come from the Sleeper public API; live roster and free-agent data from ESPN.
- ESPN consensus rankings are extracted from ESPN's published cheat sheet — a periodic manual refresh via `extract_espn.py`.
- AI features use the Anthropic Claude API with web search; news results are cached to minimize cost.
- Secrets (API keys, ESPN cookies) live in a gitignored `.env` file and are never committed.

---

*Built as a portfolio project and a practical draft-day and in-season tool.*
