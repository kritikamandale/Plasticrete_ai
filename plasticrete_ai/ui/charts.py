"""
Plotly charts themed to the PlastiCrete palette (transparent background, mono
tick fonts, structural/amber/green colours). Every figure is returned so pages
render it with `st.plotly_chart(fig, use_container_width=True)`.
"""
from __future__ import annotations

import plotly.graph_objects as go

from ui.theme import PLASTIC_COLORS, TARGET_META, palette

_MONO = "JetBrains Mono, monospace"
_SANS = "Inter, sans-serif"


def _base(fig: go.Figure, dark: bool, height: int = 320, legend=False) -> go.Figure:
    pal = palette(dark)
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=28, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_SANS, size=12, color=pal["text"]),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=11)),
        hoverlabel=dict(font=dict(family=_MONO, size=12)),
    )
    grid = pal["border"]
    fig.update_xaxes(gridcolor=grid, zerolinecolor=grid, tickfont=dict(family=_MONO, size=10))
    fig.update_yaxes(gridcolor=grid, zerolinecolor=grid, tickfont=dict(family=_MONO, size=10))
    return fig


# ── 7-property radar ─────────────────────────────────────────────────────────
def radar_7prop(values: dict, dark: bool = False, height: int = 340) -> go.Figure:
    pal = palette(dark)
    labels, norm = [], []
    for t, (label, _u, _s, (vmin, vmax), _i) in TARGET_META.items():
        v = values.get(t)
        labels.append(label.replace(" ", "<br>"))
        norm.append(0 if v is None else max(0, min(100, (v - vmin) / (vmax - vmin) * 100)))
    labels.append(labels[0]); norm.append(norm[0])
    fig = go.Figure(go.Scatterpolar(
        r=norm, theta=labels, fill="toself",
        line=dict(color=pal["amber"], width=2),
        fillcolor="rgba(245,158,11,.18)",
        marker=dict(size=6, color=pal["amber"]),
        hovertemplate="%{theta}: %{r:.0f}/100<extra></extra>"))
    fig.update_layout(
        polar=dict(bgcolor="rgba(0,0,0,0)",
                   radialaxis=dict(visible=True, range=[0, 100], showticklabels=False,
                                   gridcolor=pal["border"]),
                   angularaxis=dict(gridcolor=pal["border"], tickfont=dict(size=10))))
    return _base(fig, dark, height)


# ── SHAP waterfall ───────────────────────────────────────────────────────────
def shap_waterfall(shap_dict: dict, final: float, unit: str = "MPa",
                   dark: bool = False, height: int = 360) -> go.Figure:
    pal = palette(dark)
    items = sorted(shap_dict.items(), key=lambda kv: -abs(kv[1]))
    contrib = sum(v for _, v in items)
    base = final - contrib
    x = ["Baseline"] + [k for k, _ in items] + ["Prediction"]
    y = [base] + [v for _, v in items] + [final]
    measure = ["absolute"] + ["relative"] * len(items) + ["total"]
    fig = go.Figure(go.Waterfall(
        orientation="v", measure=measure, x=x, y=y,
        text=[f"{base:.1f}"] + [f"{v:+.1f}" for _, v in items] + [f"{final:.1f}"],
        textposition="outside", textfont=dict(family=_MONO, size=10),
        connector=dict(line=dict(color=pal["border"])),
        increasing=dict(marker=dict(color=pal["green"])),
        decreasing=dict(marker=dict(color=pal["red"])),
        totals=dict(marker=dict(color=pal["primary"]))))
    fig.update_layout(yaxis_title=unit)
    fig.update_xaxes(tickangle=-30)
    return _base(fig, dark, height)


