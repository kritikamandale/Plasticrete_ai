"""Dashboard — bento command center."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ui import charts, components as C, mock_data, nav
from ui.theme import PLASTIC_COLORS, label_app


def render():
    ss = st.session_state
    dark = ss.get("dark_mode", False)
    mix = ss.mix
    pred = ss.prediction
    score = ss.score

    # ── hero strip ────────────────────────────────────────────────────────────
    pcolor = PLASTIC_COLORS.get(mix["plastic_type"], "#64748B")
    st.markdown(
        f"<div class='pc-hero'>"
        f"<div class='pc-eyebrow'>PlastiCrete AI · Explainable Materials Intelligence</div>"
        f"<h1>From plastic waste to load-bearing intelligence.</h1>"
        f"<p class='pc-tagline'>Welcome back — your active formulation is "
        f"<span class='pc-chip {mix['plastic_type'].lower()}' style='background:{pcolor}'>"
        f"{mix['plastic_type']} · {mix['replacement_pct']:.0f}%</span> "
        f"@ w/c {mix['wc_ratio']:.2f}, {mix['additive_type'].replace('_',' ')} "
        f"{mix['additive_pct']:.0f}%, {mix['curing_days']}d.</p>"
        f"</div>",
        unsafe_allow_html=True)
    c1, c2, _ = st.columns([1.1, 1, 2.4])
    with c1:
        if st.button("＋ Design a New Mix", type="primary", use_container_width=True):
            nav.goto("m1")
    with c2:
        if st.button("⚙ Optimise a Target", use_container_width=True):
            nav.goto("m2")

    st.write("")
    # ── KPI row ───────────────────────────────────────────────────────────────
    cs = pred["values"]["compressive_strength_mpa"]
    lo = pred["ci_low"].get("compressive_strength_mpa", cs)
    hi = pred["ci_high"].get("compressive_strength_mpa", cs)
    pm = (hi - lo) / 2
    C.kpi_row([
        dict(label="Compressive Strength", value=f"{cs:.1f}", unit="MPa",
             sub=f"90% PI ±{pm:.1f}", icon="🧱"),
        dict(label="Sustainability Score", value=f"{score['sustainability_score']:.0f}",
             unit="/100", sub=f"Grade {score['sustainability_grade']}", icon="♻️"),
        dict(label="Plastic Diverted", value=f"{score['plastic_diversion_kg_m3']:.0f}",
             unit="kg/m³", sub=f"≈ {score['pet_bottle_equiv']:.0f} PET bottles", icon="🍶"),
        dict(label="Embodied Carbon", value=f"−{score['co2_saving_pct']:.0f}%", unit="",
             delta=f"vs M20 · {score.get('co2_saved_kgco2e_m3', 0):.0f} kg CO₂e/m³ saved",
             delta_good=True, icon="🌿"),
    ])

    st.write("")
    C.section("Module workflow", "how your data flows")
    C.workflow_rail(active_key="m1")

    st.write("")
    left, right = st.columns([1.5, 1])

    # ── recent predictions ────────────────────────────────────────────────────
    with left:
        C.section("Recent predictions")
        rows = mock_data.recent_predictions()
        df = pd.DataFrame(rows)
        df = df.rename(columns={
            "plastic_type": "Plastic", "replacement_pct": "Repl %", "wc_ratio": "w/c",
            "cs": "CS (MPa)", "score": "Score", "top_app": "Top application", "when": "When"})
        st.dataframe(
            df, use_container_width=True, hide_index=True,
            column_config={
                "Repl %": st.column_config.NumberColumn(format="%d%%"),
                "CS (MPa)": st.column_config.ProgressColumn(
                    format="%.1f", min_value=0, max_value=60),
                "Score": st.column_config.ProgressColumn(
                    format="%d", min_value=0, max_value=100),
            })

    # ── quick actions 2×2 ─────────────────────────────────────────────────────
    with right:
        C.section("Quick actions")
        q1, q2 = st.columns(2)
        with q1:
            C.quick_action_tile("🔬", "Predict", "7 properties from a recipe", "m1", "qa_m1")
            st.write("")
            C.quick_action_tile("♻️", "Score", "Sustainability & BIS", "m3", "qa_m3")
        with q2:
            C.quick_action_tile("⚙️", "Optimise", "Best mix for a target", "m2", "qa_m2")
            st.write("")
            C.quick_action_tile("🏆", "Recommend", "What to build", "m4", "qa_m4")

    st.write("")
    # ── SDG ribbon ────────────────────────────────────────────────────────────
    C.section("UN SDG impact", "live contribution")
    C.sdg_ribbon(counters={3: "cleaner air", 9: "circular industry",
                           11: "resilient cities", 12: f"{score['plastic_diversion_kg_m3']:.0f} kg/m³ diverted",
                           13: f"−{score['co2_saving_pct']:.0f}% CO₂"})

    st.write("")
    # ── mini cluster map ──────────────────────────────────────────────────────
    m1c, m2c = st.columns([1, 1])
    with m1c:
        C.section("Formulation archetypes")
        st.plotly_chart(
            charts.cluster_scatter(mock_data.cluster_scatter_points(),
                                   mock_data.CLUSTERS, dark=dark, height=300, mini=True),
            use_container_width=True, config={"displayModeBar": False})
        if st.button("Explore Material Insights →", key="dash_insights", use_container_width=True):
            nav.goto("insights")
    with m2c:
        C.section("Top applications for this mix")
        rec = ss.recommendation
        for app, sc in list(rec["suitability_scores"].items())[:5]:
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;align-items:center;"
                f"padding:7px 0;border-bottom:1px solid var(--pc-border)'>"
                f"<span style='font-weight:600'>{label_app(app)}</span>"
                f"<span style='font-family:JetBrains Mono,monospace;color:var(--pc-green);"
                f"font-weight:700'>{sc:.0f}%</span></div>",
                unsafe_allow_html=True)
        st.write("")
        if st.button("Full recommendation →", key="dash_m4", use_container_width=True):
            nav.goto("m4")
