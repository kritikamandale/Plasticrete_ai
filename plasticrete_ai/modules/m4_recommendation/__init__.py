"""
M4 — Construction Application Recommendation Engine
=====================================================
Classifies optimal construction applications for a given plastic-concrete mix,
retrieves literature analogues via FAISS RAG, and computes cost-benefit economics.

Public surface:
    load_models()                          -> None
    recommend(mix_params, m1_properties)   -> RecommendationResult

Internal layout:
    model/classifiers.py  — model singletons and disk-loading
    model/recommender.py  — recommendation orchestration logic
    utils/schema.py       — output dataclasses (RAGAnalogue, CostBenefit, RecommendationResult)
    utils/features.py     — feature vector builder
    utils/cost_benefit.py — economics calculator
    utils/rag.py          — FAISS knowledge base retrieval
    tests/                — contract and unit tests
"""
from __future__ import annotations

from modules.m4_recommendation.model import classifiers
from modules.m4_recommendation.model.recommender import recommend as _recommend
from modules.m4_recommendation.utils.schema import RecommendationResult  # re-exported


def load_models(model_dir: str | None = None) -> None:
    """Load all M4 models, encoders, and knowledge base from disk (idempotent)."""
    classifiers.load(model_dir)


def recommend(mix_params: dict, m1_properties: dict) -> RecommendationResult:
    """
    Main M4 entry point.

    Parameters
    ----------
    mix_params : dict
        Keys: plastic_type, replacement_pct, particle_size_mm, wc_ratio,
              additive_type, additive_pct, curing_temp_c, curing_days
    m1_properties : dict
        Keys: compressive_strength_mpa, flexural_strength_mpa, split_tensile_mpa,
              density_kgm3, water_absorption_pct, thermal_conductivity_wm, durability_index

    Returns
    -------
    RecommendationResult
    """
    if not classifiers.is_loaded():
        classifiers.load()
    return _recommend(mix_params, m1_properties)
