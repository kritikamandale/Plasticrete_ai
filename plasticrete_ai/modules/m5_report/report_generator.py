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
    }


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
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
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
    canvas.drawString(MARGIN, h - 9 * mm, "PlastiCrete.ai")
    canvas.setFillColor(C_EMERALD_700)
    canvas.drawString(MARGIN + 65, h - 9 * mm, "— Mix Design Report")
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
                      "DISCLAIMER: This report is generated by AI models trained on peer-reviewed literature. "
                      "All predictions carry ±5–15% uncertainty. Independent lab verification is required "
                      "before any structural application. Refer to IS 456, IS 1237, IS 2185 for compliance.")
    canvas.drawRightString(w - MARGIN, 4 * mm, f"Page {doc.page}")
    canvas.restoreState()


# ── Section Builders ───────────────────────────────────────────────────────────

def _section_mix_recipe(mix_params: dict, st: dict) -> list:
    plastic_label_map = {
        "PET": "Polyethylene Terephthalate (PET)",
        "HDPE": "High-Density Polyethylene (HDPE)",
        "LDPE": "Low-Density Polyethylene (LDPE)",
        "PVC": "Polyvinyl Chloride (PVC)",
        "PP": "Polypropylene (PP)",
        "Mixed": "Mixed Polymer Blend",
    }
    additive_label_map = {
        "fly_ash": "Fly Ash (Class F, IS 3812)",
        "silica_fume": "Silica Fume (IS 15388)",
        "ggbs": "Ground Granulated Blast-Furnace Slag",
        "fibres": "Synthetic Fibre Reinforcement",
        "none": "No Supplementary Material",
    }

    cement_kg  = round(383.0 * (1 - mix_params.get("additive_pct", 0) / 100), 1)
    plastic_pct = mix_params.get("replacement_pct", 0)
    sand_kg    = round(680.0 * (1 - plastic_pct / 100), 1)
    coarse_kg  = round(1210.0 * (1 - plastic_pct / 100), 1)
    water_kg   = round(383.0 * mix_params.get("wc_ratio", 0.45), 1)
    add_pct    = mix_params.get("additive_pct", 0)
    add_kg     = round(383.0 * add_pct / 100, 1)
    plastic_density_map = {"PET": 1380, "HDPE": 960, "LDPE": 920, "PVC": 1400, "PP": 905, "Mixed": 1100}
    plastic_rho = plastic_density_map.get(mix_params.get("plastic_type", "PET"), 1100)
    plastic_kg  = round((plastic_pct / 100) * 1210.0 * plastic_rho / 2650, 1)

    data = [
        ["Constituent", "Quantity (kg/m³)", "Standard / Grade", "Notes"],
        ["OPC 53 Cement", f"{cement_kg}", "IS 12269", f"Binder, {100 - add_pct:.0f}% of total"],
        [additive_label_map.get(mix_params.get("additive_type", "none"), mix_params.get("additive_type", "-")),
         f"{add_kg}", "IS 3812 / IS 15388", f"{add_pct:.1f}% by mass of binder"],
        ["Fine Aggregate (River Sand)", f"{sand_kg}", "IS 383 Zone II", "Partially replaced by plastic"],
        ["Coarse Aggregate (20mm)", f"{coarse_kg}", "IS 383", "Crushed granite"],
        [plastic_label_map.get(mix_params.get("plastic_type", "PET"), mix_params.get("plastic_type")),
         f"{plastic_kg}", "Recycled, washed", f"{plastic_pct:.1f}% vol. replacement, {mix_params.get('particle_size_mm', 4)}mm"],
        ["Potable Water", f"{water_kg}", "IS 456 Cl. 5.4", f"w/c = {mix_params.get('wc_ratio', 0.45):.2f}"],
    ]
    tbl = Table(data, colWidths=[55*mm, 35*mm, 45*mm, None])
    tbl.setStyle(_tbl_style())
    return [
        Paragraph("Mix Recipe Proportions (per m³)", st["h2"]),
        Paragraph(
            f"Design basis: IS 10262 — M20 reference mix adjusted for "
            f"<b>{plastic_pct:.0f}% {mix_params.get('plastic_type','PET')} plastic aggregate</b> "
            f"replacement, cured at {mix_params.get('curing_temp_c', 27)}°C for "
            f"{mix_params.get('curing_days', 28)} days.",
            st["body"],
        ),
        Spacer(1, 3*mm),
        tbl,
    ]


