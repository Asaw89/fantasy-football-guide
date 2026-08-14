import streamlit as st
from collections import Counter
from draft_board import build_board, NUM_TEAMS
from categories import sleepers, top_rookies, boom_ceiling, high_floor
from grader import grade_draft
from collections import Counter as _C

st.set_page_config(page_title="Fantasy Command Center", page_icon="🏈", layout="wide")

# ---- Config ----
STARTERS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}
BENCH_SPOTS = 7
NEED_BONUS = 20.0
TOP_N = 30
SCORING_LABELS = {"PPR": "pts_ppr", "Half-PPR": "pts_half_ppr", "Standard": "pts_std"}

POS_COLORS = {
    "QB": "#c084fc",
    "RB": "#34d399",
    "WR": "#38bdf8",
    "TE": "#fb923c",
    "K": "#94a3b8",
    "DEF": "#f87171",
}

# ---- Styling ----
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
.stApp { background: radial-gradient(1200px 600px at 20% -10%, #14203a 0%, #0b0f17 55%, #080b11 100%); }
.stApp > div, [data-testid="stMarkdownContainer"], [data-testid="stSidebar"] * { color: #ffffff; }
[data-baseweb="select"] *, [role="listbox"] *, .stTextInput input { color: #1a1a1a !important; }
header[data-testid="stHeader"] { background: transparent; }
html, body, [class*="css"] { font-family: 'Chakra Petch', sans-serif; }
.cc-title { font-weight:700; font-size:2.1rem; letter-spacing:2px; text-transform:uppercase; color:#e6edf3; margin-bottom:0; }
.cc-title .accent { color:#00e0a4; }
.cc-sub { color:#7d8590; letter-spacing:3px; font-size:0.72rem; text-transform:uppercase; }
.stat-card { background:linear-gradient(180deg,#121826,#0d1420); border:1px solid #1f2a3a; border-radius:10px; padding:12px 16px; }
.stat-val { font-family:'JetBrains Mono',monospace; font-size:1.5rem; color:#00e0a4; font-weight:600; }
.stat-lbl { color:#7d8590; font-size:0.68rem; letter-spacing:2px; text-transform:uppercase; }
.rec-panel { background:linear-gradient(90deg, rgba(0,224,164,0.12), rgba(0,224,164,0.02)); border:1px solid rgba(0,224,164,0.35); border-left:4px solid #00e0a4; border-radius:12px; padding:18px 22px; margin:14px 0 22px; box-shadow:0 0 40px rgba(0,224,164,0.08); }
.rec-label { color:#00e0a4; letter-spacing:3px; font-size:0.72rem; text-transform:uppercase; margin-bottom:4px; }
.rec-name { font-size:1.5rem; font-weight:700; color:#f0f6fc; }
.rec-meta { color:#9aa4b2; font-size:0.9rem; margin-top:4px; font-family:'JetBrains Mono',monospace; }
.sec-head { color:#e6edf3; letter-spacing:2px; text-transform:uppercase; font-weight:600; font-size:0.95rem; border-bottom:1px solid #1f2a3a; padding-bottom:8px; margin:6px 0; }
.badge { padding:2px 9px; border-radius:6px; font-weight:600; font-size:0.78rem; font-family:'JetBrains Mono',monospace; }
.mono { font-family:'JetBrains Mono',monospace; color:#c9d1d9; }
.rank-num { font-family:'JetBrains Mono',monospace; color:#4d5866; }
.stButton > button { border-radius:8px; border:1px solid #2a3a4f; font-family:'Chakra Petch',sans-serif; letter-spacing:1px; font-weight:600; transition:all .15s ease; background:#1a2230; color:#ffffff; }
.stButton > button:hover { border-color:#00e0a4; box-shadow:0 0 12px rgba(0,224,164,0.25); }
[data-testid="stSidebar"] { background:#0a0e15; border-right:1px solid #1a2230; }
</style>
""",
    unsafe_allow_html=True,
)


def badge(pos, tier=""):
    c = POS_COLORS.get(pos, "#94a3b8")
    return f"<span class='badge' style='background:{c}22;color:{c};border:1px solid {c}55;'>{pos}{tier}</span>"


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


def player_key(p):
    return f"{p['name']}|{p['team']}|{p['position']}"


def draft_player(p, mine):
    st.session_state.drafted.add(player_key(p))
    if mine:
        st.session_state.my_roster.append(p)


def reset_draft():
    st.session_state.drafted = set()
    st.session_state.my_roster = []


# ---- Session defaults ----
if "drafted" not in st.session_state:
    st.session_state.drafted = set()
if "my_roster" not in st.session_state:
    st.session_state.my_roster = []
if "scoring" not in st.session_state:
    st.session_state.scoring = "PPR"
if "league_size" not in st.session_state:
    st.session_state.league_size = 12
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


# ==================== SIDEBAR ====================
with st.sidebar:
    # ---- Mode toggle (top) ----
    st.markdown("<div class='sec-head'>Mode</div>", unsafe_allow_html=True)
    mode = st.radio(
        "App mode",
        options=["🏈 Draft", "📅 In-Season"],
        label_visibility="collapsed",
        key="app_mode",
    )
    st.divider()

    # ---- Player Search (both modes) ----
    st.markdown("<div class='sec-head'>Player Search</div>", unsafe_allow_html=True)
    news_options = {f"{p['name']} · {p['position']} {p['team']}": p for p in board}
    choice = st.selectbox(
        "Find a player", options=list(news_options.keys()), label_visibility="collapsed"
    )
    if st.button("Get news", type="primary", use_container_width=True):
        picked = news_options[choice]
        with st.spinner(f"Searching outlets for {picked['name']}..."):
            st.session_state.news_summary = cached_news(
                picked["name"], picked["team"], picked["position"]
            )
            st.session_state.news_player = picked["name"]

    # ---- Ask the Analyst (both modes) ----
    st.markdown("<div class='sec-head'>Ask the Analyst</div>", unsafe_allow_html=True)
    user_q = st.text_input(
        "Ask a fantasy question",
        label_visibility="collapsed",
        placeholder="e.g. Should I start my WR2 this week?",
    )
    if st.button("Ask", use_container_width=True) and user_q:
        from news import ask_question

        with st.spinner("Thinking..."):
            st.session_state.answer = ask_question(user_q)

    if st.session_state.get("answer"):
        st.markdown(
            f"<div style='color:#ffffff;'>{st.session_state.answer}</div>",
            unsafe_allow_html=True,
        )

    if st.session_state.get("news_summary"):
        st.markdown(f"**{st.session_state.news_player}**")
        st.markdown(
            f"<div style='color:#ffffff;'>{st.session_state.news_summary}</div>",
            unsafe_allow_html=True,
        )

    # ---- Draft-only sidebar sections ----
    if mode == "🏈 Draft":
        st.divider()
        st.markdown("<div class='sec-head'>My Roster</div>", unsafe_allow_html=True)
        if my_roster:
            for p in my_roster:
                st.markdown(
                    f"{badge(p['position'])} &nbsp; <span style='color:#ffffff;'>{p['name']}</span> "
                    f"<span class='rank-num'>({p['team']})</span>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                "<span class='rank-num'>No picks yet</span>", unsafe_allow_html=True
            )

        # Bye week collision check
        bye_counts = _C(p.get("bye") for p in my_roster if p.get("bye"))
        heavy_byes = {wk: n for wk, n in bye_counts.items() if n >= 3}
        if heavy_byes:
            st.markdown(
                "<div class='sec-head'>⚠️ Bye Stacking</div>", unsafe_allow_html=True
            )
            for wk, n in sorted(heavy_byes.items()):
                st.markdown(
                    f"<span style='color:#fb923c'>Week {wk}: {n} players on bye</span>",
                    unsafe_allow_html=True,
                )

        st.markdown("<div class='sec-head'>Still Need</div>", unsafe_allow_html=True)
        need_labels = [f"{pos} x{n}" for pos, n in needs.items() if n > 0]
        st.markdown(
            " &nbsp;".join(
                badge(l.split()[0]) + f" <span class='mono'>{l.split()[1]}</span>"
                for l in need_labels
            )
            if need_labels
            else "<span class='mono' style='color:#34d399'>Starters filled ✓</span>",
            unsafe_allow_html=True,
        )

        starters_needed = sum(needs.values())
        total_starters = sum(STARTERS.values())
        bench_filled = max(0, len(my_roster) - (total_starters - starters_needed))
        st.markdown(
            f"<div class='sec-head'>Bench</div>"
            f"<span class='mono'>{bench_filled} / {BENCH_SPOTS} filled</span>",
            unsafe_allow_html=True,
        )

        st.divider()
        st.button("Reset draft", on_click=reset_draft, use_container_width=True)


# ==================== HEADER ====================
subtitle = (
    "Value-based rankings · live board"
    if mode == "🏈 Draft"
    else "In-season tools · live from your league"
)
st.markdown(
    f"<div class='cc-title'>🏈 Fantasy <span class='accent'>Command Center</span></div>"
    f"<div class='cc-sub'>{subtitle}</div>",
    unsafe_allow_html=True,
)


# ==================== DRAFT MODE ====================
if mode == "🏈 Draft":
    # ---- Scoring + league size ----
    st.radio(
        "League scoring",
        options=list(SCORING_LABELS.keys()),
        horizontal=True,
        key="scoring",
    )
    st.radio("League size", options=[8, 10, 12, 14], horizontal=True, key="league_size")

    # ---- Draft status cards ----
    picks_made = len(st.session_state.drafted)
    round_num = picks_made // st.session_state.league_size + 1
    pick_in_round = picks_made % st.session_state.league_size + 1

    def stat_card(label, value):
        return f"<div class='stat-card'><div class='stat-val'>{value}</div><div class='stat-lbl'>{label}</div></div>"

    m1, m2, m3 = st.columns(3)
    m1.markdown(
        stat_card("Round · Pick", f"{round_num} · {pick_in_round}"),
        unsafe_allow_html=True,
    )
    m2.markdown(stat_card("Overall Picks", picks_made), unsafe_allow_html=True)
    m3.markdown(stat_card("Your Roster", len(my_roster)), unsafe_allow_html=True)

    # ---- Recommendation ----
    if available:
        pick = max(available, key=adjusted_score)
        fills = needs.get(pick["position"], 0) > 0
        reason = (
            f"fills a need at {pick['position']}"
            if fills
            else "best value on the board"
        )
        st.markdown(
            f"<div class='rec-panel'><div class='rec-label'>Recommended Pick</div>"
            f"<div class='rec-name'>{pick['name']} &nbsp; {badge(pick['position'], pick.get('tier', ''))}</div>"
            f"<div class='rec-meta'>{reason} · PROJ {pick['points']} · VOR {pick['vor']}</div></div>",
            unsafe_allow_html=True,
        )

    # ---- Board ----
    st.markdown("<div class='sec-head'>Best Available</div>", unsafe_allow_html=True)

    filters = ["All", "QB", "RB", "WR", "TE", "K", "DEF"]
    fcols = st.columns(len(filters))
    for col, pos in zip(fcols, filters):
        btn_type = "primary" if st.session_state.pos_filter == pos else "secondary"
        if col.button(
            pos, key=f"filter_{pos}", type=btn_type, use_container_width=True
        ):
            st.session_state.pos_filter = pos
            st.rerun()

    if st.session_state.pos_filter == "All":
        shown = available
    else:
        shown = [p for p in available if p["position"] == st.session_state.pos_filter]

    st.markdown(
        f"<div style='color:#9aa4b2;font-size:0.85rem;margin:6px 0'>"
        f"Showing {min(len(shown), TOP_N)} of {len(shown)} available"
        f"{'' if st.session_state.pos_filter == 'All' else ' ' + st.session_state.pos_filter}"
        f"</div>",
        unsafe_allow_html=True,
    )

    last_tier = None
    for i, p in enumerate(shown[:TOP_N], start=1):
        if st.session_state.pos_filter == "All":
            this_tier = p.get("global_tier")
            tier_label = f"Tier {this_tier}"
        else:
            this_tier = p.get("tier")
            tier_label = f"{st.session_state.pos_filter} · Tier {this_tier}"

        if this_tier != last_tier:
            st.markdown(
                f"<div style='color:#00e0a4;font-size:0.72rem;letter-spacing:2px;"
                f"text-transform:uppercase;border-bottom:1px solid #1f2a3a;"
                f"margin:10px 0 4px;padding-bottom:4px;'>{tier_label}</div>",
                unsafe_allow_html=True,
            )
            last_tier = this_tier

        key = player_key(p)
        c = st.columns([0.5, 3.2, 1.3, 1.8, 1, 1], vertical_alignment="center")
        c[0].markdown(f"<span class='rank-num'>{i:>2}</span>", unsafe_allow_html=True)
        c[1].markdown(
            f"<span style='color:#ffffff;font-weight:600;'>{p['name']}</span> "
            f"<span class='rank-num'>{p['team']}</span>",
            unsafe_allow_html=True,
        )
        c[2].markdown(badge(p["position"], p.get("tier", "")), unsafe_allow_html=True)
        bye_txt = f" · Bye {p['bye']}" if p.get("bye") else ""
        c[3].markdown(
            f"<span class='mono'>{p['points']} / {p['vor']}<span class='rank-num'>{bye_txt}</span></span>",
            unsafe_allow_html=True,
        )
        c[4].button(
            "Mine",
            key=f"mine_{i}_{key}",
            on_click=draft_player,
            args=(p, True),
            type="primary",
            use_container_width=True,
        )
        c[5].button(
            "Taken",
            key=f"taken_{i}_{key}",
            on_click=draft_player,
            args=(p, False),
            use_container_width=True,
        )

    # ---- Draft Insights ----
    st.markdown("<div class='sec-head'>Draft Insights</div>", unsafe_allow_html=True)

    def show_list(players, stat_label, stat_key):
        for i, p in enumerate(players, start=1):
            cols = st.columns([0.5, 3, 1.2, 2], vertical_alignment="center")
            cols[0].markdown(
                f"<span class='rank-num'>{i}</span>", unsafe_allow_html=True
            )
            cols[1].markdown(
                f"<span style='color:#ffffff'>{p['name']}</span> "
                f"<span class='rank-num'>{p['team']}</span>",
                unsafe_allow_html=True,
            )
            cols[2].markdown(
                badge(p["position"], p.get("tier", "")), unsafe_allow_html=True
            )
            cols[3].markdown(
                f"<span class='mono'>{stat_label}: {p.get(stat_key)}</span>",
                unsafe_allow_html=True,
            )

    def caption(text):
        st.markdown(
            f"<div style='color:#9aa4b2;font-size:0.85rem;margin-bottom:6px'>{text}</div>",
            unsafe_allow_html=True,
        )

    t1, t2, t3, t4 = st.tabs(
        ["💤 Sleepers", "🌟 Top Rookies", "💥 Boom / Ceiling", "🛡️ High Floor"]
    )
    with t1:
        caption("Drafted later than their projected value — target these late.")
        show_list(sleepers(board), "Value", "value_gap")
    with t2:
        caption("Best first-year players by value over replacement.")
        show_list(top_rookies(board), "VOR", "vor")
    with t3:
        caption(
            "Scoring leans on TDs and long plays — exciting but week-to-week volatile."
        )
        show_list(boom_ceiling(board), "Boom", "boom_score")
    with t4:
        caption("High projected touch volume — the safest weekly floor.")
        show_list(high_floor(board), "Touches", "touches")

    # ---- Draft Grade ----
    st.markdown("<div class='sec-head'>Draft Grade</div>", unsafe_allow_html=True)
    grade = grade_draft(my_roster, STARTERS, BENCH_SPOTS)
    if grade is None:
        st.markdown(
            "<span class='rank-num'>Draft some players (mark them \"Mine\") to see your grade.</span>",
            unsafe_allow_html=True,
        )
    else:
        grade_colors = {
            "A": "#34d399",
            "B": "#38bdf8",
            "C": "#fbbf24",
            "D": "#fb923c",
            "F": "#f87171",
        }
        color = grade_colors.get(grade["letter"], "#94a3b8")
        g1, g2 = st.columns([1, 3], vertical_alignment="center")
        g1.markdown(
            f"<div style='font-size:3.5rem;font-weight:700;color:{color};"
            f"font-family:JetBrains Mono,monospace;text-align:center'>{grade['letter']}</div>"
            f"<div style='text-align:center;color:#9aa4b2;font-size:0.8rem'>{grade['score']}/100</div>",
            unsafe_allow_html=True,
        )
        details = (
            f"<span style='color:#ffffff'>Total value (VOR): <b>{grade['total_vor']}</b></span> &nbsp;·&nbsp; "
            f"<span style='color:#ffffff'>Avg per pick: <b>{grade['avg_vor']}</b></span><br>"
            f"<span style='color:#ffffff'>Starting slots filled: "
            f"<b>{grade['slots_filled']}/{grade['slots_total']}</b></span>"
        )
        if grade["missing"]:
            details += (
                f"<br><span style='color:#fb923c'>Still missing starters: "
                f"{', '.join(grade['missing'])}</span>"
            )
        g2.markdown(
            f"<div style='line-height:1.7'>{details}</div>", unsafe_allow_html=True
        )


# ==================== IN-SEASON MODE ====================
if mode == "📅 In-Season":
    # ---- Waiver Targets (live from ESPN) ----
    st.markdown(
        "<div class='sec-head'>Waiver Targets · Live</div>", unsafe_allow_html=True
    )

    if st.button("Load waiver targets", type="primary"):
        try:
            st.session_state.waivers = load_waivers()
        except Exception as e:
            st.session_state.waivers = None
            st.error(f"Couldn't reach ESPN: {e}")

    if st.session_state.get("waivers"):
        for i, t in enumerate(st.session_state.waivers[:25], start=1):
            c = st.columns([0.5, 3, 1.3, 1.6, 1.4], vertical_alignment="center")
            c[0].markdown(f"<span class='rank-num'>{i}</span>", unsafe_allow_html=True)
            name_html = f"<span style='color:#ffffff;font-weight:600;'>{t['name']}</span> <span class='rank-num'>{t['team']}</span>"
            if t["status"] != "ACTIVE":
                name_html += f" <span style='color:#fb923c;font-size:0.75rem'>⚠️ {t['status']}</span>"
            c[1].markdown(name_html, unsafe_allow_html=True)
            c[2].markdown(badge(t["position"]), unsafe_allow_html=True)
            c[3].markdown(
                f"<span class='mono'>proj {t['proj']}</span>", unsafe_allow_html=True
            )
            need = (
                "<span style='color:#34d399;font-size:0.75rem'>★ NEED</span>"
                if t["fills_need"]
                else ""
            )
            c[4].markdown(need, unsafe_allow_html=True)

    # ---- Start/Sit (coming after your draft) ----
    st.markdown("<div class='sec-head'>Start / Sit</div>", unsafe_allow_html=True)
    st.markdown(
        "<span class='rank-num'>Unlocks after your draft — compares your rostered "
        "players' weekly projections to set your lineup.</span>",
        unsafe_allow_html=True,
    )

    # ---- Trade Evaluator (coming after your draft) ----
    st.markdown("<div class='sec-head'>Trade Evaluator</div>", unsafe_allow_html=True)
    st.markdown(
        "<span class='rank-num'>Unlocks after your draft — weighs value on each "
        "side of a proposed trade.</span>",
        unsafe_allow_html=True,
    )
