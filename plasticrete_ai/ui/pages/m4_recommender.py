"""M4 — Application Recommender."""
from __future__ import annotations

import streamlit as st

from ui import charts, components as C
from ui.theme import PALETTE, label_app, page_header


def render():
    ss = st.session_state
    dark = ss.get("dark_mode", False)
    rec = ss.recommendation

    page_header("Application Recommender",
                "What should this mix be used to build? 12 construction products, ranked.",
                "Module M4 · RF classifier + RAG")
    c1, c2 = st.columns([3, 1])
    with c1:
        primary = label_app(rec["primary_application"])
        st.markdown(
            f"<div class='pc-card' style='border-left:4px solid var(--pc-green)'>"
            f"<div class='pc-card-sub'>Primary recommendation</div>"
            f"<div style='font-family:Space Grotesk;font-size:1.4rem;font-weight:600'>"
            f"🏆 {primary}</div>"
            f"<div class='pc-card-sub'>Suitability "
            f"<b style='color:var(--pc-green)'>{rec['primary_confidence_pct']:.0f}%</b></div></div>",
            unsafe_allow_html=True)
    with c2:
        C.source_chip(rec.get("source", "mock"))
        if rec.get("source") == "mock":
            st.caption("RAG index (faiss) not installed — demo recommendations.")

    st.write("")
    C.section("Ranked applications", "12 products · sorted by suitability")
    scores = rec["suitability_scores"]
    items = sorted(scores.items(), key=lambda kv: -kv[1])
    for i in range(0, len(items), 4):
        cols = st.columns(4)
        for col, (key, sc) in zip(cols, items[i:i+4]):
            with col:
                C.application_card(key, sc)

    st.write("")
    # ── cost-benefit ──────────────────────────────────────────────────────────
    cb = rec["cost_benefit"]
    C.section("Cost-benefit", f"top pick · {label_app(rec['primary_application'])}")
    a, b = st.columns([1.3, 1], gap="large")
    with a:
        with st.container(border=True):
            st.plotly_chart(
                charts.comparison_bar(
                    ["Plastic mix", "Conventional"],
                    [cb["plastic_mix_cost_inr_m2"], cb["conventional_cost_inr_m2"]],
                    [PALETTE["green"], PALETTE["muted"]], dark=dark, height=180,
                    x_title="₹ / m²", suffix=""),
                use_container_width=True, config={"displayModeBar": False})
    with b:
        st.metric("Cost / m²", f"₹{cb['plastic_mix_cost_inr_m2']:,.0f}",
                  f"−₹{cb['cost_saving_inr_m2']:,.0f} vs conventional")
        st.metric("Saving", f"{cb['cost_saving_pct']:.1f}%",
                  f"₹{cb['cost_saving_inr_m3']:,.0f}/m³")
        st.caption(f"Yield ≈ {cb['product_yield_m2_per_m3']:.1f} m²/m³ · "
                   f"plastic {cb['plastic_kg_per_m3']:.0f} kg/m³")

    st.write("")
    # ── RAG analogues ─────────────────────────────────────────────────────────
    C.section("Nearest validated analogues", "RAG · published formulations")
    st.caption("The 3 most similar real mixes from the literature knowledge base.")
    cols = st.columns(3, gap="medium")
    for col, a in zip(cols, rec["rag_analogues"][:3]):
        with col:
            C.citation_card(a)
