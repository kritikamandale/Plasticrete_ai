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
