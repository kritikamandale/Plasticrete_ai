"""M3 — Sustainability & Compliance scorecard."""
from __future__ import annotations

import datetime as _dt

import streamlit as st

from ui import charts, components as C, data_bridge
from ui.theme import BIS_STANDARDS, PALETTE, label_app, page_header


def _subscores(score: dict) -> dict:
    if score.get("subscores"):
        return score["subscores"]
    return {
        "Embodied-carbon reduction": min(100, max(0, score.get("co2_saving_pct", 0) / 30 * 100)),
        "Plastic diversion":         min(100, score.get("plastic_diversion_kg_m3", 0) / 200 * 100),
        "Recycled content":          min(100, score.get("recycled_content_pct", 15) * 3),
        "Local sourcing":            score.get("local_sourcing_pct", 80),
        "BIS compliance":            100 if score.get("bis_overall_pass") else 45,
    }


def render():
    ss = st.session_state
    dark = ss.get("dark_mode", False)
    score = ss.score
    mix = ss.mix
    props = data_bridge.props_from_prediction(ss.prediction)

    page_header("Sustainability & Compliance",
                "Procurement-ready scorecard: carbon, diversion, BIS & green-rating credits.",
                "Module M3 · Scoring engine")
    C.source_chip(score.get("source", "mock"))

    # ── hero: gauge + sub-scores ──────────────────────────────────────────────
    g, s = st.columns([1, 1.4], gap="large")
    with g:
        with st.container(border=True):
            st.plotly_chart(charts.gauge(score["sustainability_score"], "Sustainability Score",
                                         dark=dark, height=250),
                            use_container_width=True, config={"displayModeBar": False})
            st.markdown(
                f"<div style='text-align:center;margin-top:-8px'>"
                f"<span class='pc-pill pass'>Grade {score['sustainability_grade']}</span></div>",
                unsafe_allow_html=True)
    with s:
        with st.container(border=True):
            C.section("Score composition")
            for name, val in _subscores(score).items():
                color = PALETTE["green"] if val >= 70 else (PALETTE["amber"] if val >= 45 else PALETTE["red"])
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;font-size:.85rem;"
                    f"font-weight:600;margin-bottom:2px'><span>{name}</span>"
                    f"<span style='font-family:JetBrains Mono,monospace'>{val:.0f}</span></div>"
                    f"<div class='pc-band' style='height:8px;margin-bottom:12px'>"
                    f"<span style='left:0;width:{val:.0f}%;background:{color};opacity:.85'></span></div>",
                    unsafe_allow_html=True)

    st.write("")
    # ── carbon + diversion cards ──────────────────────────────────────────────
    cc, dc = st.columns(2, gap="large")
    with cc:
        with st.container(border=True):
            C.section("Embodied carbon", "vs conventional M20")
            st.markdown(
                f"<span class='pc-metric-value sm'>−{score['co2_saving_pct']:.0f}%</span>"
                f"<span class='pc-metric-unit'>  {score.get('co2_saved_kgco2e_m3',0):.0f} kg CO₂e/m³ saved</span>",
                unsafe_allow_html=True)
            st.plotly_chart(
                charts.comparison_bar(
                    ["This mix", "Conventional M20"],
                    [score["embodied_carbon_kgco2e_m3"], score.get("baseline_co2_kgco2e_m3", 365.71)],
                    [PALETTE["green"], PALETTE["muted"]], dark=dark, height=170,
                    x_title="kg CO₂e / m³"),
                use_container_width=True, config={"displayModeBar": False})
    with dc:
        with st.container(border=True):
            C.section("Plastic diversion", "per m³ of material")
            st.markdown(
                f"<span class='pc-metric-value sm'>{score['plastic_diversion_kg_m3']:.0f}</span>"
                f"<span class='pc-metric-unit'> kg/m³</span>", unsafe_allow_html=True)
            bottles = score["pet_bottle_equiv"]
            fill = min(100, bottles / 500 * 100)
            st.markdown(
                f"<div class='pc-card-sub' style='margin:8px 0 4px'>🍶 ≈ "
                f"<b>{bottles:.0f}</b> × 500 ml PET bottles</div>"
                f"<div class='pc-band' style='height:16px'>"
                f"<span style='left:0;width:{fill:.0f}%;"
                f"background:linear-gradient(90deg,#06B6D4,#22C55E);opacity:.9'></span></div>",
                unsafe_allow_html=True)
            st.caption(f"Recycled content ≈ {score.get('recycled_content_pct', 18):.0f}% · "
                       f"local sourcing ≈ {score.get('local_sourcing_pct', 80):.0f}%")

    st.write("")
    # ── BIS compliance checklist ──────────────────────────────────────────────
    C.section("BIS compliance checklist", "Indian standards")
    checklist = data_bridge.bis_checklist(props)
    for row in checklist:
        C.compliance_row(row)

    st.write("")
    # ── green rating + SDG ────────────────────────────────────────────────────
    gcol, sdgcol = st.columns([1, 1.3], gap="large")
    with gcol:
        C.section("Green-building credits")
        for name, got, total, note in [
            ("IGBC", score.get("igbc_total_credits", 0), 3, "New Buildings · materials"),
            ("GRIHA", score.get("griha_material_criterion_pts", 0), 2, "Sustainable materials"),
            ("LEED", score.get("leed_total_points", 0), 2, "MR credit · recycled content"),
        ]:
            pct = min(100, got / total * 100) if total else 0
            st.markdown(
                f"<div class='pc-card' style='margin-bottom:10px;padding:12px 16px'>"
                f"<div style='display:flex;justify-content:space-between'>"
                f"<b>{name}</b><span style='font-family:JetBrains Mono,monospace;font-weight:700'>"
                f"{got:.0f}/{total}</span></div>"
                f"<div class='pc-card-sub'>{note}</div>"
                f"<div class='pc-band' style='height:6px;margin-top:8px'>"
                f"<span style='left:0;width:{pct:.0f}%;background:var(--pc-green);opacity:.85'></span>"
                f"</div></div>", unsafe_allow_html=True)
    with sdgcol:
        C.section("SDG contribution")
        C.sdg_ribbon(counters={
            3: "healthier air", 9: "circular industry", 11: "resilient cities",
            12: f"{score['plastic_diversion_kg_m3']:.0f} kg/m³ diverted",
            13: f"−{score['co2_saving_pct']:.0f}% CO₂"})
        st.write("")
        st.markdown(
            "<div class='pc-card-sub'>Each mix advances five UN Sustainable Development "
            "Goals — from responsible consumption (12) to climate action (13).</div>",
            unsafe_allow_html=True)

    st.write("")
    # ── remediation + report ──────────────────────────────────────────────────
    C.section("Remediation guidance", "SHAP-suggested adjustments")
    C.callout(f"Top limiting factor: {score.get('top_negative_factor','—').replace('_',' ')}  "
              f"· estimated gain if applied: +{score.get('estimated_score_gain',0):.0f} pts", icon="🔧")
    for i in (1, 2, 3):
        act = score.get(f"remediation_action_{i}")
        if act:
            st.markdown(f"&nbsp;&nbsp;**{i}.** {act}")

    st.write("")
    try:
        pdf_bytes = _build_report_pdf(mix, props, score, checklist)
        st.download_button("⬇ Generate Compliance Report (PDF)", pdf_bytes,
                           file_name=f"plasticrete_compliance_{_dt.date.today()}.pdf",
                           mime="application/pdf", type="primary")
    except Exception as exc:  # noqa: BLE001 — fall back to HTML if reportlab is unavailable
        st.download_button("⬇ Generate Compliance Report (HTML)", _build_report(mix, props, score),
                           file_name=f"plasticrete_compliance_{_dt.date.today()}.html",
                           mime="text/html", type="primary")
        st.caption(f"PDF export unavailable ({exc}); serving HTML instead. "
                   "Install `reportlab` to enable PDF.")
    with st.expander("Preview report"):
        st.markdown(_build_report(mix, props, score), unsafe_allow_html=True)


