"""M2 — Mix Optimiser (Bayesian virtual laboratory)."""
from __future__ import annotations

import time

import streamlit as st

from ui import charts, components as C, data_bridge, mock_data
from ui.theme import PLASTIC_TYPES, page_header


def render():
    ss = st.session_state
    dark = ss.get("dark_mode", False)

    page_header("Mix Optimiser",
                "Find the optimal recipe for a target across strength, cost, CO₂ & plastic diversion.",
                "Module M2 · Bayesian optimisation")

    # ── objective configurator ────────────────────────────────────────────────
    C.section("Objective priorities", "weight the four goals")
    o1, o2 = st.columns([1.6, 1], gap="large")
    with o1:
        c = st.columns(4)
        w_cs = c[0].slider("Max Strength", 0.0, 1.0, 0.40, 0.05)
        w_cost = c[1].slider("Min Cost", 0.0, 1.0, 0.25, 0.05)
        w_co2 = c[2].slider("Min CO₂", 0.0, 1.0, 0.20, 0.05)
        st.markdown("<div style='margin-top:-6px'></div>", unsafe_allow_html=True)
        w_div = c[3].slider("♻️ Max Diversion", 0.0, 1.0, 0.15, 0.05,
                            help="Signature objective — maximise plastic waste diverted per m³.")
        c[3].markdown("<div class='pc-eyebrow-dark'>★ signature objective</div>",
                      unsafe_allow_html=True)
        total = w_cs + w_cost + w_co2 + w_div or 1.0
        weights = {"compressive_strength": w_cs/total, "cost_per_m3": w_cost/total,
                   "co2_per_m3": w_co2/total, "plastic_content_pct": w_div/total}
    with o2:
        st.plotly_chart(charts.objective_radar(weights, dark=dark, height=230),
                        use_container_width=True, config={"displayModeBar": False})

    # ── constraint builder ────────────────────────────────────────────────────
    C.section("Hard constraints")
    cc = st.columns([1, 1, 1, 1])
    fix_plastic = cc[0].selectbox("Fix plastic type", ["(free)", *PLASTIC_TYPES])
    cs_min = cc[1].slider("Compressive ≥ (MPa)", 0.0, 60.0, 20.0, 1.0)
    use_den = cc[2].toggle("Limit density", value=False)
    den_max = cc[2].slider("Density ≤ (kg/m³)", 1200, 2600, 1800, 50, disabled=not use_den)
    rep_max = cc[3].slider("Replacement ≤ %", 5.0, 40.0, 30.0, 1.0)

    pills = [C.compliance_pill_html("pass", f"CS ≥ {cs_min:.0f} MPa"),
             C.compliance_pill_html("pass", f"Replacement ≤ {rep_max:.0f}%")]
    if fix_plastic != "(free)":
        pills.append(C.compliance_pill_html("warn", f"{fix_plastic} only"))
    if use_den:
        pills.append(C.compliance_pill_html("warn", f"Density ≤ {den_max} kg/m³"))
    st.markdown(" ".join(pills), unsafe_allow_html=True)

    constraints = {
        "plastic_type": None if fix_plastic == "(free)" else fix_plastic,
        "replacement_pct_max": rep_max, "compressive_strength_min": cs_min,
        "density_max_kgm3": float(den_max) if use_den else None,
        "cost_max_inr_per_m3": None,
    }

    st.write("")
    run = st.button("⚙ Run optimiser", type="primary")
    if run:
        with st.spinner("Optimising across the surrogate landscape…"):
            ss.optimized = data_bridge.optimize(constraints, weights, mode="constrained")

    st.write("")
    # ── scenario cards ────────────────────────────────────────────────────────
    C.section("One-click scenarios")
    scols = st.columns(3, gap="medium")
    for col, (key, sc) in zip(scols, mock_data.SCENARIOS.items()):
        with col:
            with st.container(border=True):
                st.markdown(
                    f"<div class='pc-card-title'>{sc['icon']} {sc['label']}</div>"
                    f"<div class='pc-metric-value sm'>{sc['headline']}</div>"
                    f"<div class='pc-card-sub'>{sc['headline_label']}</div>",
                    unsafe_allow_html=True)
                m = sc["best_mix"]
                st.caption(f"{m['plastic_type']} · {m['replacement_pct']:.0f}% · w/c {m['wc_ratio']:.2f}")
                if st.button("Run scenario", key=f"scn_{key}", use_container_width=True):
                    with st.spinner(f"Running {sc['label']}…"):
                        ss.optimized = data_bridge.optimize(
                            {**constraints, "plastic_type": None}, weights, mode="scenario")
                        if ss.optimized.get("source") == "mock":
                            ss.optimized = mock_data.optimize(key)

    st.write("")
    # ── pareto front ──────────────────────────────────────────────────────────
    C.section("Pareto front", "non-dominated solutions · Strength ↔ Cost")
    pts = mock_data.pareto_front()
    ph = st.empty()
    if st.button("▶ Animate convergence"):
        for n in range(6, len(pts) + 1, 3):
            ph.plotly_chart(charts.pareto_scatter(pts, dark=dark, n_visible=n),
                            use_container_width=True, config={"displayModeBar": False},
                            key=f"par_{n}")
            time.sleep(0.04)
    ph.plotly_chart(charts.pareto_scatter(pts, dark=dark),
                    use_container_width=True, config={"displayModeBar": False}, key="par_full")
    st.caption("Point size ∝ plastic diverted · colour ∝ embodied CO₂. "
               "Illustrative NSGA-II front from the training landscape.")

    st.write("")
    # ── optimised recipe vs current ───────────────────────────────────────────
    opt = ss.get("optimized")
    if opt:
        C.section("Optimised recipe", f"mode · {opt.get('mode','—')}")
        C.source_chip(opt.get("source", "mock"))
        m = opt["best_mix"]
        k = st.columns(4)
        cur_cs = ss.prediction["values"]["compressive_strength_mpa"]
        cur_co2 = ss.score["embodied_carbon_kgco2e_m3"]
        cur_div = ss.score["plastic_diversion_kg_m3"]
        k[0].metric("Compressive", f"{opt['predicted_cs_mpa']:.1f} MPa",
                    f"{opt['predicted_cs_mpa']-cur_cs:+.1f} vs current")
        k[1].metric("Cost", f"₹{opt['predicted_cost_inr_m3']:,.0f}/m³")
        k[2].metric("Embodied CO₂", f"{opt['predicted_co2_kgco2e_m3']:.0f} kg/m³",
                    f"{opt['predicted_co2_kgco2e_m3']-cur_co2:+.0f} vs current", delta_color="inverse")
        k[3].metric("Plastic diverted", f"{opt['predicted_plastic_diversion_kg_m3']:.1f} kg/m³",
                    f"{opt['predicted_plastic_diversion_kg_m3']-cur_div:+.1f} vs current")
        st.markdown(
            "**Recipe** — "
            f"`{m.get('plastic_type','?')}` · {m.get('replacement_pct',0):.1f}% · "
            f"{m.get('particle_size_mm',0):.1f} mm · w/c {m.get('wc_ratio',0):.2f} · "
            f"{m.get('additive_type','none')} {m.get('additive_pct',0):.0f}% · "
            f"{m.get('curing_temp_c',0):.0f}°C · {int(m.get('curing_days',0))}d")

    st.write("")
    # ── sensitivity ───────────────────────────────────────────────────────────
    C.section("Sensitivity analysis", "±10% input variation → Δ strength")
    st.plotly_chart(charts.sensitivity_tornado(mock_data.sensitivity(), dark=dark),
                    use_container_width=True, config={"displayModeBar": False})
    st.caption("Inputs with the longest bars are the highest quality-control priorities.")
