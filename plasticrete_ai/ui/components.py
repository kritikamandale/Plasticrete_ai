"""
Reusable, premium-styled UI components. Most render directly via st.markdown with
the CSS classes defined in `.streamlit/style.css`; a few `*_html` helpers return
fragments for inline composition.
"""
from __future__ import annotations

from typing import Optional

import streamlit as st

from ui import nav
from ui.theme import (
    APP_META, BIS_STANDARDS, PLASTIC_COLORS, SDG_INFO, plastic_class,
)


# ── inline HTML fragments ─────────────────────────────────────────────────────
def plastic_chip_html(ptype: str) -> str:
    return f"<span class='pc-chip {plastic_class(ptype)}'>{ptype}</span>"


def status_dot_html(status: str) -> str:
    s = status if status in ("ok", "warn", "fail") else "ok"
    return f"<span class='pc-dot {s}'></span>"


def badge_html(text: str, icon: str = "") -> str:
    ic = f"{icon} " if icon else ""
    return f"<span class='pc-badge'>{ic}{text}</span>"


def _band_html(low, mean, high, vmin, vmax) -> str:
    span = max(vmax - vmin, 1e-9)
    lo = max(0, min(100, (low - vmin) / span * 100))
    hi = max(0, min(100, (high - vmin) / span * 100))
    mk = max(0, min(100, (mean - vmin) / span * 100))
    return (f"<div class='pc-band'><span style='left:{lo:.1f}%;width:{max(hi-lo,1):.1f}%'></span>"
            f"<b style='left:{mk:.1f}%'></b></div>")


def _fmt(v, dec: int = 1) -> str:
    if v is None:
        return "—"
    if dec == 0:
        return f"{v:,.0f}"
    return f"{v:,.{dec}f}"


# ── metric / spec cards ───────────────────────────────────────────────────────
def metric_card(label, value, unit="", interval=None, delta=None, status=None,
                standard=None, icon="", dec=1, band=None):
    """Full spec-sheet card: value · unit · interval band · standard · status dot."""
    dot = status_dot_html(status) if status else ""
    val = _fmt(value, dec) if isinstance(value, (int, float)) else str(value)
    unit_html = f"<span class='pc-metric-unit'>{unit}</span>" if unit else ""
    parts = [f"<div class='pc-card pc-lift'>",
             f"<div class='pc-metric-label'>{icon} {label}"
             f"<span style='margin-left:auto'>{dot}</span></div>",
             f"<div><span class='pc-metric-value sm'>{val}</span>{unit_html}</div>"]
    if band is not None:
        lo, hi, vmin, vmax = band
        parts.append(_band_html(lo, hi, value, vmin, vmax))
    if interval:
        parts.append(f"<div class='pc-metric-interval'>{interval}</div>")
    if delta:
        cls = "pc-delta-up" if str(delta).startswith(("+", "−", "-")) is False else "pc-delta-down"
        parts.append(f"<div class='pc-metric-interval {cls}'>{delta}</div>")
    if standard:
        parts.append(f"<div class='pc-standard'>STANDARD · {standard}</div>")
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def kpi_card(label, value, unit="", sub="", delta=None, delta_good=True, icon=""):
    """Large dashboard KPI card with big mono number."""
    unit_html = f"<span class='pc-metric-unit'>{unit}</span>" if unit else ""
    sub_html = ""
    if delta is not None:
        cls = "pc-delta-up" if delta_good else "pc-delta-down"
        sub_html = f"<div class='pc-metric-interval {cls}'>{delta}</div>"
    if sub:
        sub_html += f"<div class='pc-metric-interval'>{sub}</div>"
    st.markdown(
        f"<div class='pc-card pc-lift'>"
        f"<div class='pc-metric-label'>{icon} {label}</div>"
        f"<div><span class='pc-metric-value'>{value}</span>{unit_html}</div>"
        f"{sub_html}</div>",
        unsafe_allow_html=True,
    )


def kpi_row(cards: list[dict]):
    cols = st.columns(len(cards))
    for col, c in zip(cols, cards):
        with col:
            kpi_card(**c)


# ── compliance ────────────────────────────────────────────────────────────────
def compliance_pill_html(status: str, text: str) -> str:
    icon = {"pass": "✓", "warn": "!", "fail": "✕"}.get(status, "•")
    return f"<span class='pc-pill {status}'>{icon} {text}</span>"


def compliance_row(row: dict):
    code, name = BIS_STANDARDS.get(row["key"], (row["key"], ""))
    status = row.get("status", "pass" if row.get("passed") else "fail")
    label = {"pass": "PASS", "warn": "MARGINAL", "fail": "FAIL"}.get(status, "—")
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(
                f"<b style='font-family:JetBrains Mono,monospace'>{code}</b> "
                f"<span class='pc-card-sub'>{name}</span><br>"
                f"<span class='pc-card-sub'>{row.get('detail','')}</span>",
                unsafe_allow_html=True)
        with c2:
            st.markdown(
                f"<div style='text-align:right'>{compliance_pill_html(status, label)}</div>",
                unsafe_allow_html=True)
        if row.get("fix"):
            st.markdown(
                f"<div class='pc-callout' style='margin-top:8px'>🔧 "
                f"<span><b>SHAP fix →</b> {row['fix']}</span></div>",
                unsafe_allow_html=True)


