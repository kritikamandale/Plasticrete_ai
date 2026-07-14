"""Material Insights — clustering · PCA · DBSCAN."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ui import charts, components as C, data_bridge, mock_data, nav
from ui.theme import page_header


def render():
    ss = st.session_state
    dark = ss.get("dark_mode", False)

    page_header("Material Insights",
                "Research-grade exploration of the formulation landscape.",
                "Unsupervised · K-Means · PCA · DBSCAN")

    left, right = st.columns([1.4, 1], gap="large")
    with left:
        C.section("Formulation archetype map", "PCA-reduced · 5 K-Means clusters")
        st.plotly_chart(
            charts.cluster_scatter(mock_data.cluster_scatter_points(), mock_data.CLUSTERS,
                                   dark=dark, height=430),
            use_container_width=True, config={"displayModeBar": False})
    with right:
        C.section("PCA biplot", "PC1 58% · PC2 26% · 84% total")
        st.plotly_chart(charts.pca_biplot(dark=dark, height=430),
                        use_container_width=True, config={"displayModeBar": False})

    st.write("")
    C.section("Cluster centroids", "load any archetype into M1")
    cols = st.columns(len(mock_data.CLUSTERS), gap="small")
    for col, c in zip(cols, mock_data.CLUSTERS):
        with col:
            with st.container(border=True):
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:8px'>"
                    f"<span style='width:12px;height:12px;border-radius:50%;background:{c['color']}'></span>"
                    f"<b style='font-size:.85rem'>{c['id']}. {c['name']}</b></div>"
                    f"<div class='pc-card-sub' style='margin-top:6px'>{c['desc']}</div>",
                    unsafe_allow_html=True)
                if st.button("Load into M1 →", key=f"cl_{c['id']}", use_container_width=True):
                    ss.mix = dict(c["params"])
                    for k, wk in [("plastic_type", "m1_plastic"), ("replacement_pct", "m1_repl"),
                                  ("particle_size_mm", "m1_particle"), ("wc_ratio", "m1_wc"),
                                  ("additive_type", "m1_additive"), ("additive_pct", "m1_add_pct"),
                                  ("curing_temp_c", "m1_temp"), ("curing_days", "m1_days")]:
                        ss[wk] = c["params"][k]
                    nav.goto("m1")

    st.write("")
    b1, b2 = st.columns([1, 1.2], gap="large")
    with b1:
        C.section("DBSCAN anomalies", "flagged outliers for review")
        df = pd.DataFrame(mock_data.dbscan_outliers()).rename(columns={
            "mix_id": "Mix", "plastic_type": "Plastic", "replacement_pct": "Repl %",
            "wc_ratio": "w/c", "compressive_strength_mpa": "CS", "note": "Why flagged"})
        st.dataframe(df, use_container_width=True, hide_index=True)
    with b2:
        C.section("Cross-tab", "input cluster → output performance")
        rows = [c["name"] for c in mock_data.CLUSTERS]
        cols_x = ["Structural", "Paving/Durable", "Lightweight"]
        z = [[42, 8, 2], [3, 12, 51], [5, 44, 14], [1, 9, 38], [48, 11, 3]]
        st.plotly_chart(
            charts.heatmap(z, cols_x, rows, x_title="Output performance",
                           y_title="", cbar="mixes", dark=dark, height=300),
            use_container_width=True, config={"displayModeBar": False})
