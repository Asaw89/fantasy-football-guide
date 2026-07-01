import streamlit as st
from collections import Counter
from draft_board import build_board

# ---- Config ----
STARTERS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}
NEED_BONUS = 20.0  # nudge toward positions you still need to fill
TOP_N = 30  # how many available players to show at once


# Load the board once and cache it, so we don't re-hit Sleeper on every click
@st.cache_data(show_spinner="Loading projections from Sleeper...")
def load_board():
    return build_board()


def player_key(p):
    return f"{p['name']}|{p['team']}|{p['position']}"


# ---- Session state: what's drafted, and who's on my team ----
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

# Available = everyone not yet drafted, best value first
available = [p for p in board if player_key(p) not in st.session_state.drafted]
available.sort(key=lambda p: p["vor"], reverse=True)

# ---- Roster counts and needs ----
counts = Counter(p["position"] for p in my_roster)
needs = {pos: max(0, STARTERS[pos] - counts.get(pos, 0)) for pos in STARTERS}


def adjusted_score(p):
    bonus = NEED_BONUS if needs.get(p["position"], 0) > 0 else 0
    return p["vor"] + bonus


# ================= UI =================
st.title("🏈 Draft Assistant")

with st.sidebar:
    st.header("My Roster")
    if my_roster:
        for p in my_roster:
            st.write(f"{p['position']} — {p['name']} ({p['team']})")
    else:
        st.write("_No picks yet_")

    st.subheader("Still need")
    need_labels = [f"{pos} x{n}" for pos, n in needs.items() if n > 0]
    st.write(", ".join(need_labels) if need_labels else "Starters filled")

    st.divider()
    st.button("Reset draft", on_click=reset_draft)

# --- Recommendation ---
if available:
    pick = max(available, key=adjusted_score)
    fills_need = needs.get(pick["position"], 0) > 0
    reason = (
        f"fills a roster need at {pick['position']}"
        if fills_need
        else "best value on the board"
    )
    st.success(
        f"**Recommended pick: {pick['name']} "
        f"({pick['position']}, {pick['team']})** — {reason}. "
        f"Projected {pick['points']}, VOR {pick['vor']}."
    )

# --- Available board with action buttons ---
st.subheader("Best available")

header = st.columns([0.5, 3, 1.5, 2, 1.2, 1.2])
for col, label in zip(header, ["#", "Player", "Pos", "Proj / VOR", "", ""]):
    col.markdown(f"**{label}**")

for i, p in enumerate(available[:TOP_N], start=1):
    key = player_key(p)
    c = st.columns([0.5, 3, 1.5, 2, 1.2, 1.2])
    c[0].write(i)
    c[1].write(f"{p['name']} ({p['team']})")
    c[2].write(f"{p['position']}{p.get('tier', '')}")
    c[3].write(f"{p['points']} / {p['vor']}")
    c[4].button("Mine", key=f"mine_{key}", on_click=draft_player, args=(p, True))
    c[5].button("Taken", key=f"taken_{key}", on_click=draft_player, args=(p, False))
