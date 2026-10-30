"""
PlastiCrete AI — Module 1 Public Contract
==========================================
M2, M3, M4 import ONLY from this file. Never import from internals.

Public surface:
    load_ensemble(model_dir, config) → None
    predict(input_dict)              → PredictionResult
    predict_batch(X)                 → (means, ci_low, ci_high)
    get_preprocessor()               → Preprocessor

CONTRACT VERSION: 1.0
Breaking change policy: any field rename/removal in PredictionResult → bump to v2.0
"""
from __future__ import annotations

from typing import Tuple

import numpy as np

from modules.m1_prediction.utils.schema import PredictionResult  # re-exported for M2/M3/M4

_ensemble = None  # singleton — loaded once at startup


def _check_loaded() -> None:
    if _ensemble is None:
        raise RuntimeError(
            "M1 ensemble not loaded. Call m1_prediction.load_ensemble(model_dir, config) first."
        )


def load_ensemble(model_dir: str, config: dict) -> None:
    """
    Call once at startup (FastAPI lifespan, Streamlit init, M2 init).
    Loads all sub-models and preprocessor from model_dir.
    """
    global _ensemble
    from modules.m1_prediction.model.ensemble import PlastiCreteEnsemble
    from modules.m1_prediction.explainability.shap_explainer import SHAPExplainer
    _ensemble = PlastiCreteEnsemble.from_saved(model_dir, config)
    explainer = SHAPExplainer(config, _ensemble, _ensemble.preprocessor)
    try:
        # Generate representative reference background across typical concrete mix ranges
        sample_presets = [
            {"plastic_type": pt, "replacement_pct": r, "particle_size_mm": ps, "wc_ratio": wc,
             "additive_type": ad, "additive_pct": ap, "curing_temp_c": ct, "curing_days": cd}
            for pt in ["PET", "HDPE", "Mixed", "LDPE"]
            for r in [0.0, 10.0, 20.0]
            for ps in [2.0, 5.0]
            for wc in [0.40, 0.50]
            for ad in ["none", "fly_ash"]
            for ap in [0.0, 10.0]
            for ct in [27.0]
            for cd in [28]
        ]
        X_bg = np.vstack([_ensemble.preprocessor.transform_input(p) for p in sample_presets[:50]])
        explainer.fit(X_bg)
    except Exception as exc:
        from loguru import logger
        logger.warning(f"Could not pre-fit SHAP explainer: {exc}")
    _ensemble.set_shap_explainer(explainer)


def predict(input_dict: dict) -> PredictionResult:
    """
    Single mix prediction with SHAP explanations.
    Called by M3 (sustainability scorer), M4 (recommender), and /predict endpoint.

    Args:
        input_dict: keys matching INPUT_FEATURES from schema.py

    Returns:
        PredictionResult dataclass with all 7 targets, CIs, and SHAP values.
    """
    _check_loaded()
    return _ensemble.predict(input_dict)


def predict_batch(X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Vectorised prediction without SHAP. Called by M2 optimisation loop.

    Args:
        X: ndarray shape (n_samples, n_features) — preprocessed via get_preprocessor()

    Returns:
        (means, ci_low, ci_high) — each shape (n_samples, 7), original units.
        Column order follows TARGET_COLUMNS from schema.py.
    """
    _check_loaded()
    return _ensemble.predict_batch(X)


def get_preprocessor():
    """
    M2 uses this to transform candidate mixes before calling predict_batch().
    Returns the fitted Preprocessor instance.
    """
    _check_loaded()
    return _ensemble.preprocessor
