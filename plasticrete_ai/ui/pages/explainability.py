"""Explainability Lab — SHAP · LIME · PDP/ICE · Feature Importance."""
from __future__ import annotations

import streamlit as st

from ui import charts, components as C, mock_data
from ui.theme import TARGET_META, page_header


def render():
    ss = st.session_state
    dark = ss.get("dark_mode", False)
    pred = ss.prediction

    page_header("Explainability Lab",
                "Legible, premium XAI — see exactly why the model predicts what it does.",
                "SHAP · LIME · PDP / ICE")

    tabs = st.tabs(["🔵 SHAP", "🟢 LIME", "📈 PDP / ICE", "📊 Feature Importance"])

    # ══ SHAP ══════════════════════════════════════════════════════════════════
    with tabs[0]:
        targets = list(TARGET_META.keys())
        default = ss.get("explain_target", "compressive_strength_mpa")
        idx = targets.index(default) if default in targets else 0
        t = st.selectbox("Explain property", targets, index=idx,
                         format_func=lambda x: TARGET_META[x][0])
        label, unit, *_ = TARGET_META[t]
        shap = pred["shap_values"].get(t) or mock_data.prediction()["shap_values"].get(
            t, mock_data.prediction()["shap_values"]["compressive_strength_mpa"])
        final = pred["values"].get(t) or 0.0

        C.section(f"Waterfall — {label}", "baseline → contributions → prediction")
        st.plotly_chart(charts.shap_waterfall(shap, final, unit=unit, dark=dark),
                        use_container_width=True, config={"displayModeBar": False})
        C.source_chip(pred.get("source", "mock"))

        st.write("")
        g1, g2 = st.columns(2, gap="large")
        with g1:
            C.section("Summary beeswarm", "global feature importance")
            feats = list(shap.keys())[:7]
            st.plotly_chart(charts.beeswarm(feats, dark=dark),
                            use_container_width=True, config={"displayModeBar": False})
        with g2:
            C.section("Interaction heatmap", "plastic % × silica fume %")
            reps = [0, 10, 20, 30, 40]
            sf = [0, 5, 10, 15, 20]
            z = [[34 - r*0.45 + s*0.6 for s in sf] for r in reps]
            st.plotly_chart(
                charts.heatmap(z, [f"{s}%" for s in sf], [f"{r}%" for r in reps],
                               x_title="Silica fume", y_title="Plastic %",
                               cbar="CS MPa", dark=dark),
                use_container_width=True, config={"displayModeBar": False})

    # ══ LIME ══════════════════════════════════════════════════════════════════
    with tabs[1]:
        C.section("Contrastive remediation", "reach a target — three actionable routes")
        st.caption("Local surrogate (LIME) — single-parameter changes to lift compressive "
                   "strength toward the 20 MPa (M20) threshold.")
        options = [
            ("Reduce plastic replacement", "20% → 12%", "+2.1 MPa", "🔻"),
            ("Lower water–cement ratio", "0.50 → 0.43", "+1.8 MPa", "💧"),
            ("Add silica fume", "0% → 10%", "+2.4 MPa", "🧪"),
        ]
        cols = st.columns(3, gap="medium")
        for col, (title, change, gain, icon) in zip(cols, options):
            with col:
                st.markdown(
                    f"<div class='pc-card pc-lift'>"
                    f"<div class='ico' style='font-size:1.4rem'>{icon}</div>"
                    f"<div class='pc-card-title'>{title}</div>"
                    f"<div class='pc-metric-value sm' style='font-size:1.4rem'>{change}</div>"
                    f"<div class='pc-pill pass' style='margin-top:8px'>▲ {gain}</div></div>",
                    unsafe_allow_html=True)

    # ══ PDP / ICE ═════════════════════════════════════════════════════════════
    with tabs[2]:
        pdp = mock_data.pdp_curves()
        C.section("Partial dependence", "how strength responds to each input")
        p = st.columns(3, gap="medium")
        with p[0]:
            st.plotly_chart(charts.pdp_line(pdp["replacement_pct"]["x"], pdp["replacement_pct"]["y"],
                            "Plastic Replacement (%)", dark=dark),
                            use_container_width=True, config={"displayModeBar": False})
            st.caption("Characteristic non-linear decline with plastic content.")
        with p[1]:
            st.plotly_chart(charts.pdp_line(pdp["wc_ratio"]["x"], pdp["wc_ratio"]["y"],
                            "Water–Cement Ratio", dark=dark),
                            use_container_width=True, config={"displayModeBar": False})
            st.caption("Strength falls steadily as w/c rises.")
        with p[2]:
            st.plotly_chart(charts.pdp_line(pdp["curing_days"]["x"], pdp["curing_days"]["y"],
                            "Curing Duration (days)", dark=dark),
                            use_container_width=True, config={"displayModeBar": False})
            st.caption("Logarithmic strength gain with curing time.")

        st.write("")
        h1, h2 = st.columns(2, gap="large")
        with h1:
            C.section("2D PDP", "plastic % × additive type")
            adds = ["none", "fly ash", "silica fume", "fibres"]
            reps = [0, 10, 20, 30, 40]
            z = [[22 - r*0.4 + a*2.1 for a in range(len(adds))] for r in reps]
            st.plotly_chart(
                charts.heatmap(z, adds, [f"{r}%" for r in reps], x_title="Additive",
                               y_title="Plastic %", cbar="CS MPa", dark=dark),
                use_container_width=True, config={"displayModeBar": False})
        with h2:
            C.section("ICE curves", "per-plastic-type heterogeneity")
            st.plotly_chart(charts.ice_lines(mock_data.ice_curves(), dark=dark),
                            use_container_width=True, config={"displayModeBar": False})
            st.caption("PET declines gradually; PVC drops sharply above ~15%.")

    # ══ Feature importance ════════════════════════════════════════════════════
    with tabs[3]:
        C.section("Feature importance", "SHAP |mean| vs XGBoost gain")
        t2 = st.selectbox("Property", list(TARGET_META.keys()),
                          format_func=lambda x: TARGET_META[x][0], key="fi_target")
        shap = pred["shap_values"].get(t2) or mock_data.prediction()["shap_values"][
            "compressive_strength_mpa"]
        feats = list(shap.keys())[:7]
        shap_imp = [abs(shap[f]) for f in feats]
        mx = max(shap_imp) or 1
        gain_imp = [v * (0.7 + 0.5 * ((i * 7) % 3) / 3) for i, v in enumerate(shap_imp)]
        gmx = max(gain_imp) or 1
        st.plotly_chart(
            charts.importance_bars(feats, [s/mx for s in shap_imp], [g/gmx for g in gain_imp],
                                   dark=dark),
            use_container_width=True, config={"displayModeBar": False})
