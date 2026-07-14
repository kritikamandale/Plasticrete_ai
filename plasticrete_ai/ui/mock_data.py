"""
Realistic mock data — the graceful fallback whenever a real module can't load.

Every structure here mirrors the *normalised dict shape* that `ui.data_bridge`
returns for the real modules, so pages never branch on real-vs-mock.
"""
from __future__ import annotations

import copy

# ── The active formulation (design north-star sample) ─────────────────────────
ACTIVE_MIX = {
    "plastic_type":     "HDPE",
    "replacement_pct":  15.0,
    "particle_size_mm": 4.0,
    "wc_ratio":         0.45,
    "additive_type":    "silica_fume",
    "additive_pct":     8.0,
    "curing_temp_c":    35.0,
    "curing_days":      28,
}

# ── M1 — predicted properties (normalised predict() shape) ───────────────────
_PRED_VALUES = {
    "compressive_strength_mpa": 18.4,
    "flexural_strength_mpa":    3.8,
    "split_tensile_mpa":        2.1,
    "density_kgm3":             2080.0,
    "water_absorption_pct":     4.2,
    "thermal_conductivity_wm":  1.35,
    "durability_index":         71.0,
}
_PRED_CI_LOW = {
    "compressive_strength_mpa": 16.8, "flexural_strength_mpa": 3.4, "split_tensile_mpa": 1.8,
    "density_kgm3": 2010.0, "water_absorption_pct": 3.6, "thermal_conductivity_wm": 1.18,
    "durability_index": 64.0,
}
_PRED_CI_HIGH = {
    "compressive_strength_mpa": 20.0, "flexural_strength_mpa": 4.2, "split_tensile_mpa": 2.4,
    "density_kgm3": 2150.0, "water_absorption_pct": 4.8, "thermal_conductivity_wm": 1.52,
    "durability_index": 78.0,
}
# friendly-named SHAP contributions (MPa etc.) for the explainability waterfall
_SHAP_VALUES = {
    "compressive_strength_mpa": {
        "plastic_type=HDPE": -3.1, "replacement_pct=15%": -2.8, "wc_ratio=0.45": 1.9,
        "curing_days=28": 2.3, "additive_pct=8% silica fume": 2.4, "particle_size=4mm": -0.9,
        "curing_temp=35°C": 0.6,
    },
    "flexural_strength_mpa": {
        "additive_pct=8% silica fume": 0.7, "wc_ratio=0.45": 0.4, "replacement_pct=15%": -0.5,
        "curing_days=28": 0.3, "plastic_type=HDPE": -0.4, "particle_size=4mm": -0.2,
    },
    "durability_index": {
        "additive_pct=8% silica fume": 6.0, "wc_ratio=0.45": 3.5, "replacement_pct=15%": -5.5,
        "curing_days=28": 4.0, "water_absorption": -3.0, "plastic_type=HDPE": -2.0,
    },
}


def prediction() -> dict:
    return {
        "values":  copy.deepcopy(_PRED_VALUES),
        "ci_low":  copy.deepcopy(_PRED_CI_LOW),
        "ci_high": copy.deepcopy(_PRED_CI_HIGH),
        "shap_values": copy.deepcopy(_SHAP_VALUES),
        "uncertainty_flag": False,
        "low_coverage_targets": ["thermal_conductivity_wm"],
        "source": "mock",
    }


# ── M3 — sustainability & compliance (matches score_mix keys) ────────────────
def sustainability() -> dict:
    return {
        "sustainability_score":          74.0,
        "sustainability_grade":          "B",
        "embodied_carbon_kgco2e_m3":     281.6,
        "baseline_co2_kgco2e_m3":        365.71,
        "co2_saving_pct":                23.0,
        "co2_saved_kgco2e_m3":           84.1,
        "plastic_diversion_kg_m3":       198.0,
        "pet_bottle_equiv":              396.0,
        "recycled_content_pct":          18.5,
        "local_sourcing_pct":            82.0,
        "bis_overall_pass":              True,
        "igbc_total_credits":            2.0,
        "griha_material_criterion_pts":  1.0,
        "leed_total_points":             2.0,
        "total_green_credits":           5.0,
        "top_negative_factor":           "water_absorption_pct",
        "remediation_action_1":          "Reduce w/c ratio 0.45 → 0.42 to cut water absorption (+3 pts).",
        "remediation_action_2":          "Raise silica fume 8% → 12% to lift compressive strength (+4 pts).",
        "remediation_action_3":          "Lower plastic replacement 15% → 12% to meet IS 2185 density (+2 pts).",
        "estimated_score_gain":          9.0,
        # sub-scores feeding the aggregate gauge (0-100 each)
        "subscores": {
            "Embodied-carbon reduction": 82,
            "Plastic diversion":         88,
            "Recycled content":          62,
            "Local sourcing":            82,
            "BIS compliance":            60,
        },
        "source": "mock",
    }


