"""
PlastiCrete AI - Module 3 Public Contract
==========================================
Public surface:
    load_models(model_dir, config) -> None   (called at startup by FastAPI lifespan)
    score_mix(mix_params, m1_props)  -> dict  (matches ScoreResponse field names)
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml
from loguru import logger

from modules.m3_sustainability.core.bis_checker import BISChecker
from modules.m3_sustainability.core.lca_calculator import LCACalculator
from modules.m3_sustainability.core.green_rater import GreenRater
from modules.m3_sustainability.core.score_aggregator import ScoreAggregator
from modules.m3_sustainability.core.remediation_advisor import RemediationAdvisor

# ── Module-level config/singletons ────────────────────────────────────────────
_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "m3_config.yaml"

_config:  dict = {}
_bis:     BISChecker | None = None
_lca:     LCACalculator | None = None
_green:   GreenRater | None = None
_agg:     ScoreAggregator | None = None
_advisor: RemediationAdvisor | None = None
_loaded = False


def load_models(model_dir: str = "", config: dict | None = None) -> None:
    """Initialise all M3 scoring components from config."""
    global _config, _bis, _lca, _green, _agg, _advisor, _loaded

    if _loaded:
        return

    if config:
        _config = config
    elif _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            _config = yaml.safe_load(f)
    else:
        logger.warning(f"M3 config not found at {_CONFIG_PATH} — using defaults")
        _config = _default_config()

    ef        = _load_emission_factors(_config)
    densities = _load_plastic_densities(_config)

    _bis     = BISChecker()
    _lca     = LCACalculator(config=_config, ef=ef, densities=densities)
    _green   = GreenRater(config=_config)
    _agg     = ScoreAggregator(config=_config)
    _advisor = RemediationAdvisor()
    _loaded  = True
    logger.info("M3 sustainability scoring engine loaded")


def score_mix(mix_params: dict, m1_props: dict) -> dict:
    """
    Compute full sustainability report for a mix.

    Args:
        mix_params: 8 mix design parameters (plastic_type, replacement_pct, ...)
        m1_props:   7 predicted mechanical properties from M1

    Returns:
        dict matching all fields of ScoreResponse schema.
    """
    _ensure_loaded()

    lca_result  = _lca.compute(mix_params, m1_props)
    bis_result  = _bis.check(m1_props)
    green_result = _green.rate(mix_params, m1_props, lca_result)
    score_result = _agg.score(mix_params, lca_result, bis_result, green_result)
    rem_result   = _advisor.advise(mix_params, m1_props, lca_result, bis_result, score_result)

    return {
        "sustainability_score":          score_result.sustainability_score,
        "sustainability_grade":          score_result.sustainability_grade,
        "embodied_carbon_kgco2e_m3":     lca_result.embodied_carbon_kgco2e_m3,
        "co2_saving_pct":                lca_result.co2_saving_pct,
        "plastic_diversion_kg_m3":       lca_result.plastic_diversion_kg_m3,
        "pet_bottle_equiv":              float(lca_result.pet_bottle_equiv),
        "bis_overall_pass":              bis_result.bis_overall_pass,
        "igbc_total_credits":            float(green_result.igbc_total),
        "griha_material_criterion_pts":  float(green_result.griha_total),
        "leed_total_points":             float(green_result.leed_total),
        "total_green_credits":           float(green_result.total_green_credits),
        "top_negative_factor":           rem_result.top_negative_factor,
        "remediation_action_1":          rem_result.remediation_action_1,
        "remediation_action_2":          rem_result.remediation_action_2,
        "remediation_action_3":          rem_result.remediation_action_3,
        "estimated_score_gain":          rem_result.estimated_score_gain,
    }


# ── Internal helpers ───────────────────────────────────────────────────────────

def _ensure_loaded() -> None:
    if not _loaded:
        load_models()


def _load_emission_factors(config: dict) -> dict:
    """Load ICE emission factors from CSV; fall back to hardcoded defaults."""
    try:
        import pandas as pd
        ef_path_str = config.get("external_data", {}).get("ice_ef_path", "")
        ef_path = _resolve_path(ef_path_str)
        if ef_path.exists():
            df = pd.read_csv(ef_path)
            return dict(zip(df["material_key"], df["kg_co2e_per_kg"]))
        logger.warning(f"ICE emission factors CSV not found at {ef_path} — using defaults")
    except Exception as exc:
        logger.warning(f"Failed to load emission factors: {exc} — using defaults")
    return _default_emission_factors()


def _load_plastic_densities(config: dict) -> dict:
    """Load plastic densities from JSON; fall back to hardcoded defaults."""
    try:
        path_str = config.get("external_data", {}).get("plastic_density_path", "")
        path = _resolve_path(path_str)
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            return {k: v["density_kgm3"] for k, v in data.get("densities", {}).items()}
        logger.warning(f"Plastic density JSON not found at {path} — using defaults")
    except Exception as exc:
        logger.warning(f"Failed to load plastic densities: {exc} — using defaults")
    return {"PET": 1380, "HDPE": 960, "LDPE": 920, "PVC": 1400, "PP": 905, "Mixed": 1100}


def _resolve_path(rel_path: str) -> Path:
    """Resolve a config-relative path anchored to the project root."""
    project_root = Path(__file__).parent.parent.parent
    return project_root / rel_path


def _default_emission_factors() -> dict:
    return {
        "cement_opc":       0.872,
        "water_municipal":  0.0003,
        "sand_river":       0.0048,
        "coarse_aggregate": 0.0048,
        "PET":  -1.10,
        "HDPE": -0.85,
        "LDPE": -0.80,
        "PVC":  -0.95,
        "PP":   -0.75,
        "Mixed": -0.90,
        "fly_ash":      0.004,
        "silica_fume":  0.014,
        "ggbs":         0.083,
        "fibres_plastic": 0.0,
    }


def _default_config() -> dict:
    return {
        "score_weights": {
            "carbon_component":       30,
            "plastic_diversion_comp": 25,
            "recycled_content_comp":  20,
            "bis_compliance_comp":    15,
            "green_rating_comp":      10,
        },
        "green_rating": {
            "igbc_plastic_diversion_min_kg_m3": 50,
            "igbc_tc_threshold_wm":             0.60,
            "griha_co2_saving_min_pct":         10.0,
            "griha_diversion_min_kg_m3":       100.0,
            "leed_replacement_pct_min":         10.0,
            "leed_diversion_min_kg_m3":         75.0,
        },
        "external_data": {
            "ice_ef_path":          "data/external/ice_emission_factors_extended.csv",
            "plastic_density_path": "data/external/plastic_density_lookup.json",
        },
    }