def _build_report(mix, props, score) -> str:
    today = _dt.date.today().isoformat()
    return f"""
<div style='font-family:Inter,sans-serif;max-width:720px'>
<h2 style='font-family:Space Grotesk'>PlastiCrete AI — Sustainability & Compliance Report</h2>
<p style='color:#64748B'>Generated {today} · {score.get('source','mock')} model</p>
<h3>Mix formulation</h3>
<p style='font-family:JetBrains Mono,monospace'>{mix['plastic_type']} · {mix['replacement_pct']:.0f}% ·
{mix['particle_size_mm']:.1f} mm · w/c {mix['wc_ratio']:.2f} · {mix['additive_type']}
{mix['additive_pct']:.0f}% · {mix['curing_temp_c']:.0f}°C · {mix['curing_days']}d</p>
<h3>Sustainability score: {score['sustainability_score']:.0f}/100 (Grade {score['sustainability_grade']})</h3>
<ul>
<li>Embodied carbon: {score['embodied_carbon_kgco2e_m3']:.0f} kg CO₂e/m³ (−{score['co2_saving_pct']:.0f}% vs M20)</li>
<li>Plastic diverted: {score['plastic_diversion_kg_m3']:.0f} kg/m³ ≈ {score['pet_bottle_equiv']:.0f} PET bottles</li>
<li>BIS overall: {'PASS' if score.get('bis_overall_pass') else 'REVIEW'}</li>
<li>Green credits — IGBC {score.get('igbc_total_credits',0):.0f}/3 ·
GRIHA {score.get('griha_material_criterion_pts',0):.0f}/2 · LEED {score.get('leed_total_points',0):.0f}/2</li>
</ul>
<p style='color:#64748B;font-size:.8rem'>Predicted compressive strength
{props.get('compressive_strength_mpa',0):.1f} MPa · density {props.get('density_kgm3',0):.0f} kg/m³.
Report generated by PlastiCrete AI.</p>
</div>
"""


