import streamlit as st
from helpers import badge, espn_photo
from teams import TEAMS, get_my_roster
from teams import get_league_for
from helpers import badge
from teams import TEAMS, get_my_roster, get_league_for
from sleeper_proj import get_weekly_projections, _normalize
from helpers import badge
from collections import defaultdict
from config import POS_COLORS
import os


def render_season_mode(load_waivers):
    # ---- Team switcher ----
    st.markdown("<div class='sec-head'>Your Team</div>", unsafe_allow_html=True)
    labels = [t["label"] for t in TEAMS]
    chosen_label = st.radio(
        "Which team?",
        options=labels,
        horizontal=True,
        key="active_team",
        label_visibility="collapsed",
    )
    active_team = next(t for t in TEAMS if t["label"] == chosen_label)

    # ---- League Roster Overview (grid layout) ----
    st.markdown("<div class='sec-head'>League Rosters</div>", unsafe_allow_html=True)
    if st.button("Load all rosters"):
        with st.spinner("Loading league rosters..."):
            league = get_league_for(active_team)
            st.session_state.all_rosters = [
                {
                    "team": t.team_name,
                    "players": [
                        {"name": p.name, "position": p.position, "team": p.proTeam}
                        for p in t.roster
                    ],
                }
                for t in league.teams
            ]

    if st.session_state.get("all_rosters"):
        rosters = st.session_state.all_rosters
        cols_per_row = 3  # 3 teams across — change to 2 or 4 to taste

        # Render teams in rows of `cols_per_row`
        for row_start in range(0, len(rosters), cols_per_row):
            row_teams = rosters[row_start : row_start + cols_per_row]
            cols = st.columns(cols_per_row)
            for col, team in zip(cols, row_teams):
                with col:
                    st.markdown(
                        f"<div style='background:#0d1420;border:1px solid #1f2a3a;"
                        f"border-radius:8px;padding:10px;margin-bottom:8px'>"
                        f"<div style='color:#00e0a4;font-weight:700;font-size:0.85rem;"
                        f"border-bottom:1px solid #1f2a3a;padding-bottom:4px;margin-bottom:6px'>"
                        f"{team['team']}</div>"
                        + "".join(
                            f"<div style='font-size:0.72rem;margin:2px 0'>"
                            f"<span style='color:{POS_COLORS.get(p['position'], '#94a3b8')};"
                            f"font-weight:600'>{p['position']}</span> "
                            f"<span style='color:#ffffff'>{p['name']}</span> "
                            f"<span style='color:#4d5866'>{p['team']}</span></div>"
                            for p in team["players"]
                        )
                        + "</div>",
                        unsafe_allow_html=True,
                    )

    # ---- Sync roster ----
    if st.button("Sync roster from ESPN", type="primary"):
        with st.spinner(f"Loading {active_team['label']}..."):
            roster, _ = get_my_roster(active_team)
            st.session_state[f"roster_{chosen_label}"] = roster

    roster = st.session_state.get(f"roster_{chosen_label}")
    if roster:
        st.markdown(
            f"<div class='sec-head'>{chosen_label} · Roster</div>",
            unsafe_allow_html=True,
        )

        for p in roster:
            st.markdown(
                f"{badge(p['position'])} <span style='color:#ffffff'>{p['name']}</span> "
                f"<span class='rank-num'>{p['team']}</span>",
                unsafe_allow_html=True,
            )
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

    # ---- Start / Sit (ESPN + Sleeper consensus, FLEX-aware) ----
    st.markdown("<div class='sec-head'>Start / Sit</div>", unsafe_allow_html=True)

    if st.button("Get start/sit advice"):
        with st.spinner("Blending ESPN + Sleeper projections..."):
            league = get_league_for(active_team)
            wk = league.current_week
            sleeper_proj = get_weekly_projections(int(os.getenv("YEAR")), wk)

            team = next(
                (
                    t
                    for t in league.teams
                    if active_team["team_name"].lower() in t.team_name.lower()
                ),
                None,
            )
            lineup = []
            if team:
                for p in team.roster:
                    stats = getattr(p, "stats", {})
                    espn = None
                    if wk in stats and "projected_points" in stats[wk]:
                        espn = round(stats[wk]["projected_points"], 1)
                    slp = sleeper_proj.get(_normalize(p.name))

                    vals = [v for v in (espn, slp) if v is not None]
                    consensus = round(sum(vals) / len(vals), 1) if vals else 0
                    disagree = (
                        espn is not None and slp is not None and abs(espn - slp) >= 4
                    )

                    lineup.append(
                        {
                            "name": p.name,
                            "position": p.position,
                            "team": p.proTeam,
                            "espn": espn,
                            "sleeper": slp,
                            "consensus": consensus,
                            "disagree": disagree,
                            "status": getattr(p, "injuryStatus", "ACTIVE"),
                        }
                    )
            st.session_state.startsit = {"week": wk, "lineup": lineup}

    if st.session_state.get("startsit"):
        data = st.session_state.startsit
        st.markdown(
            f"<span class='mono'>Week {data['week']} · ESPN + Sleeper consensus</span>",
            unsafe_allow_html=True,
        )

        by_pos = defaultdict(list)
        for p in data["lineup"]:
            by_pos[p["position"]].append(p)

        starts = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "D/ST": 1}
        FLEX_POSITIONS = ("RB", "WR", "TE")
        position_order = ["QB", "RB", "WR", "TE", "K", "D/ST"]

        # Figure out the FLEX pick: best leftover RB/WR/TE after required starters
        flex_candidates = []
        for pos in position_order:
            players = sorted(
                by_pos.get(pos, []), key=lambda x: x["consensus"], reverse=True
            )
            n_start = starts.get(pos, 1)
            for i, p in enumerate(players):
                if i >= n_start and pos in FLEX_POSITIONS:
                    flex_candidates.append(p)
        flex_pick = (
            max(flex_candidates, key=lambda x: x["consensus"])
            if flex_candidates
            else None
        )

        def render_player(p, verdict_html):
            inj = (
                f" <span style='color:#fb923c;font-size:0.7rem'>⚠️{p['status']}</span>"
                if p["status"] != "ACTIVE"
                else ""
            )
            split = (
                " <span style='color:#fbbf24;font-size:0.7rem'>⚡ split</span>"
                if p["disagree"]
                else ""
            )
            espn_txt = p["espn"] if p["espn"] is not None else "—"
            slp_txt = p["sleeper"] if p["sleeper"] is not None else "—"
            st.markdown(
                f"{badge(p['position'])} <span style='color:#ffffff'>{p['name']}</span> "
                f"<span class='rank-num'>{p['team']}</span> · "
                f"<span class='mono'>{p['consensus']} pts</span> "
                f"<span class='rank-num'>(ESPN {espn_txt} · Slp {slp_txt})</span> · "
                f"{verdict_html}{split}{inj}",
                unsafe_allow_html=True,
            )

        for pos in position_order:
            players = sorted(
                by_pos.get(pos, []), key=lambda x: x["consensus"], reverse=True
            )
            if not players:
                continue
            st.markdown(
                f"<div style='margin-top:10px;color:#00e0a4;font-size:0.8rem'>{pos}</div>",
                unsafe_allow_html=True,
            )
            n_start = starts.get(pos, 1)
            for i, p in enumerate(players):
                if i < n_start:
                    verdict = "<span style='color:#34d399;font-weight:700'>START</span>"
                elif flex_pick and p["name"] == flex_pick["name"]:
                    verdict = "<span style='color:#38bdf8;font-weight:700'>FLEX</span>"
                else:
                    verdict = "<span style='color:#7d8590'>bench</span>"
                render_player(p, verdict)

    # ---- Trade Evaluator ----
    st.markdown("<div class='sec-head'>Trade Evaluator</div>", unsafe_allow_html=True)
    from trades import evaluate_trade, recommend_trade

    if not st.session_state.get("all_rosters"):
        st.markdown(
            "<span class='rank-num'>Click 'Load all rosters' above first.</span>",
            unsafe_allow_html=True,
        )
    else:
        rosters = st.session_state.all_rosters
        my_team_name = active_team["team_name"]
        my_roster = next(
            (
                r["players"]
                for r in rosters
                if my_team_name.lower() in r["team"].lower()
            ),
            [],
        )
        other_teams = [
            r for r in rosters if my_team_name.lower() not in r["team"].lower()
        ]

        if other_teams:
            partner_name = st.selectbox(
                "Trade with which team?",
                options=[r["team"] for r in other_teams],
                key="trade_partner",
            )
            partner = next(r for r in other_teams if r["team"] == partner_name)
            # --- Scan ALL teams for the best trade opportunities ---
            st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
            st.markdown(
                "<div class='sec-head'>Best Trade Targets · League-Wide</div>",
                unsafe_allow_html=True,
            )
            if st.button("Scan all teams for trades"):
                from trades import scan_all_teams

                st.session_state.all_trade_opps = scan_all_teams(
                    my_roster, rosters, my_team_name
                )

            if st.session_state.get("all_trade_opps") is not None:
                opps = st.session_state.all_trade_opps
                if not opps:
                    st.markdown(
                        "<span class='rank-num'>No mutually-beneficial trades found across "
                        "the league right now — your roster is balanced, or no one's needs "
                        "line up with yours.</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<span class='mono'>Found {len(opps)} opportunities "
                        f"(most balanced first):</span>",
                        unsafe_allow_html=True,
                    )
                    for o in opps[:8]:
                        fair_color = (
                            "#34d399"
                            if o["fairness"] <= 8
                            else "#fbbf24"
                            if o["fairness"] <= 20
                            else "#f87171"
                        )
                        fair_label = (
                            "Fair"
                            if o["fairness"] <= 8
                            else "Slightly uneven"
                            if o["fairness"] <= 20
                            else "Uneven"
                        )
                        st.markdown(
                            f"<div style='background:#0d1420;border-left:3px solid {fair_color};"
                            f"border-radius:8px;padding:10px;margin:6px 0'>"
                            f"<span style='color:#00e0a4;font-weight:700;font-size:0.8rem'>"
                            f"with {o['team']}</span><br>"
                            f"<span style='color:#ffffff'>Give <b>{o['give']}</b> "
                            f"({o['give_pos']}, {o['give_vor']} VOR)</span><br>"
                            f"<span style='color:#ffffff'>Get <b>{o['get']}</b> "
                            f"({o['get_pos']}, {o['get_vor']} VOR)</span><br>"
                            f"<span style='color:{fair_color};font-size:0.78rem'>{fair_label} "
                            f"(net {o['diff']:+} VOR)</span></div>",
                            unsafe_allow_html=True,
                        )

            # --- Manual trade builder ---
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(
                    "<span class='mono'>You give:</span>", unsafe_allow_html=True
                )
                give = st.multiselect(
                    "Give",
                    options=[p["name"] for p in my_roster],
                    label_visibility="collapsed",
                    key="trade_give",
                )
            with c2:
                st.markdown(
                    "<span class='mono'>You get:</span>", unsafe_allow_html=True
                )
                get = st.multiselect(
                    "Get",
                    options=[p["name"] for p in partner["players"]],
                    label_visibility="collapsed",
                    key="trade_get",
                )

            if give or get:
                result = evaluate_trade(give, get)
                color = (
                    "#34d399"
                    if result["diff"] > 5
                    else "#f87171"
                    if result["diff"] < -5
                    else "#fbbf24"
                )
                st.markdown(
                    f"<div style='background:#0d1420;border-left:3px solid {color};"
                    f"border-radius:8px;padding:12px;margin-top:8px'>"
                    f"<span style='color:{color};font-weight:700'>{result['verdict']}</span> "
                    f"<span class='mono'>(net VOR {result['diff']:+})</span><br>"
                    f"<span class='rank-num'>You give {result['give_vor']} VOR · "
                    f"You get {result['get_vor']} VOR</span></div>",
                    unsafe_allow_html=True,
                )

            # --- Trade recommendations for this team ---
            st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
            if st.button(f"Suggest trades with {partner_name}"):
                st.session_state.trade_recs = recommend_trade(
                    my_roster, partner["players"]
                )

            if st.session_state.get("trade_recs") is not None:
                recs = st.session_state.trade_recs
                if not recs:
                    st.markdown(
                        "<span class='rank-num'>No clear mutually-beneficial trade found — "
                        "your needs and theirs don't line up right now.</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        "<span class='mono'>Suggested trades (most balanced first):</span>",
                        unsafe_allow_html=True,
                    )
                    for r in recs[:3]:
                        fair_color = (
                            "#34d399"
                            if r["fairness"] <= 8
                            else "#fbbf24"
                            if r["fairness"] <= 20
                            else "#f87171"
                        )
                        fair_label = (
                            "Fair"
                            if r["fairness"] <= 8
                            else "Slightly uneven"
                            if r["fairness"] <= 20
                            else "Uneven"
                        )
                        st.markdown(
                            f"<div style='background:#0d1420;border-left:3px solid {fair_color};"
                            f"border-radius:8px;padding:10px;margin:6px 0'>"
                            f"<span style='color:#ffffff'>Give <b>{r['give']}</b> "
                            f"({r['give_pos']}, {r['give_vor']} VOR)</span><br>"
                            f"<span style='color:#ffffff'>Get <b>{r['get']}</b> "
                            f"({r['get_pos']}, {r['get_vor']} VOR)</span><br>"
                            f"<span style='color:{fair_color};font-size:0.78rem'>{fair_label} "
                            f"(net {r['diff']:+} VOR)</span></div>",
                            unsafe_allow_html=True,
                        )

    # ---- Matchup Preview (WWE style) ----
    st.markdown("<div class='sec-head'>⚔️ Matchup Preview</div>", unsafe_allow_html=True)
    if not st.session_state.get("all_rosters"):
        st.markdown(
            "<span class='rank-num'>Click 'Load all rosters' above first.</span>",
            unsafe_allow_html=True,
        )
    else:
        rosters = st.session_state.all_rosters
        team_names = [r["team"] for r in rosters]
        mc1, mc2 = st.columns(2)
        with mc1:
            team_a = st.selectbox("Team 1", options=team_names, key="preview_a")
        with mc2:
            team_b = st.selectbox(
                "Team 2",
                options=team_names,
                index=min(1, len(team_names) - 1),
                key="preview_b",
            )

        if st.button("🎤 Hype the matchup!") and team_a != team_b:
            from news import matchup_preview

            a = next(r for r in rosters if r["team"] == team_a)
            b = next(r for r in rosters if r["team"] == team_b)
            with st.spinner("Building the hype..."):
                st.session_state.preview = matchup_preview(
                    team_a, a["players"], team_b, b["players"]
                )

        if st.session_state.get("preview"):
            st.markdown(
                f"<div style='background:linear-gradient(90deg,rgba(0,224,164,0.1),"
                f"rgba(248,113,113,0.1));border-radius:10px;padding:16px;"
                f"font-size:0.95rem;line-height:1.6;color:#ffffff'>"
                f"{st.session_state.preview}</div>",
                unsafe_allow_html=True,
            )
    # ---- Player Stat History (from the database) ----
    st.markdown(
        "<div class='sec-head'>Player Stat History</div>", unsafe_allow_html=True
    )

    stat_name = st.text_input(
        "Look up historical game stats",
        placeholder="e.g. Bijan Robinson",
        key="stat_lookup",
    )
    if stat_name:
        rows = get_player_stats(stat_name)
        if rows:
            # Quick summary above the table
            seasons = sorted({r["season"] for r in rows})
            avg_snap = round(
                sum(r["snap_share"] or 0 for r in rows) / len(rows) * 100, 1
            )
            avg_tgt = round(
                sum(r["target_share"] or 0 for r in rows) / len(rows) * 100, 1
            )
            st.markdown(
                f"<span class='mono'>{len(rows)} games · {', '.join(map(str, seasons))} · "
                f"avg snap {avg_snap}% · avg target share {avg_tgt}%</span>",
                unsafe_allow_html=True,
            )
            st.dataframe(rows, use_container_width=True)
        else:
            st.markdown(
                f"<span class='rank-num'>No stats found for '{stat_name}' — "
                f"check spelling (first + last name).</span>",
                unsafe_allow_html=True,
            )
