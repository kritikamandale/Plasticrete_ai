"""
PlastiCrete AI — Professional PDF Mix Design Report Generator
==============================================================
Generates a fully-formatted, multi-page A4 PDF using reportlab.

Sections:
  1. Header & Branding (PlastiCrete.ai, session metadata)
  2. Mix Recipe Table (ingredients & proportions per m³)
  3. Predicted Properties Table (7 targets with 90% CI bands)
  4. BIS Standards Compliance Checklist
  5. LCA Carbon Footprint & Sustainability Score Block
  6. Green Rating Credits (IGBC / GRIHA / LEED)
  7. Top-3 Influential Features (SHAP-derived bar chart)
  8. Remediation Advisory
  9. Literature Analogues (RAG top-3 with DOI)
 10. Disclaimer & QR Footer
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    FrameBreak,
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics import renderPDF

# ── Colour Palette ─────────────────────────────────────────────────────────────
C_SLATE_950  = colors.HexColor("#020617")
C_SLATE_800  = colors.HexColor("#1e293b")
C_SLATE_600  = colors.HexColor("#475569")
C_SLATE_300  = colors.HexColor("#cbd5e1")
C_SLATE_100  = colors.HexColor("#f1f5f9")
C_EMERALD_700 = colors.HexColor("#047857")
C_EMERALD_100 = colors.HexColor("#d1fae5")
C_RED_700    = colors.HexColor("#b91c1c")
C_RED_100    = colors.HexColor("#fee2e2")
C_BLUE_700   = colors.HexColor("#1d4ed8")
C_BLUE_100   = colors.HexColor("#dbeafe")
C_AMBER_700  = colors.HexColor("#b45309")
C_AMBER_100  = colors.HexColor("#fef3c7")
C_WHITE      = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm


# ── Style Helpers ──────────────────────────────────────────────────────────────

def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    def s(name, **kw) -> ParagraphStyle:
        return ParagraphStyle(name, parent=base["Normal"], **kw)
    return {
        "h1":         s("h1", fontSize=20, leading=24, textColor=C_SLATE_950,
                         fontName="Helvetica-Bold", spaceAfter=4),
        "h2":         s("h2", fontSize=13, leading=17, textColor=C_SLATE_800,
                         fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4),
        "h3":         s("h3", fontSize=10, leading=13, textColor=C_SLATE_800,
                         fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=2),
        "body":       s("body", fontSize=8.5, leading=12, textColor=C_SLATE_800),
        "caption":    s("caption", fontSize=7.5, leading=10, textColor=C_SLATE_600),
        "badge_pass": s("badge_pass", fontSize=8, leading=10, textColor=C_EMERALD_700,
                         fontName="Helvetica-Bold"),
        "badge_fail": s("badge_fail", fontSize=8, leading=10, textColor=C_RED_700,
                         fontName="Helvetica-Bold"),
        "mono":       s("mono", fontSize=8, leading=11, fontName="Courier",
                         textColor=C_SLATE_800),
        "small_grey": s("small_grey", fontSize=7, leading=9, textColor=C_SLATE_600),
        "center":     s("center", fontSize=8, leading=11, alignment=TA_CENTER,
                         textColor=C_SLATE_600),
        "th":         s("th", fontSize=7, leading=9, textColor=C_WHITE,
                         fontName="Helvetica-Bold"),
        "td":         s("td", fontSize=7.5, leading=9.5, textColor=C_SLATE_800),
        "td_r":       s("td_r", fontSize=7.5, leading=9.5, textColor=C_SLATE_800,
                         alignment=TA_RIGHT),
    }


def _soft(value: Any) -> str:
    """Escape text and wrap long filenames on punctuation."""
    text = "-" if value is None or value == "" else str(value)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    words = []
    for word in text.split(" "):
        if len(word) <= 18:
            words.append(word)
            continue
        pieces: list[str] = []
        buf: list[str] = []
        for ch in word:
            buf.append(ch)
            if ch in "_-/" and len(buf) >= 6:
                pieces.append("".join(buf))
                buf = []
        if buf:
            pieces.append("".join(buf))
        words.append("<br/>".join(pieces))
    return " ".join(words)


def _P(value: Any, style: ParagraphStyle, html: bool = False) -> Paragraph:
    return Paragraph(str(value) if html else _soft(value), style)


def _tbl_style(header_color=C_SLATE_800, alt=True) -> TableStyle:
    cmds = [
        ("BACKGROUND",  (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR",   (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 8),
        ("FONTSIZE",    (0, 1), (-1, -1), 8),
        ("ROWBACKGROUND", (0, 1), (-1, -1),
         [C_WHITE, C_SLATE_100] if alt else [C_WHITE]),
        ("GRID",        (0, 0), (-1, -1), 0.3, C_SLATE_300),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_SLATE_100]),
    ]
    return TableStyle(cmds)


# ── Header / Footer Canvas ─────────────────────────────────────────────────────

def _header_footer(canvas, doc, mix_params, session_id):
    canvas.saveState()
    w, h = A4

    # Top brand bar
    canvas.setFillColor(C_SLATE_950)
    canvas.rect(0, h - 14 * mm, w, 14 * mm, fill=1, stroke=0)
    canvas.setFillColor(C_WHITE)
    canvas.setFont("Helvetica-Bold", 10)
    brand = "PlastiCrete.ai"
    canvas.drawString(MARGIN, h - 9 * mm, brand)
    brand_w = canvas.stringWidth(brand, "Helvetica-Bold", 10)
    canvas.setFillColor(C_EMERALD_700)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(MARGIN + brand_w + 8, h - 9 * mm, "Mix Design Report")
    canvas.setFillColor(C_SLATE_300)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawRightString(w - MARGIN, h - 9 * mm,
                           f"Session {session_id}  |  {datetime.now().strftime('%d %b %Y, %H:%M')}")

    # Bottom footer
    canvas.setFillColor(C_SLATE_100)
    canvas.rect(0, 0, w, 10 * mm, fill=1, stroke=0)
    canvas.setStrokeColor(C_SLATE_300)
    canvas.line(MARGIN, 10 * mm, w - MARGIN, 10 * mm)
    canvas.setFillColor(C_SLATE_600)
    canvas.setFont("Helvetica", 6.5)
    canvas.drawString(MARGIN, 4 * mm,
                      "Screening estimate. Not a substitute for IS-compliant laboratory testing "
                      "or a structural engineer's sign-off.")
    canvas.drawRightString(w - MARGIN, 4 * mm, f"Page {doc.page}")
    canvas.restoreState()


# ── Section Builders ───────────────────────────────────────────────────────────

def _section_mix_recipe(mix_params: dict, st: dict) -> list:
    from modules.shared.mass_balance import compute as compute_mass_balance

    balance = compute_mass_balance(mix_params)
    plastic_pct = mix_params.get("replacement_pct", 0)
    th, td, num = st["th"], st["td"], st["td_r"]
    data = [[
        _P("Constituent", th),
        _P("Quantity<br/>kg/m3", th, html=True),
        _P("Factor", th),
        _P("CO2e<br/>kg/m3", th, html=True),
        _P("Cost<br/>INR/m3", th, html=True),
        _P("Date", th),
        _P("Source", th),
    ]]
    for row in balance["rows"]:
        data.append([
            _P(row["material"], td),
            _P(f"{row['quantity_kg_m3']:.2f}", num),
            _P(f"{row['co2_factor_kg_per_kg']}", num),
            _P(f"{row['co2_kgco2e_m3']:.2f}", num),
            _P(f"{row['cost_inr_m3']:.2f}", num),
            _P(row["co2_factor_date"], td),
            _P(row["co2_factor_source"], td),
        ])
    data.append([
        _P("Total", td),
        _P("—", num),
        _P("—", num),
        _P(f"{balance['co2_kgco2e_m3']:.2f}", num),
        _P(f"{balance['cost_inr_m3']:.2f}", num),
        _P(balance["factor_date"], td),
        _P(balance["table_id"], td),
    ])
    tbl = Table(data, colWidths=[28*mm, 20*mm, 16*mm, 20*mm, 20*mm, 22*mm, 48*mm], repeatRows=1)
    tbl.setStyle(_tbl_style())
    return [
        Paragraph("Mass balance (per m³)", st["h2"]),
        Paragraph(
            f"{balance['basis']} "
            f"This mix diverts <b>{balance['plastic_kg_m3']:.2f} kg</b> of "
            f"{balance['plastic_type']} "
            f"({balance['pet_bottle_equiv']} PET-bottle equivalents at 25 g).",
            st["body"],
        ),
        Spacer(1, 3*mm),
        tbl,
        Spacer(1, 2*mm),
        Paragraph(
            f"Curing {mix_params.get('curing_temp_c', 27)}°C for "
            f"{mix_params.get('curing_days', 28)} days does not change the bill of materials. "
            f"Replacement level {plastic_pct}% by volume of the fine aggregate. "
            f"Baseline {balance['baseline_co2_kgco2e_m3']:.2f} kg CO2e/m3 "
            f"({balance['baseline_source']}, {balance['baseline_date']}).",
            st["caption"],
        ),
    ]


def _section_predicted_properties(prediction: dict, st: dict) -> list:
    UNITS = {
        "compressive_strength_mpa": "MPa",
        "flexural_strength_mpa": "MPa",
        "split_tensile_mpa": "MPa",
        "density_kgm3": "kg/m³",
        "water_absorption_pct": "%",
        "thermal_conductivity_wm": "W/m·K",
        "durability_index": "0-100",
    }
    LABELS = {
        "compressive_strength_mpa": "Compressive Strength",
        "flexural_strength_mpa": "Flexural Strength",
        "split_tensile_mpa": "Split Tensile Strength",
        "density_kgm3": "Bulk Density",
        "water_absorption_pct": "Water Absorption",
        "thermal_conductivity_wm": "Thermal Conductivity",
        "durability_index": "Durability Index",
    }

    preds = prediction.get("predictions", {})
    th, td, num = st["th"], st["td"], st["td_r"]
    data = [[
        _P("Property", th),
        _P("Predicted mean", th),
        _P("90% CI low", th),
        _P("90% CI high", th),
        _P("Unit", th),
    ]]
    for key, label in LABELS.items():
        prop = preds.get(key, {})
        mean = prop.get("mean")
        low  = prop.get("ci_90_low")
        high = prop.get("ci_90_high")
        data.append([
            _P(label, td),
            _P(f"{mean:.2f}" if mean is not None else "—", num),
            _P(f"{low:.2f}" if low is not None else "—", num),
            _P(f"{high:.2f}" if high is not None else "—", num),
            _P(UNITS[key], td),
        ])

    tbl = Table(data, colWidths=[52*mm, 32*mm, 30*mm, 32*mm, 28*mm], repeatRows=1)
    tbl.setStyle(_tbl_style(C_BLUE_700))

    unc = prediction.get("uncertainty_flag", False)
    flag_note = (
        "⚠  High Uncertainty Region: Mix parameters lie outside the training data manifold. "
        "CI bands are widened. Lab verification strongly recommended."
        if unc else
        "✓  Prediction confidence is within normal operating range of the ensemble models."
    )
    flag_style = st["badge_fail"] if unc else st["badge_pass"]

    return [
        Paragraph("AI-Predicted Mechanical & Physical Properties", st["h2"]),
        Paragraph(
            "Ensemble prediction with a 90% interval. Compressive R2 on the held-out "
            "evaluation report is 0.91 (n=455). This is not a laboratory certificate.",
            st["body"],
        ),
        Spacer(1, 3*mm),
        tbl,
        Spacer(1, 2*mm),
        Paragraph(flag_note, flag_style),
    ]


def _section_bis_compliance(score: dict, st: dict) -> list:
    gates = score.get("use_class_gates") or []
    if not gates:
        return [
            Paragraph("Use-class gate", st["h2"]),
            Paragraph(
                "No per-product gate was attached to this score. "
                "A blended pass across unrelated standards is not reported.",
                st["body"],
            ),
        ]

    labels = {
        "allowed": "ALLOWED",
        "verification_batch": "CAST BATCH",
        "lab_trial": "LAB TRIAL",
        "refused": "REFUSED",
    }
    th, td = st["th"], st["td"]
    data = [[
        _P("Product", th),
        _P("Standard", th),
        _P("Status", th),
        _P("What the bound says", th),
    ]]
    for gate in gates:
        data.append([
            _P(gate.get("label", ""), td),
            _P(gate.get("standard", ""), td),
            _P(labels.get(gate.get("status"), gate.get("status", "")), td),
            _P(gate.get("message", ""), td),
        ])
    tbl = Table(data, colWidths=[36*mm, 32*mm, 24*mm, 82*mm], repeatRows=1)
    style = _tbl_style(C_SLATE_800)
    for index, gate in enumerate(gates, start=1):
        status = gate.get("status")
        if status == "allowed":
            bg, fg = C_EMERALD_100, C_EMERALD_700
        elif status == "refused":
            bg, fg = C_RED_100, C_RED_700
        else:
            bg, fg = C_AMBER_100, C_AMBER_700
        style.add("BACKGROUND", (2, index), (2, index), bg)
        style.add("TEXTCOLOR", (2, index), (2, index), fg)
        style.add("FONTNAME", (2, index), (2, index), "Helvetica-Bold")
    tbl.setStyle(style)
    return [
        Paragraph("Use-class gate", st["h2"]),
        Paragraph(
            "Each product is allowed only when its own standard clears on the "
            "conservative side of the 90% interval. Structural concrete is a lab trial, "
            "never a certificate. When the interval crosses the grade line, cast one verification batch.",
            st["body"],
        ),
        Spacer(1, 3*mm),
        tbl,
    ]


def _section_lca_sustainability(score: dict, st: dict) -> list:
    s_score = score.get("sustainability_score", 0)
    grade   = score.get("sustainability_grade", "C")
    co2     = score.get("embodied_carbon_kgco2e_m3", 0)
    saving  = score.get("co2_saving_pct", 0)
    diversion = score.get("plastic_diversion_kg_m3", 0)
    bottles = score.get("pet_bottle_equiv", 0)
    igbc    = score.get("igbc_total_credits", 0)
    griha   = score.get("griha_material_criterion_pts", 0)
    leed    = score.get("leed_total_points", 0)
    total_gc = score.get("total_green_credits", 0)

    grade_color = {
        "A+": C_EMERALD_700, "A": C_EMERALD_700,
        "B": C_AMBER_700, "C": C_RED_700,
    }.get(grade, C_SLATE_600)

    th, td, num = st["th"], st["td"], st["td_r"]
    lca_data = [
        [_P("LCA metric", th), _P("Value", th)],
        [_P("Embodied carbon", td), _P(f"{co2:.1f} kg CO2e/m3", num)],
        [_P("CO2 saving vs conventional M20", td), _P(f"{saving:.1f}%", num)],
        [_P("Plastic diverted from landfill", td), _P(f"{diversion:.1f} kg/m3", num)],
        [_P("PET-bottle equivalent", td), _P(f"{int(bottles)} bottles/m3", num)],
    ]
    lca_tbl = Table(lca_data, colWidths=[110*mm, 64*mm], repeatRows=1)
    lca_tbl.setStyle(_tbl_style(C_EMERALD_700))

    green_data = [
        [_P("Green rating scheme", th), _P("Credits", th), _P("Criterion", th)],
        [_P("IGBC Green Homes / Buildings", td), _P(f"{igbc:.1f} pts", num), _P("Recycled content and thermal", td)],
        [_P("GRIHA (BEE/TERI)", td), _P(f"{griha:.1f} pts", num), _P("Embodied energy, waste", td)],
        [_P("LEED v4 Materials and Resources", td), _P(f"{leed:.1f} pts", num), _P("Recycled content", td)],
        [_P("Total green credits", td), _P(f"{total_gc:.1f} pts", num), _P("All schemes combined", td)],
    ]
    green_tbl = Table(green_data, colWidths=[78*mm, 28*mm, 68*mm], repeatRows=1)
    green_tbl.setStyle(_tbl_style(C_EMERALD_700))

    return [
        Paragraph("Life Cycle Assessment (LCA) & Sustainability Score", st["h2"]),
        Paragraph(
            "Cradle-to-gate embodied carbon from the shared mass-balance table "
            "(ICE v4.1 factors, dated on each row). "
            "Green-rating figures below are quantities a consultant can check. "
            "This report does not file an IGBC, GRIHA, or LEED rating. "
            f"Baseline: {score.get('mass_balance', {}).get('baseline_co2_kgco2e_m3', 365.71)} kg CO2e/m3.",
            st["body"],
        ),
        Spacer(1, 3*mm),
        lca_tbl,
        Spacer(1, 4*mm),
        Paragraph("Green Building Rating Credits", st["h3"]),
        green_tbl,
        Spacer(1, 3*mm),
        Paragraph(
            f"<b>Overall Sustainability Score: {s_score}/100 (Grade {grade})</b>",
            ParagraphStyle("score_line", fontSize=12, textColor=grade_color,
                           fontName="Helvetica-Bold", spaceAfter=2),
        ),
    ]


def _section_shap(prediction: dict, st: dict) -> list:
    """Build a simple horizontal bar-like SHAP influence table."""
    shap_vals = prediction.get("shap_values", {})
    cs_shap   = shap_vals.get("compressive_strength_mpa", {})
    if not cs_shap:
        return []

    sorted_feats = sorted(cs_shap.items(), key=lambda x: abs(x[1]), reverse=True)[:6]
    th, td, num = st["th"], st["td"], st["td_r"]
    data = [[
        _P("Feature", th),
        _P("SHAP contribution (MPa)", th),
        _P("Direction", th),
    ]]
    for feat, val in sorted_feats:
        direction = "Positive" if val >= 0 else "Negative"
        data.append([_P(feat.replace("_", " "), td), _P(f"{val:+.2f}", num), _P(direction, td)])

    tbl = Table(data, colWidths=[88*mm, 46*mm, 40*mm], repeatRows=1)
    style = _tbl_style(C_BLUE_700)
    for i, (_, val) in enumerate(sorted_feats, start=1):
        if val >= 0:
            style.add("TEXTCOLOR", (2, i), (2, i), C_EMERALD_700)
        else:
            style.add("TEXTCOLOR", (2, i), (2, i), C_RED_700)
        style.add("FONTNAME", (2, i), (2, i), "Helvetica-Bold")
    tbl.setStyle(style)

    return [
        Paragraph("Feature Influence Analysis (SHAP — Compressive Strength)", st["h2"]),
        Paragraph(
            "SHAP (SHapley Additive exPlanations) values quantify each input feature's "
            "marginal contribution to the predicted compressive strength. "
            "Positive = increases CS; Negative = decreases CS vs model baseline.",
            st["body"],
        ),
        Spacer(1, 3*mm),
        tbl,
    ]


def _section_remediation(score: dict, st: dict) -> list:
    actions = [
        score.get("remediation_action_1", ""),
        score.get("remediation_action_2", ""),
        score.get("remediation_action_3", ""),
    ]
    neg_factor = score.get("top_negative_factor", "")
    gain = score.get("estimated_score_gain", 0)

    items = []
    items.append(Paragraph("Remediation Advisory", st["h2"]))
    gain_text = (
        f" Implementing the actions below is estimated to improve the sustainability score by <b>+{gain:.1f} points</b>."
        if gain else ""
    )
    items.append(Paragraph(
        f"<b>Top limiting factor:</b> {neg_factor}.{gain_text}",
        st["body"],
    ))
    items.append(Spacer(1, 3*mm))
    for i, action in enumerate(actions, 1):
        if action:
            items.append(Paragraph(f"<b>{i}.</b> {action}", st["body"]))
            items.append(Spacer(1, 2*mm))
    return items


def _section_rag_analogues(recommendation: dict, st: dict) -> list:
    analogues = recommendation.get("rag_analogues", [])
    if not analogues:
        return []

    th, td, num = st["th"], st["td"], st["td_r"]
    data = [[
        _P("Rank", th),
        _P("Authors (year)", th),
        _P("Journal", th),
        _P("Application", th),
        _P("CS MPa", th),
        _P("DOI", th),
    ]]
    for a in analogues[:3]:
        props = a.get("properties", {})
        cs = props.get("compressive_strength_mpa")
        hide_doi = a.get("verified") is False or not a.get("doi") or str(a.get("id", "")).startswith("SYN_") or a.get("doi") == "verify-on-publisher"
        data.append([
            _P(a.get("rank", ""), td),
            _P(f"{a.get('author', '')} ({a.get('year', '')})", td),
            _P(a.get("journal", ""), td),
            _P(str(a.get("primary_application", "")).replace("_", " "), td),
            _P(f"{cs:.1f}" if isinstance(cs, float) else "—", num),
            _P("" if hide_doi else a.get("doi"), td),
        ])

    tbl = Table(data, colWidths=[14*mm, 36*mm, 36*mm, 32*mm, 18*mm, 38*mm], repeatRows=1)
    tbl.setStyle(_tbl_style(C_SLATE_800))

    return [
        Paragraph("Literature Analogues — Vector RAG Retrieval (Top 3)", st["h2"]),
        Paragraph(
            "Nearest peer-reviewed mixes retrieved by FAISS L2 search across a 15-dimensional "
            "property embedding space (15D = 7 mechanical + 8 mix parameters).",
            st["body"],
        ),
        Spacer(1, 3*mm),
        tbl,
    ]


def _section_cost_benefit(recommendation: dict, st: dict) -> list:
    cb = recommendation.get("cost_benefit", {})
    if not cb:
        return []

    th, td, num = st["th"], st["td"], st["td_r"]
    data = [
        [
            _P("Cost metric", th),
            _P("Plastic-waste concrete", th),
            _P("Conventional concrete", th),
            _P("Saving", th),
        ],
        [
            _P("Cost per m3 (INR)", td),
            _P(f"Rs {cb.get('plastic_mix_cost_inr_m3', 0):,.0f}", num),
            _P(f"Rs {cb.get('conventional_cost_inr_m3', 0):,.0f}", num),
            _P(f"Rs {cb.get('cost_saving_inr_m3', 0):,.0f} ({cb.get('cost_saving_pct', 0):.1f}%)", num),
        ],
        [
            _P("Cost per m2 product", td),
            _P(f"Rs {cb.get('plastic_mix_cost_inr_m2', 0):,.0f}", num),
            _P(f"Rs {cb.get('conventional_cost_inr_m2', 0):,.0f}", num),
            _P(f"Rs {cb.get('cost_saving_inr_m2', 0):,.0f}", num),
        ],
        [
            _P("Plastic aggregate input", td),
            _P(f"{cb.get('plastic_kg_per_m3', 0):.1f} kg/m3", num),
            _P("0 kg/m3", num),
            _P("—", num),
        ],
    ]
    tbl = Table(data, colWidths=[42*mm, 42*mm, 46*mm, 44*mm], repeatRows=1)
    tbl.setStyle(_tbl_style(C_BLUE_700))

    primary = recommendation.get("primary_application", "").replace("_", " ").title()
    conf    = recommendation.get("primary_confidence_pct", 0)

    return [
        Paragraph("Recommended Application & Cost–Benefit Analysis", st["h2"]),
        Paragraph(
            f"<b>Primary recommended application:</b> {primary} "
            f"(RF classifier confidence: {conf:.1f}%). "
            f"Product yield: {cb.get('product_yield_m2_per_m3', 7):.1f} m²/m³.",
            st["body"],
        ),
        Spacer(1, 3*mm),
        tbl,
    ]


def _qr_drawing(url: str, size_mm: float = 28):
    from reportlab.graphics.barcode import qr
    from reportlab.graphics.shapes import Drawing

    widget = qr.QrCodeWidget(url)
    bounds = widget.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    drawing = Drawing(
        size_mm * mm,
        size_mm * mm,
        transform=[size_mm * mm / width, 0, 0, size_mm * mm / height, 0, 0],
    )
    drawing.add(widget)
    return drawing


def _section_batch(batch: dict, qr_url: str, st: dict) -> list:
    def shown(value, suffix=""):
        if value is None or value == "":
            return "Not yet measured"
        if isinstance(value, float):
            return f"{value:.2f}{suffix}"
        return f"{value}{suffix}"

    th, td, num = st["th"], st["td"], st["td_r"]
    rows = [
        ("Batch", batch.get("id", "—")),
        ("Plant", batch.get("plant_name", "—")),
        ("Model", batch.get("model_version", "—")),
        ("Cast date", shown(batch.get("cast_date"))),
        ("Predicted 28-day mean", shown(batch.get("predicted_cs_mean"), " MPa")),
        ("90% interval", (
            f"{shown(batch.get('predicted_cs_low'))} to {shown(batch.get('predicted_cs_high'))} MPa"
            if batch.get("predicted_cs_low") is not None else "Not supplied"
        )),
        ("Measured 7-day strength", shown(batch.get("measured_cs_7d"), " MPa")),
        ("Measured 28-day strength", shown(batch.get("measured_cs_28d"), " MPa")),
        ("Measured absorption", shown(batch.get("measured_absorption_pct"), " %")),
        ("Error (measured - predicted)", shown(batch.get("error_mpa"), " MPa")),
    ]
    calibration = batch.get("calibration") or {}
    n_pairs = calibration.get("n_pairs") or 0
    status = "Unvalidated" if n_pairs == 0 else calibration.get("message") or f"Calibrated on {n_pairs} pairs"
    rows.append(("Validation status", status))
    data = [[_P("Field", th), _P("Value", th)]]
    data += [[_P(label, td), _P(value, num)] for label, value in rows]
    tbl = Table(data, colWidths=[62*mm, 112*mm], repeatRows=1)
    tbl.setStyle(_tbl_style(C_SLATE_800))
    story = [
        Paragraph("Batch passport", st["h2"]),
        Paragraph(
            "Recipe, prediction, lab result, carbon, and allowed uses for this cast. "
            "The QR code opens the same record.",
            st["body"],
        ),
        Spacer(1, 3*mm),
        tbl,
    ]
    if qr_url:
        story += [
            Spacer(1, 3*mm),
            _qr_drawing(qr_url),
            Paragraph(qr_url, st["caption"]),
        ]
    return story


# ── Main Public Function ───────────────────────────────────────────────────────

def generate_report(
    mix_params: dict,
    prediction: dict,
    score: dict,
    recommendation: dict,
    session_id: str = "OFFLINE",
    batch: dict | None = None,
    qr_url: str | None = None,
) -> bytes:
    """
    Generate a professional PDF mix design report.

    Args:
        mix_params:     8 mix design parameters (same dict as MixInput)
        prediction:     PredictionResponse dict (with predictions + shap_values)
        score:          ScoreResponse dict
        recommendation: RecommendationResponse dict
        session_id:     Optional session identifier for header

    Returns:
        PDF as bytes — pass directly to FastAPI StreamingResponse
    """
    buf = io.BytesIO()
    st  = _styles()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=20*mm,
        bottomMargin=16*mm,
        title="PlastiCrete AI — Mix Design Report",
        author="PlastiCrete.ai",
        subject="Plastic-Waste Composite Concrete Analysis",
    )

    story: list[Any] = []

    # ── Cover block ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("PlastiCrete<font color='#047857'>.ai</font>", st["h1"]))
    story.append(Paragraph("Plastic-Waste Composite Concrete — Mix Design Report", st["h2"]))

    label_style = ParagraphStyle("meta_label", parent=st["td"], fontName="Helvetica-Bold", textColor=C_SLATE_600)
    meta_rows = [
        ("Generated", datetime.now().strftime("%d %B %Y, %H:%M IST")),
        ("Session ID", session_id),
        ("Mix type", f"{mix_params.get('plastic_type', '—')} aggregate concrete"),
        ("Replacement level", f"{float(mix_params.get('replacement_pct', 0)):.1f}% vol."),
        ("Standards scope", "Use-class gates: IS 15658, IS 2185, IS 456"),
        ("Model version", (batch or {}).get("model_version") or "m1-ensemble evaluation_report.json compressive R2 0.9104"),
    ]
    meta_data = [[_P(label, label_style), _P(value, st["td"])] for label, value in meta_rows]
    meta_tbl = Table(meta_data, colWidths=[42*mm, 132*mm])
    meta_tbl.setStyle(TableStyle([
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID",       (0, 0), (-1, -1), 0.2, C_SLATE_300),
        ("BACKGROUND", (0, 0), (-1, -1), C_SLATE_100),
    ]))
    story.append(meta_tbl)
    story.append(HRFlowable(width="100%", thickness=1, color=C_SLATE_300, spaceAfter=6))

    # ── Sections ─────────────────────────────────────────────────────────────
    story += _section_mix_recipe(mix_params, st)
    story.append(Spacer(1, 5*mm))
    story += _section_predicted_properties(prediction, st)
    story.append(Spacer(1, 5*mm))
    story += _section_bis_compliance(score, st)
    story.append(Spacer(1, 5*mm))
    story += _section_lca_sustainability(score, st)
    story.append(Spacer(1, 5*mm))
    story += _section_cost_benefit(recommendation, st)
    story.append(Spacer(1, 5*mm))
    story += _section_shap(prediction, st)
    story.append(Spacer(1, 5*mm))
    story += _section_remediation(score, st)
    story.append(Spacer(1, 5*mm))
    story += _section_rag_analogues(recommendation, st)
    if batch:
        story.append(Spacer(1, 5*mm))
        story += _section_batch(batch, qr_url or "", st)

    # ── Disclaimer (final) ───────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_SLATE_300))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "<b>About this report:</b> Compressive strength on the held-out evaluation "
        "(models/m1/evaluation_report.json) has R2 0.91 (n=455). The files in this "
        "repository are UCI Yeh plain concrete and PlastiCreteAI_M1_Final_2000.csv. "
        "Literature CSVs named in the README are not in the repository. "
        "Carbon and cost on this page are the shared mass-balance table.",
        st["small_grey"],
    ))

    # Build
    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, mix_params, session_id),
        onLaterPages=lambda c, d: _header_footer(c, d, mix_params, session_id),
    )
    return buf.getvalue()
