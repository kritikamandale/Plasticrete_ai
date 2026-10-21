"""
M2 - Intelligent Mix Optimisation Engine
=========================================
Optuna searches candidate mixes. Compressive strength comes from M1
predict_batch. Cost, CO2, and plastic mass come from the shared mass balance.

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
    Find a mix with Optuna. Strength is M1. Cost, CO2, and plastic mass are
    the shared mass balance.

    Args:
        constraints: plastic_type, replacement_pct_max, compressive_strength_min,
                     density_max_kgm3, cost_max_inr_per_m3,
                     plastic_diversion_min_kg_m3, use_class
        weights:     compressive_strength, cost_per_m3, co2_per_m3, plastic_content_pct
        mode:        "constrained" or "scenario"
    """
    return optimizer.run(constraints, weights, mode)
