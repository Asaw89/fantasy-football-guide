# 🏈 Fantasy Football Draft Command Center

A full-stack Python web application that generates **value-based fantasy football draft rankings** from live NFL projection data, with an interactive draft board, roster-aware recommendations, configurable league scoring, and AI-powered player news.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-app-red)
![Status](https://img.shields.io/badge/status-active-brightgreen)

<!-- Add a screenshot named screenshot.png to your repo root and it will render here -->
![Draft Command Center](screenshot.png)

---

## Overview

Drafting well is the single biggest factor in a fantasy football season, but most tools just rank players by projected points — which is misleading. This app ranks players by **Value Over Replacement (VOR)**: how much better a player is than a freely available replacement at the same position. That correctly accounts for positional scarcity, so an elite running back is valued above a higher-scoring quarterback when startable quarterbacks are plentiful.

The result is a live "command center" you can run during a real draft: mark players as they're taken, get a recommendation tuned to what your roster still needs, filter by position, switch scoring formats, and pull AI-summarized news on any player — all in the browser.

## Features

- **Value-based rankings (VOR):** Players ranked by value over a position's replacement level, not raw points, with automatic tiering by scoring drop-off.
- **Interactive draft board:** Mark players "Mine" or "Taken"; the board updates live and always surfaces the best available pick.
- **Roster-aware recommendations:** The suggested pick is weighted by the starting positions you still need to fill.
- **Configurable scoring:** Toggle between PPR, Half-PPR, and Standard — the entire board re-ranks to match your league.
- **Position filtering:** View rankings for a single position (QB, RB, WR, TE, K, DST) with a live scarcity count.
- **Draft insight tabs:** Sleepers (value beating ADP), Top Rookies, Boom/Ceiling (TD- and big-play-dependent), and High Floor (high-volume, safe) angles on the board.
- **AI player news:** Look up any player and get a current, fantasy-focused summary sourced across outlets, powered by the Anthropic Claude API with web search, cached to keep costs negligible.

## How It Works

The core methodology is **Value Over Replacement (VOR)**:

1. Pull season-long projections for every position from the Sleeper API.
2. For each position, establish a *replacement level* — the projected points of the last player who would realistically start across the league (e.g. the ~12th QB, the ~30th RB in a 12-team league).
3. Compute each player's VOR as `projected_points − replacement_level`.
4. Rank all players across positions by VOR, so positional scarcity is baked into the board.
5. Group players into tiers where scoring drops off sharply between one player and the next.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python |
| Web UI | Streamlit |
| Data source | Sleeper API (NFL projections, ADP, trending data) |
| League data | ESPN (`espn-api`) — *connection built, see Roadmap* |
| AI news | Anthropic Claude API (Haiku) with web search tool |
| HTTP / config | `requests`, `python-dotenv` |
| Tooling | Git/GitHub, virtual environments, `.env`-based secrets |

## Getting Started

### Prerequisites
- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com) *(only required for the AI news feature; the draft tool runs without it)*

### Installation

```bash
# Clone the repo
git clone https://github.com/<your-username>/fantasy-football-guide.git
cd fantasy-football-guide

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
# Required only for AI player news
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional — for ESPN league features (see Roadmap)
LEAGUE_ID=your_league_id
YEAR=2025
ESPN_S2=your_espn_s2_cookie
SWID={your-swid-with-braces}
MY_TEAM_NAME=YourTeamName
```

> The core draft board runs entirely on the free Sleeper API — **no keys needed** to get started. The Anthropic key only powers the news feature.

### Run

```bash
streamlit run src/draft_app.py
```

The app opens in your browser at `http://localhost:8501`.

## Project Structure

```
fantasy-football-guide/
├── .streamlit/
│   └── config.toml         # dark theme configuration
├── src/
│   ├── draft_app.py        # Streamlit app — UI, draft board, sidebar
│   ├── draft_board.py      # VOR ranking engine + Sleeper data fetch
│   ├── categories.py       # draft-insight logic (sleepers, rookies, etc.)
│   ├── news.py             # Claude API player-news summaries
│   └── connect.py          # ESPN league connection (parked)
├── requirements.txt
└── README.md
```

## Roadmap

Planned and in-progress features:

- **ESPN league integration** — the connection is built and architecturally complete; it activates once the league is reactivated for the current season, unlocking the roster-based features below.
- **Start/Sit recommendations** — weekly lineup calls based on projections, matchup, and injury status *(in-season)*.
- **Waiver-wire targets** — rank available free agents in your league by projected value and roster fit *(in-season)*.
- **Trade evaluations** — compare value on each side of a proposed trade *(in-season)*.
- **Bye weeks & strength of schedule** — flag roster bye-week collisions and season-long matchup difficulty.
- **AI question box** — ask open-ended fantasy questions in an analyst-style voice.
- **Draft slot & snake order** — track your pick sequence to anticipate which players survive to your next turn.

## Notes

- Player projections and ADP are sourced from the Sleeper public API.
- The AI news feature uses the Anthropic Claude API with its web search tool; results are cached to minimize cost.
- Secrets (API keys, ESPN cookies) are stored in a gitignored `.env` file and never committed.

---

*Built as a portfolio project and a practical draft-day tool.*
