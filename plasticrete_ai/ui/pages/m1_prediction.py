"""M1 — Property Prediction (input panel ↔ live output panel)."""
from __future__ import annotations

import streamlit as st

from ui import charts, components as C, data_bridge, mock_data, nav
from ui.theme import (
    ADDITIVE_TYPES, PLASTIC_COLORS, PLASTIC_TYPES, TARGET_META, page_header,
)

_ADD_LABELS = {"none": "None", "fly_ash": "Fly ash", "silica_fume": "Silica fume", "fibres": "Fibres"}
_ARCH = {c["name"]: c["params"] for c in mock_data.CLUSTERS}


def _sync_from_mix():
    mix = st.session_state.mix
    for k, wk in [("plastic_type", "m1_plastic"), ("replacement_pct", "m1_repl"),
                  ("particle_size_mm", "m1_particle"), ("wc_ratio", "m1_wc"),
                  ("additive_type", "m1_additive"), ("additive_pct", "m1_add_pct"),
                  ("curing_temp_c", "m1_temp"), ("curing_days", "m1_days")]:
        st.session_state.setdefault(wk, mix[k])


def _load_archetype():
    name = st.session_state.get("m1_arch")
    p = _ARCH.get(name)
    if not p:
        return
    st.session_state.m1_plastic = p["plastic_type"]
    st.session_state.m1_repl = float(p["replacement_pct"])
    st.session_state.m1_particle = float(p["particle_size_mm"])
    st.session_state.m1_wc = float(p["wc_ratio"])
    st.session_state.m1_additive = p["additive_type"]
    st.session_state.m1_add_pct = float(p["additive_pct"])
    st.session_state.m1_temp = float(p["curing_temp_c"])
    st.session_state.m1_days = int(p["curing_days"])