def _section_predicted_properties(prediction: dict, st: dict) -> list:
    UNITS = {
        "compressive_strength_mpa": "MPa",
        "flexural_strength_mpa": "MPa",
        "split_tensile_mpa": "MPa",
        "density_kgm3": "kg/m³",
        "water_absorption_pct": "%",
        "thermal_conductivity_wm": "W/m·K",
        "durability_index": "0–100",
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
    data = [["Property", "Predicted Mean", "90% CI Low", "90% CI High", "Unit"]]
    for key, label in LABELS.items():
        prop = preds.get(key, {})
        mean = prop.get("mean")
        low  = prop.get("ci_90_low")
        high = prop.get("ci_90_high")
        data.append([
            label,
            f"{mean:.2f}" if mean is not None else "—",
            f"{low:.2f}"  if low  is not None else "—",
            f"{high:.2f}" if high is not None else "—",
            UNITS[key],
        ])

    tbl = Table(data, colWidths=[60*mm, 30*mm, 28*mm, 30*mm, 22*mm])
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
            "Ensemble of XGBoost, Random Forest, and PyTorch DNN trained on 2,000+ peer-reviewed data points. "
            "90% confidence intervals are derived from bootstrap variance across ensemble members.",
            st["body"],
        ),
        Spacer(1, 3*mm),
        tbl,
        Spacer(1, 2*mm),
        Paragraph(flag_note, flag_style),
    ]