# ── gauge / score ring ───────────────────────────────────────────────────────
def gauge(value: float, title: str = "", vmax: float = 100, dark: bool = False,
          height: int = 260) -> go.Figure:
    pal = palette(dark)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        number=dict(font=dict(family=_MONO, size=44, color=pal["text"]), suffix=f" /{int(vmax)}"),
        gauge=dict(
            axis=dict(range=[0, vmax], tickfont=dict(family=_MONO, size=9), tickcolor=pal["border"]),
            bar=dict(color=pal["primary"], thickness=0.28),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            steps=[dict(range=[0, vmax*0.45], color="rgba(220,38,38,.22)"),
                   dict(range=[vmax*0.45, vmax*0.7], color="rgba(245,158,11,.22)"),
                   dict(range=[vmax*0.7, vmax], color="rgba(34,197,94,.22)")],
            threshold=dict(line=dict(color=pal["amber"], width=3), value=value)),
        title=dict(text=title, font=dict(family=_SANS, size=13, color=pal["muted"]))))
    return _base(fig, dark, height)


# ── Pareto scatter ───────────────────────────────────────────────────────────
def pareto_scatter(points: list[dict], dark: bool = False, height: int = 380,
                   n_visible: int | None = None) -> go.Figure:
    pal = palette(dark)
    pts = points if n_visible is None else points[:n_visible]
    cs = [p["cs"] for p in pts]; cost = [p["cost"] for p in pts]
    co2 = [p["co2"] for p in pts]; div = [p["diversion"] for p in pts]
    fig = go.Figure(go.Scatter(
        x=cs, y=cost, mode="markers",
        marker=dict(size=[8 + d*0.35 for d in div], color=co2, colorscale="YlGnBu",
                    showscale=True, reversescale=True,
                    colorbar=dict(title="CO₂<br>kg/m³", thickness=12, len=0.8,
                                  tickfont=dict(family=_MONO, size=9)),
                    line=dict(width=1, color="rgba(255,255,255,.5)"), opacity=0.85),
        customdata=list(zip(co2, div)),
        hovertemplate=("CS %{x:.1f} MPa<br>Cost ₹%{y:,.0f}/m³<br>"
                       "CO₂ %{customdata[0]:.0f} kg/m³<br>Diversion %{customdata[1]:.1f} kg/m³"
                       "<extra></extra>")))
    fig.update_layout(xaxis_title="Compressive Strength (MPa)", yaxis_title="Cost (₹/m³)")
    return _base(fig, dark, height)


# ── sensitivity tornado ──────────────────────────────────────────────────────
def sensitivity_tornado(sens: dict, dark: bool = False, height: int = 320) -> go.Figure:
    pal = palette(dark)
    order = sorted(sens.items(), key=lambda kv: max(abs(kv[1]["plus"]), abs(kv[1]["minus"])))
    labels = [k.replace("_", " ").title() for k, _ in order]
    plus = [v["plus"] for _, v in order]
    minus = [v["minus"] for _, v in order]
    fig = go.Figure()
    fig.add_bar(y=labels, x=plus, orientation="h", name="+10%",
                marker=dict(color=pal["amber"]), hovertemplate="+10%%: %{x:.2f} MPa<extra></extra>")
    fig.add_bar(y=labels, x=minus, orientation="h", name="−10%",
                marker=dict(color=pal["primary_2"]), hovertemplate="−10%%: %{x:.2f} MPa<extra></extra>")
    fig.update_layout(barmode="overlay", xaxis_title="Δ Compressive Strength (MPa)")
    return _base(fig, dark, height, legend=True)


# ── PDP lines ────────────────────────────────────────────────────────────────
def pdp_line(x, y, x_title: str, dark: bool = False, height: int = 280,
             y_title: str = "Compressive Strength (MPa)") -> go.Figure:
    pal = palette(dark)
    fig = go.Figure(go.Scatter(
        x=x, y=y, mode="lines+markers",
        line=dict(color=pal["primary_2"], width=3, shape="spline"),
        marker=dict(size=6, color=pal["amber"]),
        fill="tozeroy", fillcolor="rgba(62,82,119,.10)",
        hovertemplate="%{x}: %{y:.1f} MPa<extra></extra>"))
    fig.update_layout(xaxis_title=x_title, yaxis_title=y_title)
    return _base(fig, dark, height)


