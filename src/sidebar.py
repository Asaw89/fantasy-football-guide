import streamlit as st
from collections import Counter as _C
from config import STARTERS, BENCH_SPOTS
from helpers import badge, sleeper_photo


def render_sidebar(board, my_roster, needs, load_top_stories, cached_news, reset_draft):
    """Render the whole sidebar. Returns the selected mode string."""
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

        # ---- Player Search ----
        st.markdown("<div class='sec-head'>Player Search</div>", unsafe_allow_html=True)
        news_options = {f"{p['name']} · {p['position']} {p['team']}": p for p in board}
        choice = st.selectbox(
            "Find a player",
            options=list(news_options.keys()),
            label_visibility="collapsed",
        )
        if st.button("Get news", type="primary", use_container_width=True):
            picked = news_options[choice]
            with st.spinner(f"Searching outlets for {picked['name']}..."):
                result = cached_news(picked["name"], picked["team"], picked["position"])
                st.session_state.news_summary = result["summary"]
                st.session_state.news_sources = result.get("sources", {})
                st.session_state.news_player = picked["name"]
                st.session_state.news_photo = sleeper_photo(picked.get("player_id"))

        # News result
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
        st.markdown(
            "<div class='sec-head'>Ask the Analyst</div>", unsafe_allow_html=True
        )
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

        # Analyst answer
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

            st.markdown(
                "<div class='sec-head'>Still Need</div>", unsafe_allow_html=True
            )
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
            strengths = []
            for pos in STARTERS:
                pos_players = [p for p in my_roster if p["position"] == pos]
                surplus = len(pos_players) - STARTERS[pos]
                pos_vor = sum(p.get("vor", 0) for p in pos_players)
                if surplus >= 1 and pos_vor > 100:
                    strengths.append((pos, len(pos_players), round(pos_vor)))

            if strengths:
                st.markdown(
                    "<div class='sec-head'>Strengths</div>", unsafe_allow_html=True
                )
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

    return mode