def _build_report_pdf(mix, props, score, checklist) -> bytes:
    """Render the sustainability & compliance report as a print-ready PDF (bytes)."""
    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    # ── palette ───────────────────────────────────────────────────────────────
    PRIMARY = colors.HexColor(PALETTE["primary"])
    PRIMARY2 = colors.HexColor(PALETTE["primary_2"])
    GREEN = colors.HexColor(PALETTE["green"])
    AMBER = colors.HexColor(PALETTE["amber"])
    RED = colors.HexColor(PALETTE["red"])
    MUTED = colors.HexColor(PALETTE["muted"])
    BORDER = colors.HexColor(PALETTE["border"])
    ROW_ALT = colors.HexColor("#F1F5F9")

    _STATUS_COLOR = {"pass": GREEN, "warn": AMBER, "fail": RED}
    _STATUS_LABEL = {"pass": "PASS", "warn": "MARGINAL", "fail": "FAIL"}

    today = _dt.date.today().isoformat()
    source = str(score.get("source", "mock"))

    # ── paragraph styles ──────────────────────────────────────────────────────
    ss = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=ss["Normal"], fontName="Helvetica",
                          fontSize=9.5, leading=13, textColor=colors.HexColor("#0F172A"))
    body_muted = ParagraphStyle("body_muted", parent=body, textColor=MUTED, fontSize=8.5, leading=12)
    cell = ParagraphStyle("cell", parent=body, fontSize=8.8, leading=11.5)
    cell_muted = ParagraphStyle("cell_muted", parent=cell, textColor=MUTED, fontSize=8.2, leading=10.5)
    h_sec = ParagraphStyle("h_sec", parent=body, fontName="Helvetica-Bold",
                           fontSize=11.5, leading=14, textColor=PRIMARY, spaceBefore=4, spaceAfter=6)
    title = ParagraphStyle("title", parent=body, fontName="Helvetica-Bold",
                           fontSize=17, leading=20, textColor=colors.white)
    subtitle = ParagraphStyle("subtitle", parent=body, fontSize=9,
                              leading=12, textColor=colors.HexColor("#CBD5E1"))

    def sec(txt: str) -> Paragraph:
        return Paragraph(txt, h_sec)

    # ── header band ───────────────────────────────────────────────────────────
    grade = score.get("sustainability_grade", "—")
    sscore = score.get("sustainability_score", 0)
    header = Table(
        [[Paragraph("PlastiCrete&nbsp;AI", title),
          Paragraph(f"Sustainability Score<br/><b>{sscore:.0f}/100 &nbsp; Grade {grade}</b>",
                    ParagraphStyle("score", parent=subtitle, alignment=TA_RIGHT,
                                   fontSize=10, textColor=colors.white, leading=14))],
         [Paragraph("Sustainability &amp; Compliance Report", subtitle),
          Paragraph(f"Generated {today} · {source} model",
                    ParagraphStyle("gen", parent=subtitle, alignment=TA_RIGHT))]],
        colWidths=[105 * mm, 65 * mm])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    # ── mix formulation ───────────────────────────────────────────────────────
    mix_rows = [
        ["Plastic type", str(mix.get("plastic_type", "—")),
         "Replacement", f"{mix.get('replacement_pct', 0):.0f}%"],
        ["Particle size", f"{mix.get('particle_size_mm', 0):.1f} mm",
         "W/C ratio", f"{mix.get('wc_ratio', 0):.2f}"],
        ["Additive", f"{mix.get('additive_type', 'none')} · {mix.get('additive_pct', 0):.0f}%",
         "Curing", f"{mix.get('curing_temp_c', 0):.0f}°C · {mix.get('curing_days', 0):.0f} d"],
    ]
    mix_tbl = Table(mix_rows, colWidths=[30 * mm, 55 * mm, 30 * mm, 55 * mm])
    mix_tbl.setStyle(TableStyle([
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 8.6),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 8.6),
        ("FONT", (1, 0), (1, -1), "Courier", 8.8),
        ("FONT", (3, 0), (3, -1), "Courier", 8.8),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("TEXTCOLOR", (2, 0), (2, -1), MUTED),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
    ]))

    # ── key metrics ───────────────────────────────────────────────────────────
    baseline = score.get("baseline_co2_kgco2e_m3", 365.71)
    bis_pass = score.get("bis_overall_pass")
    metric_rows = [
        ["Embodied carbon",
         f"{score.get('embodied_carbon_kgco2e_m3', 0):.0f} kg CO2e/m3",
         f"-{score.get('co2_saving_pct', 0):.0f}% vs conventional M20 ({baseline:.0f})"],
        ["Plastic diversion",
         f"{score.get('plastic_diversion_kg_m3', 0):.0f} kg/m3",
         f"= {score.get('pet_bottle_equiv', 0):.0f} x 500 ml PET bottles"],
        ["Recycled content",
         f"{score.get('recycled_content_pct', 18):.0f}%",
         f"Local sourcing = {score.get('local_sourcing_pct', 80):.0f}%"],
        ["BIS overall",
         "PASS" if bis_pass else "REVIEW",
         f"{sum(1 for r in checklist if r.get('passed'))}/{len(checklist)} standards passed"],
    ]
    metric_data = [[Paragraph(r[0], cell), Paragraph(f"<b>{r[1]}</b>", cell),
                    Paragraph(r[2], cell_muted)] for r in metric_rows]
    metric_tbl = Table(metric_data, colWidths=[38 * mm, 45 * mm, 87 * mm])
    metric_style = [
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]
    for i in range(len(metric_rows)):
        if i % 2 == 1:
            metric_style.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    metric_tbl.setStyle(TableStyle(metric_style))

    # ── BIS compliance checklist ──────────────────────────────────────────────
    bis_head = [Paragraph(f"<b>{c}</b>", ParagraphStyle("th", parent=cell, textColor=colors.white))
                for c in ("Standard", "Result", "Threshold", "Status")]
    bis_data = [bis_head]
    status_cells = []  # (row_index, color) for per-row status colouring
    for i, row in enumerate(checklist, start=1):
        code, name = BIS_STANDARDS.get(row["key"], (row["key"].upper(), ""))
        status = row.get("status", "pass" if row.get("passed") else "fail")
        std = f"<b>{code}</b><br/><font size=7 color='#64748B'>{name}</font>"
        result = row.get("detail", "")
        thr = row.get("threshold", "")
        label = _STATUS_LABEL.get(status, "—")
        bis_data.append([
            Paragraph(std, cell),
            Paragraph(result, cell),
            Paragraph(thr, cell_muted),
            Paragraph(f"<b>{label}</b>",
                      ParagraphStyle("stat", parent=cell, alignment=TA_CENTER, textColor=colors.white)),
        ])
        status_cells.append((i, _STATUS_COLOR.get(status, MUTED)))
    bis_tbl = Table(bis_data, colWidths=[36 * mm, 62 * mm, 48 * mm, 24 * mm], repeatRows=1)
    bis_style = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY2),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
    ]
    for r, col in status_cells:
        bis_style.append(("BACKGROUND", (3, r), (3, r), col))
    bis_tbl.setStyle(TableStyle(bis_style))

    # ── green-building credits ────────────────────────────────────────────────
    green_rows = [
        ("IGBC", score.get("igbc_total_credits", 0), 3, "New Buildings · materials"),
        ("GRIHA", score.get("griha_material_criterion_pts", 0), 2, "Sustainable materials"),
        ("LEED", score.get("leed_total_points", 0), 2, "MR credit · recycled content"),
    ]
    green_data = [[Paragraph(f"<b>{n}</b>", cell), Paragraph(f"{got:.0f} / {tot}", cell),
                   Paragraph(note, cell_muted)] for n, got, tot, note in green_rows]
    green_tbl = Table(green_data, colWidths=[30 * mm, 30 * mm, 110 * mm])
    green_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))

    # ── remediation ───────────────────────────────────────────────────────────
    top_factor = str(score.get("top_negative_factor", "—")).replace("_", " ")
    gain = score.get("estimated_score_gain", 0)
    rem_flow = [Paragraph(
        f"<b>Top limiting factor:</b> {top_factor} &nbsp;·&nbsp; "
        f"estimated gain if applied: <b>+{gain:.0f} pts</b>", body)]
    for i in (1, 2, 3):
        act = score.get(f"remediation_action_{i}")
        if act:
            rem_flow.append(Spacer(1, 3))
            rem_flow.append(Paragraph(f"<b>{i}.</b> {act}", body))

    # ── assemble ──────────────────────────────────────────────────────────────
    story = [
        header, Spacer(1, 10),
        sec("Mix formulation"), mix_tbl, Spacer(1, 10),
        sec("Sustainability metrics"), metric_tbl, Spacer(1, 10),
        sec("BIS compliance checklist"), bis_tbl, Spacer(1, 10),
        sec("Green-building credits"), green_tbl, Spacer(1, 10),
        sec("Remediation guidance"), *rem_flow, Spacer(1, 14),
        Paragraph(
            f"Predicted compressive strength {props.get('compressive_strength_mpa', 0):.1f} MPa · "
            f"density {props.get('density_kgm3', 0):.0f} kg/m3 · "
            f"water absorption {props.get('water_absorption_pct', 0):.1f}%. "
            f"Predictions from a {source} model; verify against lab testing before procurement. "
            "Report generated by PlastiCrete AI.", body_muted),
    ]

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
        title="PlastiCrete AI — Sustainability & Compliance Report",
        author="PlastiCrete AI")
    doc.build(story)
    return buf.getvalue()
