"""
PlastiCrete AI — Streamlit Frontend
All 4 modules integrated into one deployable app.
"""
from __future__ import annotations

import os

import requests
import streamlit as st

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title="PlastiCrete AI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar — Mix Input ────────────────────────────────────
st.sidebar.title("🏗️ PlastiCrete AI")
st.sidebar.caption("Plastic Waste Composite Construction Materials")
st.sidebar.markdown("---")
st.sidebar.subheader("Mix Parameters")

plastic_type = st.sidebar.selectbox(
    "Plastic Type", ["PET", "HDPE", "LDPE", "PVC", "PP", "Mixed"]
)
replacement_pct = st.sidebar.slider(
    "Replacement % (by volume)", 0.0, 40.0, 15.0, 0.5
)
particle_size_mm = st.sidebar.slider(
    "Particle Size (mm)", 0.5, 20.0, 4.0, 0.5
)
wc_ratio = st.sidebar.slider(
    "Water/Cement Ratio", 0.35, 0.65, 0.45, 0.01
)
additive_type = st.sidebar.selectbox(
    "Additive Type", ["none", "fly_ash", "silica_fume", "fibres"]
)
additive_pct = st.sidebar.slider(
    "Additive %", 0.0, 30.0, 0.0, 0.5,
    disabled=(additive_type == "none")
)
curing_temp_c = st.sidebar.slider(
    "Curing Temperature (°C)", 20.0, 80.0, 27.0, 1.0
)
curing_days = st.sidebar.slider(
    "Curing Days", 3, 90, 28, 1
)

st.sidebar.markdown("---")
run_all = st.sidebar.button("▶ Run All Modules", type="primary", use_container_width=True)