# ── M3 — per-standard BIS checklist (mirrors BISResult booleans) ─────────────
def bis_checklist() -> list[dict]:
    return [
        {"key": "is_516",  "passed": True,  "status": "pass",
         "detail": "Grade M15 assigned · 18.4 ≥ 10 MPa", "threshold": "CS ≥ 10 MPa",
         "fix": ""},
        {"key": "is_1237", "passed": True,  "status": "pass",
         "detail": "Water absorption 4.2% within tile spec (relaxed)", "threshold": "WA ≤ 1% / CS ≥ 30 MPa",
         "fix": ""},
        {"key": "is_2185", "passed": False, "status": "warn",
         "detail": "Density 2080 kg/m³ just above lightweight-block cap", "threshold": "Density ≤ 1500 kg/m³ (Pt.2)",
         "fix": "Raise plastic replacement 15% → 22% to drop density below 1800 kg/m³."},
        {"key": "is_5816", "passed": True,  "status": "pass",
         "detail": "Split tensile 2.1 MPa ≥ 0.10 × CS", "threshold": "STS ≥ 0.10·CS & ≥ 1.5 MPa",
         "fix": ""},
        {"key": "nbc",     "passed": True,  "status": "pass",
         "detail": "Non-structural use certified (density < 1800 not required)", "threshold": "CS ≥ 20 MPa for structural",
         "fix": ""},
    ]


# ── M4 — application recommendation (matches recommend() dict shape) ─────────
_SUITABILITY = {
    "paving_block_light":          91.0,
    "plastic_sand_paver":          88.0,
    "floor_tile_outdoor":          84.0,
    "lightweight_partition_block": 79.0,
    "hollow_concrete_block":       74.0,
    "kerb_stone":                  71.0,
    "paving_block_heavy":          66.0,
    "nonstructural_concrete_fill": 63.0,
    "floor_tile_indoor":           58.0,
    "wall_cladding_panel":         52.0,
    "thermal_insulation_panel":    44.0,
    "structural_concrete":         28.0,
}

_RAG = [
    {"rank": 1, "id": "iftikhar_2023", "author": "Iftikhar et al.", "year": 2023,
     "journal": "Heliyon", "doi": "10.1016/j.heliyon.2023.e17107",
     "primary_application": "plastic_sand_paver", "secondary_application": "paving_block_light",
     "l2_distance": 0.31,
     "properties": {"compressive_strength_mpa": 19.6, "density_kgm3": 2035.0,
                    "water_absorption_pct": 3.9, "flexural_strength_mpa": 3.9}},
    {"rank": 2, "id": "nafees_2022", "author": "Nafees et al.", "year": 2022,
     "journal": "Polymers", "doi": "10.3390/polym14081583",
     "primary_application": "paving_block_light", "secondary_application": "floor_tile_outdoor",
     "l2_distance": 0.44,
     "properties": {"compressive_strength_mpa": 17.8, "density_kgm3": 2110.0,
                    "water_absorption_pct": 4.5, "flexural_strength_mpa": 3.6}},
    {"rank": 3, "id": "nayir_2024", "author": "Nayır & Yılmaz", "year": 2024,
     "journal": "Construction & Building Materials", "doi": "10.1016/j.conbuildmat.2024.135210",
     "primary_application": "hollow_concrete_block", "secondary_application": "lightweight_partition_block",
     "l2_distance": 0.52,
     "properties": {"compressive_strength_mpa": 16.9, "density_kgm3": 1980.0,
                    "water_absorption_pct": 4.1, "flexural_strength_mpa": 3.5}},
    {"rank": 4, "id": "chong_shi_2023", "author": "Chong & Shi", "year": 2023,
     "journal": "Journal of Cleaner Production", "doi": "10.1016/j.jclepro.2023.137845",
     "primary_application": "floor_tile_outdoor", "secondary_application": "kerb_stone",
     "l2_distance": 0.59,
     "properties": {"compressive_strength_mpa": 20.4, "density_kgm3": 2150.0,
                    "water_absorption_pct": 3.7, "flexural_strength_mpa": 4.1}},
    {"rank": 5, "id": "alkharisi_2025", "author": "Alkharisi & Dahish", "year": 2025,
     "journal": "Case Studies in Construction Materials", "doi": "10.1016/j.cscm.2025.e04120",
     "primary_application": "lightweight_partition_block", "secondary_application": "thermal_insulation_panel",
     "l2_distance": 0.63,
     "properties": {"compressive_strength_mpa": 15.2, "density_kgm3": 1720.0,
                    "water_absorption_pct": 5.0, "flexural_strength_mpa": 3.2}},
]


