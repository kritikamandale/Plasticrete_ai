"""
M2 - Intelligent Mix Optimisation Engine
=========================================
Uses pre-trained XGBoost surrogate models to find optimal mix designs
via Optuna-based constrained Bayesian optimisation.

Public surface:
    run_optimization(constraints, weights, mode) -> dict
    load_models()                                -> None

Internal layout:
    model/surrogate.py  — model singletons and disk-loading
    model/optimizer.py  — Optuna study and objective function
    utils/schema.py     — shared constants (PLASTIC_TYPES, norms)
    utils/encoding.py   — feature encoding and surrogate prediction
    tests/              — contract and unit tests
"""
from __future__ import annotations

from modules.m2_optimization.model import surrogate
from modules.m2_optimization.model import optimizer


def load_models() -> None:
    """Load all M2 surrogate models and encoders from disk (idempotent)."""
    surrogate.load()


def run_optimization(constraints: dict, weights: dict, mode: str = "constrained") -> dict:
    """
    Find the optimal mix design using surrogate models and Optuna.

    Args:
        constraints: {plastic_type, replacement_pct_max, compressive_strength_min,
                      density_max_kgm3, cost_max_inr_per_m3}
        weights:     {compressive_strength, cost_per_m3, co2_per_m3, plastic_content_pct}
        mode:        "constrained" or "scenario"

    Returns:
        dict matching all OptimizeResponse fields.
    """
    if not surrogate.is_loaded():
        surrogate.load()
    return optimizer.run(constraints, weights, mode)
