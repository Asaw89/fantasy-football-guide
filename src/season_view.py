import streamlit as st
from helpers import badge, espn_photo


def render_season_mode(load_waivers):
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
