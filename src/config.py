import streamlit as st

# ---- Config ----
STARTERS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}
BENCH_SPOTS = 8
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


def inject_css():
    """Inject the app's custom CSS. Call once near the top of the app."""
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
