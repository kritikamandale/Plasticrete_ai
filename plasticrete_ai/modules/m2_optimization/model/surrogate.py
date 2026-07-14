"""
Surrogate model singletons for M2.
All module-level names are None until load() is called.
"""
from __future__ import annotations

from pathlib import Path

import joblib
from loguru import logger

_MODEL_DIR = Path(__file__).parent.parent.parent.parent / "models" / "m2"

# ── Encoders ───────────────────────────────────────────────────────────────────
le_plastic:  object = None
le_additive: object = None

# ── Scalers ────────────────────────────────────────────────────────────────────
scaler_X:    object = None
scaler_cs:   object = None
scaler_cost: object = None
scaler_co2:  object = None
scaler_div:  object = None

# ── XGBoost surrogate models ───────────────────────────────────────────────────
xgb_cs:   object = None
xgb_cost: object = None
xgb_co2:  object = None
xgb_div:  object = None

_loaded = False


def load(model_dir: Path | None = None) -> None:
    """Load all surrogate models and encoders from disk (idempotent)."""
    global le_plastic, le_additive, scaler_X, scaler_cs, scaler_cost
    global scaler_co2, scaler_div, xgb_cs, xgb_cost, xgb_co2, xgb_div, _loaded

    if _loaded:
        return

    d = Path(model_dir) if model_dir else _MODEL_DIR
    le_plastic   = joblib.load(d / "le_plastic.pkl")
    le_additive  = joblib.load(d / "le_additive.pkl")
    scaler_X     = joblib.load(d / "scaler_X.pkl")
    scaler_cs    = joblib.load(d / "scaler_cs.pkl")
    scaler_cost  = joblib.load(d / "scaler_cost.pkl")
    scaler_co2   = joblib.load(d / "scaler_co2.pkl")
    scaler_div   = joblib.load(d / "scaler_plastic_diversion.pkl")
    xgb_cs       = joblib.load(d / "xgb_cs_surrogate.pkl")
    xgb_cost     = joblib.load(d / "xgb_cost_surrogate.pkl")
    xgb_co2      = joblib.load(d / "xgb_co2_surrogate.pkl")
    xgb_div      = joblib.load(d / "xgb_plastic_diversion_surrogate.pkl")
    _loaded = True
    logger.info("M2 surrogate models loaded from {}", d)


def is_loaded() -> bool:
    return _loaded