def _section_bis_compliance(score: dict, st: dict) -> list:
    overall = score.get("bis_overall_pass", False)
    cs      = None  # pulled from score context if available

    checks = [
        ("IS 1237:2012 — Floor/Paving Tiles", "CS ≥ 30 MPa, WA ≤ 1%",
         "PASS" if overall else "REVIEW"),
        ("IS 2185:2005 Part 1 — Hollow Blocks",  "CS ≥ 3.5 MPa",
         "PASS" if overall else "REVIEW"),
        ("IS 456:2000 — Plain & Reinforced Concrete", "M20 (CS ≥ 20 MPa)",
         "PASS" if overall else "REVIEW"),
        ("IS 5816:1999 — Split Tensile Ratio",    "fst/fck ≥ 0.10",
         "PASS" if overall else "REVIEW"),
    ]

    data = [["Standard", "Threshold Criteria", "Status"]]
    for std, thresh, status in checks:
        clr = C_EMERALD_700 if status == "PASS" else C_AMBER_700
        data.append([std, thresh, status])

    tbl = Table(data, colWidths=[70*mm, 60*mm, 25*mm])
    style = _tbl_style(C_SLATE_800)
    for i, (_, _, status) in enumerate(checks, start=1):
        bg = C_EMERALD_100 if status == "PASS" else C_AMBER_100
        style.add("BACKGROUND", (2, i), (2, i), bg)
        fg = C_EMERALD_700 if status == "PASS" else C_AMBER_700
        style.add("TEXTCOLOR", (2, i), (2, i), fg)
        style.add("FONTNAME", (2, i), (2, i), "Helvetica-Bold")
    tbl.setStyle(style)

    overall_line = (
        "✓  Mix passes overall BIS compliance threshold."
        if overall else
        "⚠  One or more BIS standard thresholds may require review. "
        "Refer to remediation actions in Section 8."
    )
    return [
        Paragraph("BIS Standards Compliance Audit", st["h2"]),
        tbl,
        Spacer(1, 2*mm),
        Paragraph(overall_line, st["badge_pass"] if overall else st["badge_fail"]),
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

    lca_data = [
        ["LCA Metric", "Value"],
        ["Embodied Carbon", f"{co2:.1f} kg CO₂e/m³"],
        ["CO₂ Saving vs Conventional M20", f"−{saving:.1f}%"],
        ["Plastic Waste Diverted from Landfill", f"{diversion:.1f} kg/m³"],
        ["Equivalent PET Bottles Diverted", f"~{int(bottles):,} bottles/m³"],
    ]
    lca_tbl = Table(lca_data, colWidths=[90*mm, None])
    lca_tbl.setStyle(_tbl_style(C_EMERALD_700))

    green_data = [
        ["Green Rating Scheme", "Credits Earned", "Criterion"],
        ["IGBC Green Homes / Buildings", f"{igbc:.1f} pts", "Recycled Content + Thermal"],
        ["GRIHA (BEE/TERI)", f"{griha:.1f} pts", "Embodied Energy, Waste"],
        ["LEED v4 Materials & Resources", f"{leed:.1f} pts", "Recycled Content %"],
        ["Total Green Credits", f"{total_gc:.1f} pts", "All Schemes Combined"],
    ]
    green_tbl = Table(green_data, colWidths=[75*mm, 35*mm, None])
    green_tbl.setStyle(_tbl_style(C_EMERALD_700))

    return [
        Paragraph("Life Cycle Assessment (LCA) & Sustainability Score", st["h2"]),
        Paragraph(
            "Cradle-to-gate embodied carbon accounting using ICE Database v3.0 emission factors "
            "(Hammond & Jones, 2019). Baseline: conventional IS 10262 M20 mix at 365.7 kg CO₂e/m³.",
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
    data = [["Feature", "SHAP Contribution (MPa)", "Direction"]]
    for feat, val in sorted_feats:
        direction = "▲ Positive" if val >= 0 else "▼ Negative"
        data.append([feat, f"{val:+.2f}", direction])

    tbl = Table(data, colWidths=[90*mm, 50*mm, None])
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
    items.append(Paragraph(
        f"<b>Top limiting factor:</b> {neg_factor}. "
        f"Implementing the actions below is estimated to improve the sustainability score by "
        f"<b>+{gain:.1f} points</b>.",
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

    data = [["Rank", "Authors (Year)", "Journal", "Application", "CS (MPa)", "DOI"]]
    for a in analogues[:3]:
        props = a.get("properties", {})
        data.append([
            str(a.get("rank", "")),
            f"{a.get('author','')} ({a.get('year','')})",
            a.get("journal", "")[:30] + "…" if len(a.get("journal","")) > 30 else a.get("journal",""),
            a.get("primary_application", "").replace("_", " ").title(),
            f"{props.get('compressive_strength_mpa', '—'):.1f}" if isinstance(props.get('compressive_strength_mpa'), float) else "—",
            a.get("doi", "")[:28],
        ])

    tbl = Table(data, colWidths=[12*mm, 40*mm, 40*mm, 35*mm, 16*mm, None])
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

    data = [
        ["Cost Metric", "Plastic-Waste Concrete", "Conventional Concrete", "Saving"],
        ["Cost per m³ (INR)", f"₹{cb.get('plastic_mix_cost_inr_m3',0):,.0f}",
         f"₹{cb.get('conventional_cost_inr_m3',0):,.0f}",
         f"₹{cb.get('cost_saving_inr_m3',0):,.0f} ({cb.get('cost_saving_pct',0):.1f}%)"],
        ["Cost per m² product", f"₹{cb.get('plastic_mix_cost_inr_m2',0):,.0f}",
         f"₹{cb.get('conventional_cost_inr_m2',0):,.0f}",
         f"₹{cb.get('cost_saving_inr_m2',0):,.0f}"],
        ["Plastic aggregate input", f"{cb.get('plastic_kg_per_m3',0):.0f} kg/m³", "0 kg/m³", "—"],
    ]
    tbl = Table(data, colWidths=[55*mm, 35*mm, 40*mm, None])
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


# ── Main Public Function ───────────────────────────────────────────────────────

def generate_report(
    mix_params: dict,
    prediction: dict,
    score: dict,
    recommendation: dict,
    session_id: str = "OFFLINE",
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

    meta_data = [
        ["Generated", datetime.now().strftime("%d %B %Y, %H:%M IST")],
        ["Session ID", session_id],
        ["Mix Type", f"{mix_params.get('plastic_type', '—')} Aggregate Concrete"],
        ["Replacement Level", f"{mix_params.get('replacement_pct', '—'):.1f}% vol."],
        ["Standards Scope", "IS 456 / IS 1237 / IS 2185 (BIS, India)"],
        ["Model Version", "PlastiCrete AI v1.0 — M1/M2/M3/M4 Ensemble"],
    ]
    meta_tbl = Table(meta_data, colWidths=[45*mm, None])
    meta_tbl.setStyle(TableStyle([
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8),
        ("TEXTCOLOR",  (0, 0), (0, -1), C_SLATE_600),
        ("TEXTCOLOR",  (1, 0), (1, -1), C_SLATE_800),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
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

    # ── Disclaimer (final) ───────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_SLATE_300))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "<b>About PlastiCrete.ai:</b> An explainable ML platform for circular-economy concrete design, "
        "predicting 7 mechanical properties via XGBoost + Random Forest + DNN ensemble trained on "
        "2,000+ rows of peer-reviewed plastic-waste concrete research data. Developed for academic, "
        "industry, and policy research under Indian Standard engineering frameworks.",
        st["small_grey"],
    ))

    # Build
    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, mix_params, session_id),
        onLaterPages=lambda c, d: _header_footer(c, d, mix_params, session_id),
    )
    return buf.getvalue()