def recommendation() -> dict:
    scores = dict(sorted(_SUITABILITY.items(), key=lambda x: -x[1]))
    top = next(iter(scores))
    return {
        "primary_application":    top,
        "primary_confidence_pct": scores[top],
        "suitable_applications":  [a for a, s in scores.items() if s >= 70],
        "suitability_scores":     scores,
        "cost_benefit": {
            "plastic_mix_cost_inr_m3":  4120.0,
            "conventional_cost_inr_m3": 5180.0,
            "cost_saving_inr_m3":       1060.0,
            "cost_saving_pct":          20.5,
            "plastic_mix_cost_inr_m2":  588.6,
            "conventional_cost_inr_m2": 740.0,
            "cost_saving_inr_m2":       151.4,
            "product_yield_m2_per_m3":  7.0,
            "plastic_kg_per_m3":        198.0,
            "additive_kg_per_m3":       30.6,
        },
        "rag_analogues": copy.deepcopy(_RAG),
        "source": "mock",
    }


# ── M2 — optimiser scenarios / pareto / sensitivity ──────────────────────────
SCENARIOS = {
    "strength_optimised": {
        "label": "Strength-Optimised", "icon": "💪",
        "headline": "56.5 MPa", "headline_label": "Compressive Strength",
        "best_mix": {"plastic_type": "LDPE", "replacement_pct": 6.2, "particle_size_mm": 0.5,
                     "wc_ratio": 0.36, "additive_type": "silica_fume", "additive_pct": 30.0,
                     "curing_temp_c": 20.0, "curing_days": 90},
        "predicted": {"compressive_strength_mpa": 56.5, "cost_inr_per_m3": 6686.0,
                      "co2_kgco2e_per_m3": 303.9, "plastic_diversion_kg_per_m3": 8.4},
    },
    "cost_optimised": {
        "label": "Cost-Optimised", "icon": "💰",
        "headline": "₹4,758", "headline_label": "Cost / m³",
        "best_mix": {"plastic_type": "LDPE", "replacement_pct": 19.1, "particle_size_mm": 2.0,
                     "wc_ratio": 0.35, "additive_type": "none", "additive_pct": 0.0,
                     "curing_temp_c": 72.4, "curing_days": 86},
        "predicted": {"compressive_strength_mpa": 34.5, "cost_inr_per_m3": 4758.0,
                      "co2_kgco2e_per_m3": 248.8, "plastic_diversion_kg_per_m3": 22.5},
    },
    "sustainability_optimised": {
        "label": "Sustainability-Optimised", "icon": "♻️",
        "headline": "61.5 kg/m³", "headline_label": "Plastic Diverted",
        "best_mix": {"plastic_type": "Mixed", "replacement_pct": 40.0, "particle_size_mm": 3.6,
                     "wc_ratio": 0.35, "additive_type": "silica_fume", "additive_pct": 0.0,
                     "curing_temp_c": 80.0, "curing_days": 90},
        "predicted": {"compressive_strength_mpa": 17.4, "cost_inr_per_m3": 5487.0,
                      "co2_kgco2e_per_m3": 169.2, "plastic_diversion_kg_per_m3": 61.5},
    },
}


