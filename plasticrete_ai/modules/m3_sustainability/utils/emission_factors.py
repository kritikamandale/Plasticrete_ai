"""Load ICE emission factors from CSV and expose as a lookup dict."""
from pathlib import Path

import pandas as pd
from loguru import logger

_EF_CACHE = None
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def get_emission_factors(config: dict) -> dict:
    """
    Returns dict: {material_key: kg_co2e_per_kg}
    Loaded once and cached for the process lifetime.
    """
    global _EF_CACHE
    if _EF_CACHE is not None:
        return _EF_CACHE

    rel_path = config.get("external_data", {}).get(
        "ice_ef_path", "data/external/ice_emission_factors_extended.csv"
    )
    path = _PROJECT_ROOT / rel_path
    try:
        df = pd.read_csv(path)
        _EF_CACHE = dict(zip(df["material_key"], df["kg_co2e_per_kg"]))
    except FileNotFoundError:
        logger.warning(f"ICE emission factors not found at {path} — using hardcoded defaults")
        _EF_CACHE = _defaults()
    except Exception as exc:
        logger.warning(f"Failed to load emission factors ({exc}) — using hardcoded defaults")
        _EF_CACHE = _defaults()

    return _EF_CACHE


def _defaults() -> dict:
    return {
        "cement_opc":       0.872,
        "water_municipal":  0.0003,
        "sand_river":       0.0048,
        "coarse_aggregate": 0.0048,
        "PET":  -1.10, "HDPE": -0.85, "LDPE": -0.80,
        "PVC":  -0.95, "PP":   -0.75, "Mixed": -0.90,
        "fly_ash": 0.004, "silica_fume": 0.014,
        "ggbs": 0.083, "fibres_plastic": 0.0,
    }
