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


# ==================== SIDEBAR ====================

with st.sidebar:
    # ---- Mode toggle (top) ----
    st.markdown("<div class='sec-head'>Mode</div>", unsafe_allow_html=True)
    mode = st.radio(
        "App mode",
        options=["Draft", "In-Season"],
        label_visibility="collapsed",
        key="app_mode",
    )
    st.divider()

    # ---- Top Stories (fetched once, stored in session) ----
    with st.expander("📰 The Latest", expanded=False):
        if "top_stories" not in st.session_state:
            if st.button("Load latest news"):
                with st.spinner("Fetching..."):
                    st.session_state.top_stories = load_top_stories(())
        if st.session_state.get("top_stories"):
            for s in st.session_state.top_stories:
                st.markdown(
                    f"<div style='margin-bottom:8px'>"
                    f"<span style='color:#00e0a4;font-size:0.72rem'>{s['player']}</span><br>"
                    f"<span style='color:#ffffff;font-size:0.85rem'>{s['headline']}</span></div>",
                    unsafe_allow_html=True,
                )

    # Build a stable, hashable key from the current roster
    roster_names = tuple(sorted(p["name"] for p in my_roster))
    label = "📰 Your Players" if roster_names else "📰 The Latest"

    # ---- Player Search ----
    st.markdown("<div class='sec-head'>Player Search</div>", unsafe_allow_html=True)
    news_options = {f"{p['name']} · {p['position']} {p['team']}": p for p in board}
    choice = st.selectbox(
        "Find a player", options=list(news_options.keys()), label_visibility="collapsed"
    )
    if st.button("Get news", type="primary", use_container_width=True):
        picked = news_options[choice]
        with st.spinner(f"Searching outlets for {picked['name']}..."):
            result = cached_news(picked["name"], picked["team"], picked["position"])
            st.session_state.news_summary = result["summary"]
            st.session_state.news_sources = result.get("sources", {})
            st.session_state.news_player = picked["name"]
            st.session_state.news_photo = sleeper_photo(picked.get("player_id"))

    # News result — directly under Player Search
    if st.session_state.get("news_summary"):
        with st.expander(
            f"📰 News: {st.session_state.get('news_player', '')}", expanded=True
        ):
            if st.session_state.get("news_photo"):
                st.image(st.session_state.news_photo, width=70)
            st.markdown(
                f"<div style='color:#ffffff;'>{st.session_state.news_summary}</div>",
                unsafe_allow_html=True,
            )
            sources = st.session_state.get("news_sources", {})
            if sources:
                st.markdown(
                    "<div style='color:#7d8590;font-size:0.7rem;margin-top:8px;"
                    "text-transform:uppercase;letter-spacing:1px'>Sources</div>",
                    unsafe_allow_html=True,
                )
                for url, title in sources.items():
                    short = title[:40] + "…" if len(title) > 40 else title
                    st.markdown(
                        f"<a href='{url}' target='_blank' "
                        f"style='color:#38bdf8;font-size:0.78rem'>{short}</a>",
                        unsafe_allow_html=True,
                    )

    # ---- Ask the Analyst ----
    st.markdown("<div class='sec-head'>Ask the Analyst</div>", unsafe_allow_html=True)
    user_q = st.text_input(
        "Ask a fantasy question",
        label_visibility="collapsed",
        placeholder="e.g. Should I start my WR2 this week?",
    )
    if st.button("Ask", use_container_width=True) and user_q:
        from news import ask_question

        picks_made = len(st.session_state.drafted)
        size = st.session_state.get("league_size", 10)
        with st.spinner("Thinking..."):
            st.session_state.answer = ask_question(
                user_q,
                league_size=size,
                scoring=st.session_state.get("scoring", "PPR"),
                my_roster=st.session_state.my_roster,
                taken=st.session_state.drafted,
                round_num=picks_made // size + 1,
                pick_in_round=picks_made % size + 1,
            )

    # Analyst answer — directly under Ask the Analyst
    if st.session_state.get("answer"):
        with st.expander("💬 Analyst answer", expanded=True):
            st.markdown(
                f"<div style='color:#ffffff;'>{st.session_state.answer}</div>",
                unsafe_allow_html=True,
            )
    # ---- Draft-only sidebar sections ----
    if mode == "Draft":
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
        # ---- Positional Strengths ----
        # A position is a "strength" if you have surplus depth AND good value there
        strengths = []
        for pos in STARTERS:
            pos_players = [p for p in my_roster if p["position"] == pos]
            surplus = len(pos_players) - STARTERS[pos]  # extra beyond starters
            pos_vor = sum(p.get("vor", 0) for p in pos_players)
            # Strong if you have at least one extra AND meaningful total value
            if surplus >= 1 and pos_vor > 100:
                strengths.append((pos, len(pos_players), round(pos_vor)))

        if strengths:
            st.markdown("<div class='sec-head'>Strengths</div>", unsafe_allow_html=True)
            for pos, count, vor in strengths:
                st.markdown(
                    f"{badge(pos)} <span style='color:#34d399;font-size:0.8rem'>"
                    f"{count} deep · strong ({vor} VOR)</span>",
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
        photo = sleeper_photo(pick.get("player_id"))
        rc1, rc2 = st.columns([1, 6], vertical_alignment="center")
        if photo:
            rc1.image(photo, width=80)
        rc2.markdown(
            f"<div class='rec-panel'><div class='rec-label'>Recommended Pick</div>"
            f"<div class='rec-name'>{pick['name']} &nbsp; {badge(pick['position'], pick.get('tier', ''))}</div>"
            f"<div class='rec-meta'>{reason} · PROJ {pick['points']} · VOR {pick['vor']}</div></div>",
            unsafe_allow_html=True,
        )
        # ---- Quick Entry (fast pick marking for live drafts) ----
    st.markdown("<div class='sec-head'>Quick Entry</div>", unsafe_allow_html=True)
    qcol1, qcol2, qcol3 = st.columns([3, 1, 1])
    with qcol1:
        quick_name = st.text_input(
            "Quick mark",
            label_visibility="collapsed",
            placeholder="Type a player name…",
            key="quick_entry",
        )

    def quick_mark(mine):
        typed = st.session_state.quick_entry.strip().lower()
        if not typed:
            return
        # Find undrafted players whose name contains what you typed
        matches = [p for p in available if typed in p["name"].lower()]
        if len(matches) == 1:
            draft_player(matches[0], mine)
            st.session_state.quick_msg = (
                f"✓ {'Drafted' if mine else 'Marked taken'}: {matches[0]['name']}"
            )
            st.session_state.quick_entry = ""
        elif len(matches) == 0:
            st.session_state.quick_msg = f"⚠️ No match for '{typed}'"
        else:
            names = ", ".join(m["name"] for m in matches[:5])
            st.session_state.quick_msg = (
                f"⚠️ Multiple matches — be more specific: {names}"
            )

    qcol2.button(
        "Mine",
        key="quick_mine",
        on_click=quick_mark,
        args=(True,),
        type="primary",
        use_container_width=True,
    )
    qcol3.button(
        "Taken",
        key="quick_taken",
        on_click=quick_mark,
        args=(False,),
        use_container_width=True,
    )

    if st.session_state.get("quick_msg"):
        color = "#34d399" if st.session_state.quick_msg.startswith("✓") else "#fb923c"
        st.markdown(
            f"<span style='color:{color};font-size:0.85rem'>{st.session_state.quick_msg}</span>",
            unsafe_allow_html=True,
        )

        # ---- Positional Scarcity (tiers remaining) ----
    st.markdown(
        "<div class='sec-head'>Position Scarcity · Tiers Left</div>",
        unsafe_allow_html=True,
    )

    scarcity_cols = st.columns(6)
    for col, pos in zip(scarcity_cols, ["QB", "RB", "WR", "TE", "K", "DEF"]):
        pos_avail = [p for p in available if p["position"] == pos]
        # Count how many remain in each within-position tier
        tier_counts = {}
        for p in pos_avail:
            t = p.get("tier", "?")
            tier_counts[t] = tier_counts.get(t, 0) + 1

        # Build a small readout, top 3 tiers
        lines = ""
        for t in sorted(k for k in tier_counts if isinstance(k, int))[:3]:
            n = tier_counts[t]
            # Warn (orange) when a top tier is nearly gone
            warn = n <= 2 and t <= 2
            color = "#fb923c" if warn else "#9aa4b2"
            flag = " ⚠️" if warn else ""
            lines += (
                f"<div style='color:{color};font-size:0.72rem'>T{t}: {n}{flag}</div>"
            )

        col.markdown(
            f"<div style='text-align:center'>{badge(pos)}</div>{lines}",
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

    sort_by = st.radio(
        "Sort by",
        options=["VOR", "Consensus", "ESPN", "Berry"],
        horizontal=True,
        key="sort_by",
    )

    if st.session_state.pos_filter == "All":
        shown = list(available)
    else:
        shown = [p for p in available if p["position"] == st.session_state.pos_filter]

    if sort_by == "VOR":
        shown.sort(key=lambda p: p.get("vor", 0), reverse=True)
    elif sort_by == "Consensus":
        shown.sort(key=lambda p: p.get("consensus") or 9999)
    elif sort_by == "ESPN":
        shown.sort(key=lambda p: p.get("espn_rank") or 9999)
    elif sort_by == "Berry":
        shown.sort(key=lambda p: p.get("berry_rank") or 9999)
    st.markdown(
        f"<div style='color:#9aa4b2;font-size:0.85rem;margin:6px 0'>"
        f"Showing {min(len(shown), TOP_N)} of {len(shown)} available"
        f"{'' if st.session_state.pos_filter == 'All' else ' ' + st.session_state.pos_filter}"
        f"</div>",
        unsafe_allow_html=True,
    )
    # ---- Tag filter ----
    tag_filter = st.radio(
        "Show tagged",
        options=["All players", "⭐ Ride or Die", "📈 Breakout", "💎 Value"],
        horizontal=True,
        key="tag_filter",
    )

    tag_map = {
        "⭐ Ride or Die": "ride_or_die",
        "📈 Breakout": "breakout",
        "💎 Value": "value",
    }
    if tag_filter in tag_map:
        from player_tags import get_tags

        wanted = tag_map[tag_filter]
        shown = [p for p in shown if wanted in get_tags(p["name"])]

    # ---- Injury filter ----
    injury_filter = st.radio(
        "Injuries",
        options=["Show all", "Healthy", "Injured"],
        horizontal=True,
        key="injury_filter",
    )
    INJURED = {"IR", "PUP", "Out", "OUT", "NA", "Questionable"}
    if injury_filter == "Healthy":
        shown = [p for p in shown if p.get("injury_status") not in INJURED]
    elif injury_filter == "Injured":
        shown = [p for p in shown if p.get("injury_status") in INJURED]

    # ---- Stack detection ----
    # Teams where you have a QB → highlight available WR/TE on those teams
    my_qb_teams = {p["team"] for p in my_roster if p["position"] == "QB"}
    # Teams where you have a WR/TE → highlight available QB on those teams
    my_pass_catcher_teams = {
        p["team"] for p in my_roster if p["position"] in ("WR", "TE")
    }

    def is_stack(p):
        if p["position"] in ("WR", "TE") and p["team"] in my_qb_teams:
            return True
        if p["position"] == "QB" and p["team"] in my_pass_catcher_teams:
            return True
        return False

    last_tier = None
    for i, p in enumerate(shown[:TOP_N], start=1):
        if st.session_state.pos_filter == "All":
            this_tier = p.get("global_tier")
            tier_label = f"Tier {this_tier}"
        else:
            this_tier = p.get("tier")
            tier_label = f"{st.session_state.pos_filter} · Tier {this_tier}"

        if sort_by == "VOR" and this_tier != last_tier:
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

        tag_html = ""
        for t in get_tags(p["name"]):
            style = TAG_STYLES[t]
            tag_html += (
                f" <span style='background:{style['color']}22;"
                f"color:{style['color']};border:1px solid {style['color']}66;"
                f"font-size:0.62rem;font-weight:700;border-radius:4px;"
                f"padding:1px 5px;margin-left:3px'>{style['label']}</span>"
            )
        stack_tag = ""
        if is_stack(p):
            # Highlighted stack row: tinted background, glowing border, bold tag
            c[1].markdown(
                f"<div style='background:rgba(0,224,164,0.12);border-left:3px solid #00e0a4;"
                f"border-radius:6px;padding:4px 10px;'>"
                f"<span style='color:#ffffff;font-weight:700;'>{p['name']}</span> "
                f"<span class='rank-num'>{p['team']}</span> "
                f"<span style='background:#00e0a4;color:#0b0f17;font-size:0.68rem;"
                f"font-weight:700;border-radius:4px;padding:1px 6px;margin-left:4px'>"
                f"🔗 STACK</span></div>",
                unsafe_allow_html=True,
            )
        else:
            c[1].markdown(
                f"<span style='color:#ffffff;font-weight:600;'>{p['name']}</span> "
                f"<span class='rank-num'>{p['team']}</span>{tag_html}",
                unsafe_allow_html=True,
            )
        injury_flag = ""
        inj = p.get("injury_status")
        if inj and inj not in ("ACTIVE", None):
            # Color by severity — red for serious, orange for questionable
            color = "#f87171" if inj in ("IR", "PUP", "Out", "OUT", "NA") else "#e8fb3c"
            injury_flag = (
                f" <span style='background:{color}22;color:{color};"
                f"border:1px solid {color}66;font-size:0.62rem;font-weight:700;"
                f"border-radius:4px;padding:1px 5px'>⚕️ {inj}</span>"
            )
        c[2].markdown(badge(p["position"], p.get("tier", "")), unsafe_allow_html=True)
        bye_txt = f" · Bye {p['bye']}" if p.get("bye") else ""
        ranks_txt = ""
        if p.get("sleeper_rank"):
            ranks_txt += f" · Sleeper #{p['sleeper_rank']}"
        if p.get("espn_rank"):
            ranks_txt += f" · ESPN #{p['espn_rank']}"
        if p.get("berry_rank"):
            ranks_txt += f" · Berry #{p['berry_rank']}"
        split = ""
        if p.get("disagreement"):
            split = (
                f" <span style='color:#fbbf24;font-size:0.7rem'>"
                f"⚡ SPLIT ({p.get('rank_spread')})</span>"
            )
        value_flag = ""
        gap = p.get("value_gap", 0)
        if gap >= 12:
            value_flag = (
                f" <span style='background:#34d39922;color:#34d399;"
                f"border:1px solid #34d39966;font-size:0.62rem;font-weight:700;"
                f"border-radius:4px;padding:1px 5px'>💎 VALUE +{gap}</span>"
            )
        elif gap <= -12:
            value_flag = (
                f" <span style='background:#f8717122;color:#f87171;"
                f"border:1px solid #f8717166;font-size:0.62rem;font-weight:700;"
                f"border-radius:4px;padding:1px 5px'>⚠️ REACH {gap}</span>"
            )
        c[3].markdown(
            f"<span class='mono'>{p['points']} / {p['vor']}"
            f"<span class='rank-num'>{bye_txt}{ranks_txt}</span></span>{split}{value_flag}{injury_flag}",
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
if mode == "In-Season":
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
            c = st.columns([0.4, 0.7, 3, 1.3, 1.6, 1.4], vertical_alignment="center")
            c[0].markdown(f"<span class='rank-num'>{i}</span>", unsafe_allow_html=True)
            photo = espn_photo(t.get("player_id"))
            if photo:
                c[1].image(photo, width=45)
            name_html = f"<span style='color:#ffffff;font-weight:600;'>{t['name']}</span> <span class='rank-num'>{t['team']}</span>"
            if t["status"] != "ACTIVE":
                name_html += f" <span style='color:#fb923c;font-size:0.75rem'>⚠️ {t['status']}</span>"
            c[2].markdown(name_html, unsafe_allow_html=True)
            c[3].markdown(badge(t["position"]), unsafe_allow_html=True)
            c[4].markdown(
                f"<span class='mono'>proj {t['proj']}</span>", unsafe_allow_html=True
            )
            need = (
                "<span style='color:#34d399;font-size:0.75rem'>★ NEED</span>"
                if t["fills_need"]
                else ""
            )
            c[5].markdown(need, unsafe_allow_html=True)

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
