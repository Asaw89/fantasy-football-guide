import streamlit as st
from collections import Counter
from draft_board import build_board, NUM_TEAMS

st.set_page_config(page_title="Draft Command Center", page_icon="🏈", layout="wide")

# ---- Config ----
STARTERS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}
NEED_BONUS = 20.0
TOP_N = 30

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
.stButton > button { border-radius:8px; border:1px solid #2a3a4f; font-family:'Chakra Petch',sans-serif; letter-spacing:1px; font-weight:600; transition:all .15s ease; }
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
def load_board():
    return build_board()


def player_key(p):
    return f"{p['name']}|{p['team']}|{p['position']}"


if "drafted" not in st.session_state:
    st.session_state.drafted = set()
if "my_roster" not in st.session_state:
    st.session_state.my_roster = []


def draft_player(p, mine):
    st.session_state.drafted.add(player_key(p))
    if mine:
        st.session_state.my_roster.append(p)


def reset_draft():
    st.session_state.drafted = set()
    st.session_state.my_roster = []


board = load_board()
my_roster = st.session_state.my_roster
available = [p for p in board if player_key(p) not in st.session_state.drafted]
available.sort(key=lambda p: p["vor"], reverse=True)

counts = Counter(p["position"] for p in my_roster)
needs = {pos: max(0, STARTERS[pos] - counts.get(pos, 0)) for pos in STARTERS}


def adjusted_score(p):
    bonus = NEED_BONUS if needs.get(p["position"], 0) > 0 else 0
    return p["vor"] + bonus


# ---- Header ----
st.markdown(
    "<div class='cc-title'>🏈 Draft <span class='accent'>Command Center</span></div>"
    "<div class='cc-sub'>Value-based rankings · live board</div>",
    unsafe_allow_html=True,
)

picks_made = len(st.session_state.drafted)
round_num = picks_made // NUM_TEAMS + 1
pick_in_round = picks_made % NUM_TEAMS + 1


def stat_card(label, value):
    return f"<div class='stat-card'><div class='stat-val'>{value}</div><div class='stat-lbl'>{label}</div></div>"


m1, m2, m3 = st.columns(3)
m1.markdown(
    stat_card("Round · Pick", f"{round_num} · {pick_in_round}"), unsafe_allow_html=True
)
m2.markdown(stat_card("Overall Picks", picks_made), unsafe_allow_html=True)
m3.markdown(stat_card("Your Roster", len(my_roster)), unsafe_allow_html=True)

# ---- Sidebar ----
with st.sidebar:
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
    st.divider()
    st.button("Reset draft", on_click=reset_draft, use_container_width=True)

# ---- Recommendation ----
if available:
    pick = max(available, key=adjusted_score)
    fills = needs.get(pick["position"], 0) > 0
    reason = (
        f"fills a need at {pick['position']}" if fills else "best value on the board"
    )
    st.markdown(
        f"""
    <div class='rec-panel'>
      <div class='rec-label'>Recommended Pick</div>
      <div class='rec-name'>{pick["name"]} &nbsp; {badge(pick["position"], pick.get("tier", ""))}</div>
      <div class='rec-meta'>{reason} · PROJ {pick["points"]} · VOR {pick["vor"]}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ---- Board ----
st.markdown("<div class='sec-head'>Best Available</div>", unsafe_allow_html=True)
for i, p in enumerate(available[:TOP_N], start=1):
    key = player_key(p)
    c = st.columns([0.5, 3.2, 1.3, 1.8, 1, 1], vertical_alignment="center")
    c[0].markdown(f"<span class='rank-num'>{i:>2}</span>", unsafe_allow_html=True)
    c[1].markdown(
        f"<span style='color:#ffffff;font-weight:600;'>{p['name']}</span> "
        f"<span class='rank-num'>{p['team']}</span>",
        unsafe_allow_html=True,
    )
    c[2].markdown(badge(p["position"], p.get("tier", "")), unsafe_allow_html=True)
    c[3].markdown(
        f"<span class='mono'>{p['points']} / {p['vor']}</span>", unsafe_allow_html=True
    )
    c[4].button(
        "Mine",
        key=f"mine_{key}",
        on_click=draft_player,
        args=(p, True),
        type="primary",
        use_container_width=True,
    )
    c[5].button(
        "Taken",
        key=f"taken_{key}",
        on_click=draft_player,
        args=(p, False),
        use_container_width=True,
    )