def render():
    ss = st.session_state
    dark = ss.get("dark_mode", False)
    _sync_from_mix()
    rng = data_bridge.input_ranges()

    page_header("Property Prediction", "Predict 7 mechanical & physical properties from a mix recipe.",
                "Module M1 · Ensemble predictor")

    left, right = st.columns([1, 1.35], gap="large")

    # ══ LEFT — mix recipe inputs ══════════════════════════════════════════════
    with left:
        with st.container(border=True):
            C.section("Mix recipe", "8 parameters")

            st.selectbox("Load archetype (pre-fill sliders)", ["—", *_ARCH.keys()],
                         key="m1_arch", on_change=_load_archetype)

            cur_plastic = ss.get("m1_plastic") or ss.mix["plastic_type"]
            chips = " ".join(
                f"<span class='pc-chip {p.lower()}' style='opacity:"
                f"{'1' if p == cur_plastic else '.45'}'>{p}</span>" for p in PLASTIC_TYPES)
            st.markdown("**Plastic type**", help="Recycled plastic aggregate stream")
            st.markdown(f"<div style='margin:-6px 0 6px'>{chips}</div>", unsafe_allow_html=True)
            # capture returns into locals — never reassign a widget-keyed session value
            sel = st.segmented_control("Plastic type", PLASTIC_TYPES, key="m1_plastic",
                                       label_visibility="collapsed")
            p_type = sel if sel is not None else ss.mix["plastic_type"]

            st.slider("Plastic replacement %  (by volume)", rng["replacement_pct"][0],
                      rng["replacement_pct"][1], key="m1_repl", step=0.5)
            st.slider("Plastic particle size (mm)", rng["particle_size_mm"][0],
                      rng["particle_size_mm"][1], key="m1_particle", step=0.5)
            st.slider("Water–cement ratio", rng["wc_ratio"][0], rng["wc_ratio"][1],
                      key="m1_wc", step=0.01)

            add = st.segmented_control("Additive type", ADDITIVE_TYPES, key="m1_additive",
                                       format_func=lambda x: _ADD_LABELS.get(x, x))
            a_type = add if add is not None else ss.mix["additive_type"]
            st.slider("Additive %", rng["additive_pct"][0], rng["additive_pct"][1],
                      key="m1_add_pct", step=0.5, disabled=(a_type == "none"))
            st.slider("Curing temperature (°C)", rng["curing_temp_c"][0], rng["curing_temp_c"][1],
                      key="m1_temp", step=1.0)
            st.slider("Curing duration (days)", int(rng["curing_days"][0]),
                      int(rng["curing_days"][1]), key="m1_days", step=1)

            live = st.toggle("⚡ Live re-prediction", value=False,
                             help="Re-run the ensemble on every change (first run warms models).")
            predict_clicked = st.button("▶ Predict properties", type="primary",
                                        use_container_width=True)

    mix = {
        "plastic_type": p_type, "replacement_pct": float(ss.m1_repl),
        "particle_size_mm": float(ss.m1_particle), "wc_ratio": float(ss.m1_wc),
        "additive_type": a_type,
        "additive_pct": float(ss.m1_add_pct) if a_type != "none" else 0.0,
        "curing_temp_c": float(ss.m1_temp), "curing_days": int(ss.m1_days),
    }

    # Auto-run the real ensemble once per session so the page opens on live
    # predictions instead of the seeded demo values. Cached, so it is a one-time
    # ~30 s warm-up; the explicit button below still forces a re-run any time.
    auto_run = (not ss.get("_m1_auto_ran")) and ss.prediction.get("source") != "real"

    if predict_clicked or auto_run or (live and mix != ss.mix):
        ss._m1_auto_ran = True
        ss.mix = mix
        spinner_msg = ("Warming XGBoost + Random Forest + DNN ensemble (first run ~30 s)…"
                       if auto_run and not predict_clicked
                       else "Running XGBoost + Random Forest + DNN ensemble…")
        with st.spinner(spinner_msg):
            ss.prediction = data_bridge.predict(mix)
            props = data_bridge.props_from_prediction(ss.prediction)
            ss.score = data_bridge.score(mix, props)
            ss.recommendation = data_bridge.recommend(mix, props)

    pred = ss.prediction

    # ══ RIGHT — predicted properties ══════════════════════════════════════════
    with right:
        top = st.columns([1.3, 1])
        with top[0]:
            C.section("Predicted profile", "7 properties")
            st.plotly_chart(charts.radar_7prop(pred["values"], dark=dark, height=300),
                            use_container_width=True, config={"displayModeBar": False})
        with top[1]:
            st.write("")
            st.markdown(C.badge_html("Ensemble · XGB + RF + DNN", "🧠"), unsafe_allow_html=True)
            st.write("")
            conf = "High" if not pred.get("uncertainty_flag") else "Guarded"
            st.markdown(C.badge_html(f"Confidence: {conf}", "🎯"), unsafe_allow_html=True)
            st.write("")
            C.source_chip(pred.get("source", "mock"))
            if pred.get("source") == "mock":
                st.caption("Backend model not loaded — showing demo values.")

        if pred.get("uncertainty_flag") or pred.get("low_coverage_targets"):
            lc = ", ".join(TARGET_META[t][0] for t in pred.get("low_coverage_targets", [])
                           if t in TARGET_META) or "one or more properties"
            C.callout(f"Low confidence on {lc} — consider targeted lab validation.")

        st.write("")
        # 7 spec cards (2-up)
        decs = {"density_kgm3": 0, "durability_index": 0, "thermal_conductivity_wm": 2}
        targets = list(TARGET_META.keys())
        for i in range(0, len(targets), 2):
            cols = st.columns(2)
            for col, t in zip(cols, targets[i:i+2]):
                label, unit, standard, (vmin, vmax), icon = TARGET_META[t]
                v = pred["values"].get(t)
                lo = pred["ci_low"].get(t, v); hi = pred["ci_high"].get(t, v)
                dec = decs.get(t, 1)
                status = "warn" if t in pred.get("low_coverage_targets", []) else "ok"
                with col:
                    C.metric_card(
                        label, v, unit=unit,
                        interval=f"90% PI  {lo:,.{dec}f} – {hi:,.{dec}f}" if v is not None else None,
                        status=status, standard=standard, icon=icon, dec=dec,
                        band=(lo, hi, vmin, vmax) if v is not None else None)
                    if st.button(f"Explain {label} ↗", key=f"exp_{t}", use_container_width=True):
                        ss.explain_target = t
                        nav.goto("explain")