def optimize(scenario: str = "strength_optimised") -> dict:
    s = SCENARIOS.get(scenario, SCENARIOS["strength_optimised"])
    p = s["predicted"]
    return {
        "best_mix":                          s["best_mix"],
        "predicted_cs_mpa":                  p["compressive_strength_mpa"],
        "predicted_cost_inr_m3":             p["cost_inr_per_m3"],
        "predicted_co2_kgco2e_m3":           p["co2_kgco2e_per_m3"],
        "predicted_plastic_diversion_kg_m3": p["plastic_diversion_kg_per_m3"],
        "composite_score":                   0.71,
        "mode":                              "scenario",
        "source":                            "mock",
    }


# Pareto front (Strength vs Cost, coloured by CO₂, sized by diversion)
def pareto_front() -> list[dict]:
    import random
    rng = random.Random(42)
    pts = []
    for i in range(60):
        cs = rng.uniform(14, 57)
        cost = 4600 + (cs - 14) * 55 + rng.uniform(-250, 250)
        co2 = 320 - (cs - 14) * 2.4 + rng.uniform(-15, 15)
        div = max(4, 70 - cs * 0.9 + rng.uniform(-6, 6))
        pts.append({"cs": round(cs, 1), "cost": round(cost), "co2": round(co2, 1),
                    "diversion": round(div, 1)})
    return pts


def sensitivity() -> dict:
    """Tornado data — ±10% CS delta per input (MPa)."""
    return {
        "wc_ratio":         {"plus": -3.04, "minus": 0.0},
        "replacement_pct":  {"plus": -0.86, "minus": 0.30},
        "curing_temp_c":    {"plus": 0.70,  "minus": 0.0},
        "additive_pct":     {"plus": 0.0,   "minus": 0.68},
        "curing_days":      {"plus": 0.0,   "minus": -0.30},
        "particle_size_mm": {"plus": 0.0,   "minus": 0.0},
    }


# ── Clustering / PCA (Material Insights) ─────────────────────────────────────
CLUSTERS = [
    {"id": 1, "name": "High-Strength Modified", "color": "#2B3A55", "centroid": (-1.9, 1.3),
     "desc": "Low plastic 5–10% · low w/c · silica fume · HDPE/PET → structural blocks",
     "params": {"plastic_type": "HDPE", "replacement_pct": 8.0, "particle_size_mm": 2.0,
                "wc_ratio": 0.38, "additive_type": "silica_fume", "additive_pct": 12.0,
                "curing_temp_c": 30.0, "curing_days": 56}},
    {"id": 2, "name": "Lightweight Thermal", "color": "#EC4899", "centroid": (1.6, 1.1),
     "desc": "High plastic 25–35% · LDPE/PP → insulating partitions",
     "params": {"plastic_type": "LDPE", "replacement_pct": 30.0, "particle_size_mm": 6.0,
                "wc_ratio": 0.50, "additive_type": "none", "additive_pct": 0.0,
                "curing_temp_c": 25.0, "curing_days": 28}},
    {"id": 3, "name": "Durable Paving", "color": "#F59E0B", "centroid": (-0.3, -1.4),
     "desc": "Moderate plastic 10–20% · fly ash · long curing → paving / footpath",
     "params": {"plastic_type": "PET", "replacement_pct": 15.0, "particle_size_mm": 4.0,
                "wc_ratio": 0.44, "additive_type": "fly_ash", "additive_pct": 20.0,
                "curing_temp_c": 35.0, "curing_days": 90}},
    {"id": 4, "name": "Economy Mix", "color": "#64748B", "centroid": (2.1, -1.0),
     "desc": "High plastic 30–40% · no additive → fillers, planters, furniture",
     "params": {"plastic_type": "Mixed", "replacement_pct": 35.0, "particle_size_mm": 8.0,
                "wc_ratio": 0.55, "additive_type": "none", "additive_pct": 0.0,
                "curing_temp_c": 25.0, "curing_days": 14}},
    {"id": 5, "name": "High-Performance Composite", "color": "#16A34A", "centroid": (-2.3, -0.2),
     "desc": "Fibre · very low w/c · multi-additive → precast / thin-shell",
     "params": {"plastic_type": "PP", "replacement_pct": 12.0, "particle_size_mm": 1.5,
                "wc_ratio": 0.35, "additive_type": "fibres", "additive_pct": 2.0,
                "curing_temp_c": 40.0, "curing_days": 56}},
]


