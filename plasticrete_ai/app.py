"""
PlastiCrete AI — Streamlit entrypoint (premium civil-sector UI).

`streamlit run app.py` boots the multi-page navigation shell. All UI lives in the
`ui/` package; the backend ML modules are reached in-process through
`ui.data_bridge` (real module → mock fallback), so no sidecar API is required.

Legacy note — the previous `app.py` was a Hugging Face dual-process launcher
(uvicorn FastAPI `deployment/api/app:app` + the old `deployment/frontend/
streamlit_app.py`). That path is preserved untouched under `deployment/` and in
git history; the API-based deployment can still be launched with
`python -m deployment.api.app` + the old frontend. This file is now the primary
Streamlit Space entrypoint.
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="PlastiCrete AI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui import mock_data, nav
from ui.theme import load_css
from ui.pages import (
    dashboard, m1_prediction, m2_optimiser, m3_sustainability,
    m4_recommender, explainability, insights,
)

_LOGO = (
    "<svg width='26' height='26' viewBox='0 0 32 32' fill='none' "
    "xmlns='http://www.w3.org/2000/svg'>"
    "<rect x='3' y='12' width='26' height='16' rx='2.5' fill='#2B3A55'/>"
    "<rect x='7' y='16' width='7' height='8' rx='1' fill='#3E5277'/>"
    "<rect x='18' y='16' width='7' height='8' rx='1' fill='#3E5277'/>"
    "<path d='M16 3c-3.6 2.2-5 5.2-3.4 8.2C14 8.6 16.4 7.6 20 8c-1.6-2.6-1.6-3.4-4-5z' "
    "fill='#22C55E'/><circle cx='16' cy='8.6' r='1.4' fill='#F59E0B'/></svg>"
)


def _bootstrap() -> None:
    ss = st.session_state
    ss.setdefault("dark_mode", False)
    ss.setdefault("segment", "Manufacturer")
    ss.setdefault("mix", dict(mock_data.ACTIVE_MIX))
    ss.setdefault("prediction", mock_data.prediction())
    ss.setdefault("score", mock_data.sustainability())
    ss.setdefault("recommendation", mock_data.recommendation())
    ss.setdefault("explain_target", "compressive_strength_mpa")


def _top_bar(current_title: str) -> None:
    a, b, c, d = st.columns([3, 2.4, 1, 1.6])
    with a:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:9px;padding-top:4px'>{_LOGO}"
            f"<span style='font-family:JetBrains Mono,monospace;color:var(--pc-text-muted);"
            f"font-size:.8rem'>PlastiCrete&nbsp;AI&nbsp;/&nbsp;"
            f"<b style='color:var(--pc-text)'>{current_title}</b></span></div>",
            unsafe_allow_html=True)
    with b:
        st.segmented_control(
            "segment", ["Manufacturer", "Consultant", "Researcher", "Govt"],
            key="segment", label_visibility="collapsed")
    with c:
        st.toggle("🌙 Dark", key="dark_mode")
    with d:
        if st.button("▶ Run New Prediction", type="primary", use_container_width=True):
            nav.goto("m1")
    st.markdown("<hr style='margin:2px 0 14px;border:none;border-top:1px solid var(--pc-border)'>",
                unsafe_allow_html=True)


def main() -> None:
    _bootstrap()
    load_css(st.session_state.dark_mode)

    # sidebar brand (above the nav links)
    with st.sidebar:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;padding:6px 4px 2px'>{_LOGO}"
            f"<div><div style='font-family:Space Grotesk;font-weight:700;font-size:1.05rem'>"
            f"PlastiCrete AI</div><div class='pc-card-sub' style='font-size:.7rem'>"
            f"Plastic-waste materials intelligence</div></div></div>",
            unsafe_allow_html=True)
        st.markdown("<hr style='margin:8px 0;border:none;border-top:1px solid var(--pc-border)'>",
                    unsafe_allow_html=True)

    # build pages
    p_dash = st.Page(dashboard.render, title="Dashboard", icon="🏠", url_path="dashboard", default=True)
    p_m1 = st.Page(m1_prediction.render, title="Property Prediction", icon="🔬", url_path="m1")
    p_m3 = st.Page(m3_sustainability.render, title="Sustainability & Compliance", icon="♻️", url_path="m3")
    p_m4 = st.Page(m4_recommender.render, title="Application Recommender", icon="🏆", url_path="m4")
    p_m2 = st.Page(m2_optimiser.render, title="Mix Optimiser", icon="⚙️", url_path="m2")
    p_xai = st.Page(explainability.render, title="Explainability Lab", icon="🔎", url_path="explain")
    p_ins = st.Page(insights.render, title="Material Insights", icon="🧭", url_path="insights")

    for key, page in [("dashboard", p_dash), ("m1", p_m1), ("m3", p_m3), ("m4", p_m4),
                      ("m2", p_m2), ("explain", p_xai), ("insights", p_ins)]:
        nav.register(key, page)

    pages = {
        "Overview": [p_dash],
        "Modules · M1→M3→M4→M2": [p_m1, p_m3, p_m4, p_m2],
        "Explore": [p_xai, p_ins],
    }
    current = st.navigation(pages, position="sidebar")

    _top_bar(current.title)
    current.run()


if __name__ == "__main__":
    main()