# ── Helper ─────────────────────────────────────────────────
def post(endpoint: str, payload: dict) -> dict | None:
    try:
        r = requests.post(f"{API_BASE}{endpoint}", json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Service unavailable. Please try again later.")
        return None
    except Exception as e:
        st.error(f"❌ API error: {e}")
        return None

# ── Main layout ────────────────────────────────────────────
st.title("🏗️ PlastiCrete AI")
st.caption("Explainable ML Platform for Plastic Waste Composite Construction Materials")

tab1, tab2, tab3, tab4 = st.tabs([
    "🔬 M1 — Property Prediction",
    "♻️ M3 — Sustainability Score",
    "🏆 M4 — Application Recommendation",
    "⚙️ M2 — Mix Optimisation",
])

mix_payload = dict(
    plastic_type=plastic_type,
    replacement_pct=replacement_pct,
    particle_size_mm=particle_size_mm,
    wc_ratio=wc_ratio,
    additive_type=additive_type,
    additive_pct=additive_pct if additive_type != "none" else 0.0,
    curing_temp_c=curing_temp_c,
    curing_days=curing_days,
)

# ── TAB 1 — M1 ─────────────────────────────────────────────
with tab1:
    st.subheader("M1 — Property Prediction Engine")
    st.caption("XGBoost + Random Forest + DNN Ensemble | 7 simultaneous predictions")

    if run_all or st.button("Predict Properties", key="btn_m1"):
        with st.spinner("Running M1 ensemble..."):
            m1_result = post("/predict", mix_payload)

        if m1_result:
            preds = m1_result["predictions"]
            col1, col2, col3, col4 = st.columns(4)
            cols = [col1, col2, col3, col4]
            icons = ["💪","〰️","🔩","⚖️","💧","🌡️","🛡️"]
            labels = [
                "Compressive Strength (MPa)",
                "Flexural Strength (MPa)",
                "Split Tensile (MPa)",
                "Density (kg/m³)",
                "Water Absorption (%)",
                "Thermal Conductivity (W/m·K)",
                "Durability Index",
            ]
            keys = [
                "compressive_strength_mpa",
                "flexural_strength_mpa",
                "split_tensile_mpa",
                "density_kgm3",
                "water_absorption_pct",
                "thermal_conductivity_wm",
                "durability_index",
            ]
            for i, (k, label, icon) in enumerate(zip(keys, labels, icons)):
                p = preds.get(k, {})
                mean = p.get("mean")
                lo   = p.get("ci_90_low")
                hi   = p.get("ci_90_high")
                with cols[i % 4]:
                    if mean is not None:
                        st.metric(f"{icon} {label}", f"{mean:.2f}")
                        st.caption(f"90% CI: [{lo:.2f}, {hi:.2f}]" if lo and hi else "")
                    else:
                        st.metric(f"{icon} {label}", "N/A")

            if m1_result.get("uncertainty_flag"):
                st.warning("⚠️ High uncertainty — mix is outside training distribution.")
            if m1_result.get("low_coverage_targets"):
                st.info(f"ℹ️ Low coverage targets: {', '.join(m1_result['low_coverage_targets'])}")

            st.session_state["m1_result"]  = m1_result
            st.session_state["m1_preds"]   = preds
            st.session_state["mix_payload"] = mix_payload

# ── TAB 2 — M3 ─────────────────────────────────────────────
with tab2:
    st.subheader("M3 — Sustainability & Compliance Scoring Engine")
    st.caption("Embodied Carbon · BIS Compliance · IGBC/GRIHA/LEED Credits · 0–100 Score")

    if "m1_preds" not in st.session_state:
        st.info("Run M1 Property Prediction first (Tab 1).")
    else:
        if run_all or st.button("Score Sustainability", key="btn_m3"):
            preds = st.session_state["m1_preds"]

            def safe(k): 
                v = preds.get(k, {}).get("mean")
                return v if v is not None else 0.0

            score_payload = {
                **mix_payload,
                "compressive_strength_mpa": safe("compressive_strength_mpa"),
                "flexural_strength_mpa":    safe("flexural_strength_mpa"),
                "split_tensile_mpa":        safe("split_tensile_mpa"),
                "density_kgm3":             safe("density_kgm3"),
                "water_absorption_pct":     safe("water_absorption_pct"),
                "thermal_conductivity_wm":  safe("thermal_conductivity_wm"),
                "durability_index":         safe("durability_index"),
            }
            with st.spinner("Running M3 scorer..."):
                m3_result = post("/score", score_payload)

            if m3_result:
                st.session_state["m3_result"]      = m3_result
                st.session_state["score_payload"]  = score_payload

                grade = m3_result.get("sustainability_grade", "?")
                score = m3_result.get("sustainability_score", 0)
                grade_color = {"A":"🟢","B":"🟡","C":"🟠","D":"🔴"}.get(grade, "⚪")

                col1, col2, col3 = st.columns(3)
                col1.metric("🏅 Sustainability Score", f"{score:.1f} / 100")
                col1.metric("Grade", f"{grade_color} {grade}")
                col2.metric("🌿 Embodied Carbon",
                            f"{m3_result.get('embodied_carbon_kgco2e_m3', 0):.1f} kg CO₂e/m³")
                col2.metric("📉 CO₂ Saving", f"{m3_result.get('co2_saving_pct', 0):.1f}%")
                col3.metric("♻️ Plastic Diverted",
                            f"{m3_result.get('plastic_diversion_kg_m3', 0):.1f} kg/m³")
                col3.metric("🍶 PET Bottles Equiv.",
                            f"{m3_result.get('pet_bottle_equiv', 0):.0f} bottles")

                st.markdown("---")
                col4, col5 = st.columns(2)
                with col4:
                    st.markdown("**BIS Compliance**")
                    bis = "✅ PASS" if m3_result.get("bis_overall_pass") else "❌ FAIL"
                    st.write(bis)
                with col5:
                    st.markdown("**Green Rating Credits**")
                    st.write(f"IGBC: {m3_result.get('igbc_total_credits', 0):.0f} / 3")
                    st.write(f"GRIHA: {m3_result.get('griha_material_criterion_pts', 0):.0f} / 2")
                    st.write(f"LEED: {m3_result.get('leed_total_points', 0):.0f} / 2")

                st.markdown("---")
                st.markdown("**Remediation Advice**")
                st.warning(f"⚠️ Top limiting factor: `{m3_result.get('top_negative_factor', 'N/A')}`")
                for i in range(1, 4):
                    action = m3_result.get(f"remediation_action_{i}", "")
                    if action:
                        st.write(f"{i}. {action}")
                gain = m3_result.get("estimated_score_gain", 0)
                if gain:
                    st.success(f"Estimated score gain if remediation applied: +{gain:.1f} points")

# ── TAB 3 — M4 ─────────────────────────────────────────────
with tab3:
    st.subheader("M4 — Construction Application Recommendation Engine")
    st.caption("RF Classifier · RAG Nearest-Neighbour · Cost-Benefit Calculator")

    if "m1_preds" not in st.session_state:
        st.info("Run M1 Property Prediction first (Tab 1).")
    else:
        if run_all or st.button("Get Recommendations", key="btn_m4"):
            preds = st.session_state["m1_preds"]

            def safe(k):
                v = preds.get(k, {}).get("mean")
                return v if v is not None else 0.0

            rec_payload = {
                **mix_payload,
                "compressive_strength_mpa": safe("compressive_strength_mpa"),
                "flexural_strength_mpa":    safe("flexural_strength_mpa"),
                "split_tensile_mpa":        safe("split_tensile_mpa"),
                "density_kgm3":             safe("density_kgm3"),
                "water_absorption_pct":     safe("water_absorption_pct"),
                "thermal_conductivity_wm":  safe("thermal_conductivity_wm"),
                "durability_index":         safe("durability_index"),
            }
            with st.spinner("Running M4 recommender..."):
                m4_result = post("/recommend", rec_payload)

            if m4_result:
                st.session_state["m4_result"] = m4_result

                primary = m4_result["primary_application"].replace("_", " ").title()
                conf    = m4_result["primary_confidence_pct"]
                st.success(f"✅ **Primary Application: {primary}** (confidence: {conf:.1f}%)")

                suitable = m4_result.get("suitable_applications", [])
                if suitable:
                    st.markdown("**All Suitable Applications:**")
                    st.write(" · ".join(
                        [f"`{a.replace('_', ' ').title()}`" for a in suitable]
                    ))

                st.markdown("---")
                st.markdown("**Suitability Scores (0–100)**")
                scores = m4_result.get("suitability_scores", {})
                for app, score in list(scores.items())[:8]:
                    label = app.replace("_", " ").title()
                    st.progress(int(min(score, 100)), text=f"{label}: {score:.1f}")

                st.markdown("---")
                cb = m4_result.get("cost_benefit", {})
                col1, col2, col3 = st.columns(3)
                col1.metric("💰 Plastic Mix Cost",
                            f"₹{cb.get('plastic_mix_cost_inr_m3', 0):,.0f}/m³",
                            f"₹{cb.get('plastic_mix_cost_inr_m2', 0):,.0f}/m²")
                col2.metric("🏗️ Conventional Cost",
                            f"₹{cb.get('conventional_cost_inr_m3', 0):,.0f}/m³",
                            f"₹{cb.get('conventional_cost_inr_m2', 0):,.0f}/m²")
                col3.metric("📉 Cost Saving",
                            f"{cb.get('cost_saving_pct', 0):+.1f}%",
                            f"₹{cb.get('cost_saving_inr_m2', 0):,.0f}/m² saved")

                st.markdown("---")
                st.markdown("**Top 3 Validated Research Analogues (RAG)**")
                for a in m4_result.get("rag_analogues", []):
                    app_label = a["primary_application"].replace("_", " ").title()
                    with st.expander(
                        f"#{a['rank']} — {a['author']} ({a['year']}) · {a['journal']}"
                    ):
                        st.write(f"**Application:** {app_label}")
                        st.write(f"**DOI:** `{a['doi']}`")
                        st.write(f"**Similarity (L2 distance):** {a['l2_distance']}")
                        prop_cols = st.columns(4)
                        props = a.get("properties", {})
                        for i, (k, v) in enumerate(props.items()):
                            prop_cols[i % 4].metric(k.replace("_", " ").title(), f"{v:.2f}")

# ── TAB 4 — M2 ─────────────────────────────────────────────
with tab4:
    st.subheader("M2 — Mix Optimisation Engine")
    st.caption("GP-BO · NSGA-II · Sensitivity Analysis")

    st.markdown("**Objective Weights** (must sum to 1.0)")
    col1, col2, col3, col4 = st.columns(4)
    w_cs   = col1.number_input("Compressive Strength", 0.0, 1.0, 0.40, 0.05)
    w_cost = col2.number_input("Cost",                 0.0, 1.0, 0.30, 0.05)
    w_co2  = col3.number_input("CO₂",                  0.0, 1.0, 0.20, 0.05)
    w_pl   = col4.number_input("Plastic Content",      0.0, 1.0, 0.10, 0.05)

    total_w = round(w_cs + w_cost + w_co2 + w_pl, 2)
    if abs(total_w - 1.0) > 0.01:
        st.warning(f"⚠️ Weights sum to {total_w:.2f} — should be 1.0")

    st.markdown("**Constraints**")
    col5, col6, col7 = st.columns(3)
    fix_plastic  = col5.selectbox("Fix Plastic Type (optional)",
                                  ["(free)", "PET", "HDPE", "LDPE", "PVC", "PP", "Mixed"])
    rep_max      = col6.slider("Max Replacement %", 5.0, 40.0, 25.0, 1.0)
    cs_min       = col7.number_input("Min CS (MPa)", 0.0, 80.0, 20.0, 1.0)
    opt_mode     = st.selectbox("Mode", ["constrained", "scenario"])

    if st.button("⚙️ Run Optimisation", key="btn_m2"):
        opt_payload = {
            "plastic_type":             None if fix_plastic == "(free)" else fix_plastic,
            "replacement_pct_max":      rep_max,
            "compressive_strength_min": cs_min,
            "weight_compressive":       w_cs,
            "weight_cost":              w_cost,
            "weight_co2":               w_co2,
            "weight_plastic_content":   w_pl,
            "mode":                     opt_mode,
        }
        with st.spinner("Running M2 optimiser..."):
            m2_result = post("/optimize", opt_payload)

        if m2_result:
            st.success("✅ Optimisation complete")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("💪 Predicted CS",
                        f"{m2_result.get('predicted_cs_mpa', 0):.1f} MPa")
            col2.metric("💰 Cost",
                        f"₹{m2_result.get('predicted_cost_inr_m3', 0):,.0f}/m³")
            col3.metric("🌿 CO₂",
                        f"{m2_result.get('predicted_co2_kgco2e_m3', 0):.1f} kg/m³")
            col4.metric("🏅 Composite Score",
                        f"{m2_result.get('composite_score', 0):.3f}")

            st.markdown("**Optimal Mix Formulation**")
            best = m2_result.get("best_mix", {})
            cols = st.columns(4)
            for i, (k, v) in enumerate(best.items()):
                cols[i % 4].metric(k.replace("_", " ").title(), f"{v}")