# ── SDG ───────────────────────────────────────────────────────────────────────
def sdg_badge_html(n: int, counter: str = "") -> str:
    color, label = SDG_INFO.get(n, ("#64748B", f"SDG {n}"))
    cnt = f"<div class='l' style='opacity:.85'>{counter}</div>" if counter else ""
    return (f"<div class='pc-sdg' style='background:{color}'>"
            f"<div class='n'>{n}</div><div class='l'>{label}</div>{cnt}</div>")


def sdg_ribbon(nums=(3, 9, 11, 12, 13), counters=None):
    counters = counters or {}
    cols = st.columns(len(nums))
    for col, n in zip(cols, nums):
        with col:
            st.markdown(sdg_badge_html(n, counters.get(n, "")), unsafe_allow_html=True)


# ── workflow rail ─────────────────────────────────────────────────────────────
def workflow_rail(active_key: str = "m1"):
    steps = [("m1", "M1", "Predict"), ("m3", "M3", "Score"),
             ("m4", "M4", "Recommend"), ("m2", "M2", "Optimise")]
    html = ["<div class='pc-rail'>"]
    for i, (key, badge, label) in enumerate(steps):
        active = " active" if key == active_key else ""
        html.append(f"<div class='step{active}'><span class='b'>{badge}</span>{label}</div>")
        if i < len(steps) - 1:
            html.append("<span class='arrow'>→</span>")
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


# ── citation card ─────────────────────────────────────────────────────────────
def citation_card(a: dict):
    sim = max(0.0, 1.0 - a.get("l2_distance", 0.5))
    app = APP_META.get(a.get("primary_application", ""),
                       (a.get("primary_application", ""), "", False))[0]
    props = a.get("properties", {})
    prop_str = " · ".join(
        f"{k.replace('_',' ').replace('mpa','MPa').replace('kgm3','kg/m³').replace('pct','%').title()}: "
        f"{v:.1f}" for k, v in list(props.items())[:3])
    st.markdown(
        f"<div class='pc-citation'>"
        f"<span class='pc-sim'>sim {sim:.2f}</span>"
        f"<div class='au'>#{a.get('rank','?')} · {a.get('author','')} "
        f"<span class='pc-card-sub'>({a.get('year','')})</span></div>"
        f"<div class='meta'>{a.get('journal','')}</div>"
        f"<div class='doi'>DOI {a.get('doi','')}</div>"
        f"<div class='pc-card-sub' style='margin-top:6px'>▸ {app}</div>"
        f"<div class='meta' style='margin-top:4px'>{prop_str}</div>"
        f"</div>",
        unsafe_allow_html=True)


# ── progress ring (application suitability) ──────────────────────────────────
def progress_ring_html(value: float, color: str) -> str:
    return (f"<div class='pc-ring' style='--v:{value:.0f};--c:{color}'>"
            f"<b>{value:.0f}%</b></div>")


def application_card(key: str, score: float):
    label, icon, structural = APP_META.get(key, (key, "🧱", False))
    color = "#16A34A" if score >= 70 else ("#F59E0B" if score >= 50 else "#DC2626")
    badge = ("<span class='pc-pill pass'>✓ Structural OK</span>" if structural and score >= 60
             else "<span class='pc-pill warn'>Non-structural</span>")
    with st.container(border=True):
        c1, c2 = st.columns([1, 1.4])
        with c1:
            st.markdown(progress_ring_html(score, color), unsafe_allow_html=True)
        with c2:
            st.markdown(
                f"<div style='font-size:1.4rem'>{icon}</div>"
                f"<div style='font-weight:600;font-size:.9rem;line-height:1.15'>{label}</div>",
                unsafe_allow_html=True)
        st.markdown(badge, unsafe_allow_html=True)


# ── quick-action tile (dashboard) ────────────────────────────────────────────
def quick_action_tile(icon: str, title: str, desc: str, target: str, key: str):
    st.markdown(
        f"<div class='pc-tile'><div class='ico'>{icon}</div>"
        f"<div class='t'>{title}</div><div class='d'>{desc}</div></div>",
        unsafe_allow_html=True)
    if st.button(f"Open {title} →", key=key, use_container_width=True):
        nav.goto(target)


# ── misc ──────────────────────────────────────────────────────────────────────
def section(title: str, eyebrow: str = ""):
    if eyebrow:
        st.markdown(f"<div class='pc-eyebrow-dark'>{eyebrow}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='pc-section'>{title}</div>", unsafe_allow_html=True)


def callout(text: str, icon: str = "⚠️"):
    st.markdown(f"<div class='pc-callout'>{icon} <span>{text}</span></div>",
                unsafe_allow_html=True)


def source_chip(source: str):
    if source == "real":
        st.markdown("<span class='pc-pill pass'>● live model</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='pc-pill warn'>● demo data</span>", unsafe_allow_html=True)