def ice_lines(ice: dict, dark: bool = False, height: int = 320) -> go.Figure:
    pal = palette(dark)
    x = ice["x"]
    fig = go.Figure()
    for ptype, color in PLASTIC_COLORS.items():
        if ptype in ice:
            fig.add_scatter(x=x, y=ice[ptype], mode="lines", name=ptype,
                            line=dict(color=color, width=2.5, shape="spline"),
                            hovertemplate=f"{ptype} @ %{{x}}%%: %{{y:.1f}} MPa<extra></extra>")
    fig.update_layout(xaxis_title="Plastic Replacement (%)",
                      yaxis_title="Compressive Strength (MPa)")
    return _base(fig, dark, height, legend=True)


# ── cluster scatter (PCA) ────────────────────────────────────────────────────
def cluster_scatter(points: list[dict], clusters: list[dict], dark: bool = False,
                    height: int = 420, mini: bool = False) -> go.Figure:
    pal = palette(dark)
    fig = go.Figure()
    by_cluster: dict = {}
    for p in points:
        by_cluster.setdefault(p["cluster"], {"x": [], "y": [], "c": p["color"]})
        by_cluster[p["cluster"]]["x"].append(p["x"])
        by_cluster[p["cluster"]]["y"].append(p["y"])
    for name, d in by_cluster.items():
        fig.add_scatter(x=d["x"], y=d["y"], mode="markers", name=name,
                        marker=dict(size=7 if not mini else 5, color=d["c"], opacity=0.55,
                                    line=dict(width=0)),
                        hovertemplate=f"{name}<extra></extra>")
    if not mini:
        for c in clusters:
            fig.add_scatter(x=[c["centroid"][0]], y=[c["centroid"][1]], mode="markers+text",
                            text=[str(c["id"])], textposition="middle center",
                            textfont=dict(family=_MONO, color="#fff", size=11),
                            marker=dict(size=26, color=c["color"], symbol="circle",
                                        line=dict(width=2, color="#fff")),
                            showlegend=False, hovertemplate=f"{c['name']}<extra></extra>")
    fig.update_layout(xaxis_title="PC1 — structural ↔ lightweighting",
                      yaxis_title="PC2 — durability ↔ workability")
    if mini:
        fig.update_layout(xaxis_title="", yaxis_title="")
        fig.update_xaxes(showticklabels=False); fig.update_yaxes(showticklabels=False)
    return _base(fig, dark, height, legend=not mini)


# ── PCA biplot ───────────────────────────────────────────────────────────────
def pca_biplot(dark: bool = False, height: int = 420) -> go.Figure:
    pal = palette(dark)
    loadings = {
        "replacement_pct": (0.9, -0.2), "wc_ratio": (0.5, -0.7), "additive_pct": (-0.7, 0.4),
        "curing_days": (-0.6, -0.5), "particle_size_mm": (0.6, 0.5), "curing_temp_c": (-0.3, 0.6),
        "compressive_strength": (-0.95, 0.1), "density": (-0.4, -0.8),
    }
    fig = go.Figure()
    for name, (dx, dy) in loadings.items():
        fig.add_scatter(x=[0, dx], y=[0, dy], mode="lines+text",
                        line=dict(color=pal["primary_2"], width=2),
                        text=["", name.replace("_", " ")], textposition="top center",
                        textfont=dict(size=10, color=pal["muted"]), showlegend=False,
                        hoverinfo="skip")
        fig.add_annotation(x=dx, y=dy, ax=0, ay=0, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5,
                           arrowcolor=pal["amber"])
    fig.update_layout(xaxis_title="PC1 (58% variance)", yaxis_title="PC2 (26% variance)")
    fig.update_xaxes(range=[-1.2, 1.2]); fig.update_yaxes(range=[-1.2, 1.2])
    return _base(fig, dark, height)


