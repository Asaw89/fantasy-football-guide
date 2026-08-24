import streamlit as st
from collections import Counter
from draft_board import build_board, NUM_TEAMS
from categories import sleepers, top_rookies, boom_ceiling, high_floor
from grader import grade_draft
from collections import Counter as _C
from player_tags import get_tags, TAG_STYLES
from news import get_top_stories
import streamlit as st
from config import (
    STARTERS,
    BENCH_SPOTS,
    NEED_BONUS,
    TOP_N,
    SCORING_LABELS,
    POS_COLORS,
    inject_css,
)
from helpers import badge, sleeper_photo, espn_photo, player_key
from sidebar import render_sidebar
from draft_view import render_draft_mode
from season_view import render_season_mode

st.set_page_config(page_title="Fantasy Command Center", page_icon="🏈", layout="wide")
inject_css()


@st.cache_data(show_spinner="Loading projections from Sleeper...")
def load_board(scoring, num_teams):
    return build_board(scoring, num_teams)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_news(name, team, position):
    from news import get_player_news

    return get_player_news(name, team, position)


@st.cache_data(ttl=600, show_spinner="Pulling free agents from ESPN...")
def load_waivers():
    from waivers import get_league, get_waiver_targets
    import os

    league = get_league()
    return get_waiver_targets(league, os.getenv("MY_TEAM_NAME", ""), size=40)


def draft_player(p, mine):
    st.session_state.drafted.add(player_key(p))
    if mine:
        st.session_state.my_roster.append(p)


def reset_draft():
    st.session_state.drafted = set()
    st.session_state.my_roster = []


def load_top_stories(player_names):
    from news import get_top_stories

    return get_top_stories(list(player_names) if player_names else None)


# ---- Session defaults ----
if "drafted" not in st.session_state:
    st.session_state.drafted = set()
if "my_roster" not in st.session_state:
    st.session_state.my_roster = []
if "scoring" not in st.session_state:
    st.session_state.scoring = "PPR"
if "league_size" not in st.session_state:
    st.session_state.league_size = 10
if "pos_filter" not in st.session_state:
    st.session_state.pos_filter = "All"

# ---- Load board (needed by player search in both modes) ----
board = load_board(
    SCORING_LABELS[st.session_state.scoring], st.session_state.league_size
)
board = list({player_key(x): x for x in board}.values())  # de-duplicate

my_roster = st.session_state.my_roster
available = [p for p in board if player_key(p) not in st.session_state.drafted]
available.sort(key=lambda p: p["vor"], reverse=True)

counts = Counter(p["position"] for p in my_roster)
needs = {pos: max(0, STARTERS[pos] - counts.get(pos, 0)) for pos in STARTERS}


def adjusted_score(p):
    bonus = NEED_BONUS if needs.get(p["position"], 0) > 0 else 0
    return p["vor"] + bonus


mode = render_sidebar(
    board, my_roster, needs, load_top_stories, cached_news, reset_draft
)

# ==================== HEADER ====================
subtitle = (
    "Value-based rankings · live board"
    if mode == "Draft"
    else "In-season tools · live from your league"
)
st.markdown(
    f"<div class='cc-title'>🏈 Fantasy <span class='accent'>Command Center</span></div>"
    f"<div class='cc-sub'>{subtitle}</div>",
    unsafe_allow_html=True,
)

# ==================== DRAFT MODE ====================
if mode == "Draft":
    render_draft_mode(board, available, my_roster, needs, adjusted_score, draft_player)

# ==================== IN-SEASON MODE ====================
if mode == "In-Season":
    render_season_mode(load_waivers)
