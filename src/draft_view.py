import streamlit as st
from config import STARTERS, BENCH_SPOTS, SCORING_LABELS, TOP_N
from helpers import badge, sleeper_photo, player_key
from categories import sleepers, top_rookies, boom_ceiling, high_floor
from grader import grade_draft
from player_tags import get_tags, TAG_STYLES


def render_draft_mode(board, available, my_roster, needs, adjusted_score, draft_player):
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
        tier_counts = {}
        for p in pos_avail:
            t = p.get("tier", "?")
            tier_counts[t] = tier_counts.get(t, 0) + 1
        lines = ""
        for t in sorted(k for k in tier_counts if isinstance(k, int))[:3]:
            n = tier_counts[t]
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
    my_qb_teams = {p["team"] for p in my_roster if p["position"] == "QB"}
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
        if is_stack(p):
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