# ── comparison bar (embodied carbon / cost) ─────────────────────────────────
def comparison_bar(labels, values, colors, dark: bool = False, height: int = 240,
                   x_title: str = "", suffix: str = "") -> go.Figure:
    fig = go.Figure(go.Bar(
        y=labels, x=values, orientation="h", marker=dict(color=colors),
        text=[f"{v:,.0f}{suffix}" for v in values], textposition="auto",
        textfont=dict(family=_MONO, size=12),
        hovertemplate="%{y}: %{x:,.1f}<extra></extra>"))
    fig.update_layout(xaxis_title=x_title)
    return _base(fig, dark, height)


# ── feature importance bars (SHAP vs XGB gain) ───────────────────────────────
def importance_bars(feat_names, shap_imp, gain_imp, dark: bool = False, height: int = 340) -> go.Figure:
    pal = palette(dark)
    fig = go.Figure()
    fig.add_bar(y=feat_names, x=shap_imp, orientation="h", name="SHAP |mean|",
                marker=dict(color=pal["amber"]))
    fig.add_bar(y=feat_names, x=gain_imp, orientation="h", name="XGBoost gain",
                marker=dict(color=pal["primary_2"]))
    fig.update_layout(barmode="group", xaxis_title="relative importance")
    return _base(fig, dark, height, legend=True)


# ── heatmap (SHAP interaction / 2D PDP) ──────────────────────────────────────
def heatmap(z, x, y, x_title="", y_title="", cbar="value", dark: bool = False,
            height: int = 320) -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=z, x=x, y=y, colorscale="YlGnBu", reversescale=True,
        colorbar=dict(title=cbar, thickness=12, tickfont=dict(family=_MONO, size=9)),
        hovertemplate=f"{x_title}: %{{x}}<br>{y_title}: %{{y}}<br>{cbar}: %{{z:.1f}}<extra></extra>"))
    fig.update_layout(xaxis_title=x_title, yaxis_title=y_title)
    return _base(fig, dark, height)


# ── SHAP summary beeswarm (mock distribution) ────────────────────────────────
def beeswarm(features: list[str], dark: bool = False, height: int = 340) -> go.Figure:
    import random
    pal = palette(dark)
    rng = random.Random(11)
    fig = go.Figure()
    for i, feat in enumerate(features):
        spread = (len(features) - i) / len(features)
        xs = [rng.gauss(0, 0.6 * spread) + (0.4 * spread if rng.random() > .5 else -0.3 * spread)
              for _ in range(45)]
        ys = [i + rng.uniform(-0.28, 0.28) for _ in xs]
        vals = [x for x in xs]
        fig.add_scatter(x=xs, y=ys, mode="markers",
                        marker=dict(size=6, color=vals, colorscale=[[0, pal["primary_2"]], [1, pal["amber"]]],
                                    showscale=(i == 0),
                                    colorbar=dict(title="feature<br>value", thickness=10,
                                                  tickfont=dict(size=8)) if i == 0 else None,
                                    opacity=0.75, line=dict(width=0)),
                        showlegend=False, hoverinfo="skip")
    fig.update_layout(xaxis_title="SHAP value (impact on prediction)",
                      yaxis=dict(tickmode="array", tickvals=list(range(len(features))),
                                 ticktext=features))
    fig.add_vline(x=0, line=dict(color=pal["border"], width=1))
    return _base(fig, dark, height)


# ── objective weight radar (M2) ──────────────────────────────────────────────
def objective_radar(weights: dict, dark: bool = False, height: int = 300) -> go.Figure:
    pal = palette(dark)
    labels = ["Strength", "Cost", "CO₂", "Plastic<br>Diversion"]
    vals = [weights.get("compressive_strength", 0), weights.get("cost_per_m3", 0),
            weights.get("co2_per_m3", 0), weights.get("plastic_content_pct", 0)]
    labels.append(labels[0]); vals.append(vals[0])
    fig = go.Figure(go.Scatterpolar(
        r=vals, theta=labels, fill="toself", line=dict(color=pal["green"], width=2),
        fillcolor="rgba(34,197,94,.16)"))
    fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
                                 radialaxis=dict(range=[0, max(vals) or 1], showticklabels=False,
                                                 gridcolor=pal["border"]),
                                 angularaxis=dict(gridcolor=pal["border"])))
    return _base(fig, dark, height)
