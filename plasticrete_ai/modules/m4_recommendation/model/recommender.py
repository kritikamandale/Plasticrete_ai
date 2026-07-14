"""
Recommendation orchestration logic for M4.
"""
from __future__ import annotations

from modules.m4_recommendation.model import classifiers
from modules.m4_recommendation.utils.features import build_feature_vector
from modules.m4_recommendation.utils.cost_benefit import calculate as calc_cost_benefit
from modules.m4_recommendation.utils.rag import retrieve as rag_retrieve
from modules.m4_recommendation.utils.schema import RecommendationResult


def recommend(mix_params: dict, m1_properties: dict) -> RecommendationResult:
    """
    Orchestrate primary classification, multi-label suitability scoring,
    cost-benefit calculation, and RAG retrieval.

    Args:
        mix_params:     dict with plastic_type, replacement_pct, particle_size_mm,
                        wc_ratio, additive_type, additive_pct, curing_temp_c, curing_days
        m1_properties:  dict with compressive_strength_mpa, flexural_strength_mpa,
                        split_tensile_mpa, density_kgm3, water_absorption_pct,
                        thermal_conductivity_wm, durability_index

    Returns:
        RecommendationResult
    """
    apps = classifiers.config.get("application_categories", [])
    X    = classifiers.scaler.transform(build_feature_vector(mix_params, m1_properties))

    # Primary application
    pred_class  = classifiers.rf_primary.predict(X)[0]
    pred_proba  = classifiers.rf_primary.predict_proba(X)[0]
    primary_app = classifiers.label_enc.inverse_transform([pred_class])[0]
    confidence  = round(float(pred_proba.max()) * 100, 1)

    # Multi-label suitability
    ml_preds = classifiers.rf_multilabel.predict(X)[0]
    suitable = [a for a, s in zip(apps, ml_preds) if s == 1]

    # Continuous suitability scores
    score_preds = classifiers.rf_score_reg.predict(X)[0]
    scores = dict(sorted(
        {a: round(float(s), 1) for a, s in zip(apps, score_preds)}.items(),
        key=lambda x: x[1],
        reverse=True,
    ))

    return RecommendationResult(
        primary_application    = primary_app,
        primary_confidence_pct = confidence,
        suitable_applications  = suitable,
        suitability_scores     = scores,
        cost_benefit           = calc_cost_benefit(mix_params, primary_app),
        rag_analogues          = rag_retrieve(m1_properties),
    )