def cluster_scatter_points() -> list[dict]:
    import random
    rng = random.Random(7)
    pts = []
    for c in CLUSTERS:
        cx, cy = c["centroid"]
        for _ in range(38):
            pts.append({"x": cx + rng.gauss(0, 0.5), "y": cy + rng.gauss(0, 0.45),
                        "cluster": c["name"], "color": c["color"]})
    return pts


def dbscan_outliers() -> list[dict]:
    return [
        {"mix_id": "M-0417", "plastic_type": "PVC", "replacement_pct": 38.0, "wc_ratio": 0.63,
         "compressive_strength_mpa": 6.1, "note": "Extreme PVC + high w/c — brittle low-strength"},
        {"mix_id": "M-1122", "plastic_type": "PET", "replacement_pct": 2.0, "wc_ratio": 0.35,
         "compressive_strength_mpa": 61.8, "note": "Near-plain high-performance outlier"},
        {"mix_id": "M-0839", "plastic_type": "Mixed", "replacement_pct": 40.0, "wc_ratio": 0.60,
         "compressive_strength_mpa": 8.4, "note": "Max plastic, no additive — density anomaly"},
    ]


# ── Dashboard — recent predictions table ─────────────────────────────────────
def recent_predictions() -> list[dict]:
    return [
        {"plastic_type": "HDPE",  "replacement_pct": 15, "wc_ratio": 0.45, "cs": 18.4,
         "score": 74, "top_app": "Paving Blocks · Light",   "when": "just now"},
        {"plastic_type": "PET",   "replacement_pct": 10, "wc_ratio": 0.42, "cs": 24.1,
         "score": 79, "top_app": "Floor Tiles · Outdoor",   "when": "12 min ago"},
        {"plastic_type": "LDPE",  "replacement_pct": 30, "wc_ratio": 0.50, "cs": 12.6,
         "score": 81, "top_app": "Partition Wall Panels",   "when": "1 hr ago"},
        {"plastic_type": "PP",    "replacement_pct": 12, "wc_ratio": 0.38, "cs": 31.7,
         "score": 76, "top_app": "Structural Concrete",     "when": "3 hr ago"},
        {"plastic_type": "Mixed", "replacement_pct": 35, "wc_ratio": 0.55, "cs":  9.8,
         "score": 83, "top_app": "Non-Structural Fill",     "when": "yesterday"},
        {"plastic_type": "PVC",   "replacement_pct": 18, "wc_ratio": 0.48, "cs": 15.2,
         "score": 68, "top_app": "Kerb Stones",             "when": "yesterday"},
    ]


# PDP / ICE illustrative curves (Explainability Lab)
def pdp_curves() -> dict:
    return {
        "replacement_pct": {
            "x": [0, 5, 10, 15, 20, 25, 30, 35, 40],
            "y": [34.0, 30.5, 26.8, 22.9, 19.4, 16.2, 13.6, 11.4, 9.8],
        },
        "wc_ratio": {
            "x": [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65],
            "y": [28.5, 24.9, 21.4, 18.1, 15.2, 12.8, 10.9],
        },
        "curing_days": {
            "x": [3, 7, 14, 28, 56, 90],
            "y": [9.1, 13.4, 17.2, 21.4, 24.0, 25.6],
        },
    }


def ice_curves() -> dict:
    """Per-plastic-type CS vs replacement% — PET gradual, PVC sharp drop >15%."""
    x = [0, 5, 10, 15, 20, 25, 30, 35, 40]
    return {
        "PET":  [34, 31, 28, 25.5, 23, 20.5, 18, 16, 14],
        "HDPE": [34, 30, 26.5, 23, 19.5, 16.5, 14, 12, 10.5],
        "LDPE": [34, 29, 24.5, 20, 16, 13, 11, 9.5, 8.5],
        "PVC":  [34, 30, 25, 19, 12.5, 8.5, 6.5, 5.5, 5.0],
        "PP":   [34, 30.5, 27, 24, 21, 18.5, 16.5, 15, 13.5],
        "Mixed":[34, 29.5, 25.5, 21.5, 17.5, 14.5, 12.5, 11, 10],
        "x": x,
    }
