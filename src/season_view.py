import streamlit as st
from helpers import badge, espn_photo
from teams import TEAMS, get_my_roster
from teams import get_league_for
from helpers import badge


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

    # ---- League Roster Overview ----
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
        from helpers import badge

        for team in st.session_state.all_rosters:
            with st.expander(f"🏈 {team['team']} ({len(team['players'])} players)"):
                for p in team["players"]:
                    st.markdown(
                        f"{badge(p['position'])} <span style='color:#ffffff'>{p['name']}</span> "
                        f"<span class='rank-num'>{p['team']}</span>",
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
        from helpers import badge

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

    # ---- Start / Sit (ESPN + Sleeper consensus) ----
    st.markdown("<div class='sec-head'>Start / Sit</div>", unsafe_allow_html=True)

    if st.button("Get start/sit advice"):
        from teams import get_league_for
        from sleeper_proj import get_weekly_projections, _normalize

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

                    # Consensus = average of whatever sources we have
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
        from helpers import badge
        from collections import defaultdict

        data = st.session_state.startsit
        st.markdown(
            f"<span class='mono'>Week {data['week']} · ESPN + Sleeper consensus</span>",
            unsafe_allow_html=True,
        )

        by_pos = defaultdict(list)
        for p in data["lineup"]:
            by_pos[p["position"]].append(p)

        starts = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "D/ST": 1}
        for pos in ["QB", "RB", "WR", "TE", "K", "D/ST"]:
            players = sorted(
                by_pos.get(pos, []), key=lambda x: x["consensus"], reverse=True
            )
            if not players:
                continue
            n_start = starts.get(pos, 1)
            st.markdown(
                f"<div style='margin-top:10px;color:#00e0a4;font-size:0.8rem'>{pos}</div>",
                unsafe_allow_html=True,
            )
            for i, p in enumerate(players):
                verdict = (
                    "<span style='color:#34d399;font-weight:700'>START</span>"
                    if i < n_start
                    else "<span style='color:#7d8590'>bench</span>"
                )
                inj = (
                    f" <span style='color:#fb923c;font-size:0.7rem'>⚠️{p['status']}</span>"
                    if p["status"] != "ACTIVE"
                    else ""
                )
                split = (
                    " <span style='color:#fbbf24;font-size:0.7rem'>⚡ sources split</span>"
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
                    f"{verdict}{split}{inj}",
                    unsafe_allow_html=True,
                )

    # ---- Trade Evaluator (coming after your draft) ----
    st.markdown("<div class='sec-head'>Trade Evaluator</div>", unsafe_allow_html=True)
    st.markdown(
        "<span class='rank-num'>Unlocks after your draft — weighs value on each "
        "side of a proposed trade.</span>",
        unsafe_allow_html=True,
    )

    # ---- Player Stat History (from the database) ----
    st.markdown(
        "<div class='sec-head'>Player Stat History</div>", unsafe_allow_html=True
    )
    from database import get_player_stats

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
