"""
Output dataclasses for M4 public contract.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class RAGAnalogue:
    rank:                  int
    id:                    str
    author:                str
    year:                  int
    journal:               str
    doi:                   str
    primary_application:   str
    secondary_application: str
    l2_distance:           float
    properties:            Dict[str, float]


@dataclass
class CostBenefit:
    plastic_mix_cost_inr_m3:   float
    conventional_cost_inr_m3:  float
    cost_saving_inr_m3:        float
    cost_saving_pct:           float
    plastic_mix_cost_inr_m2:   float
    conventional_cost_inr_m2:  float
    cost_saving_inr_m2:        float
    product_yield_m2_per_m3:   float
    plastic_kg_per_m3:         float
    additive_kg_per_m3:        float


@dataclass
class RecommendationResult:
    primary_application:     str
    primary_confidence_pct:  float
    suitable_applications:   List[str]
    suitability_scores:      Dict[str, float]
    cost_benefit:            CostBenefit
    rag_analogues:           List[RAGAnalogue]
