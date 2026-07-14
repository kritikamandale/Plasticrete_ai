"""
Pydantic request/response models for the M1 FastAPI endpoint.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from modules.m1_prediction.utils.schema import (
    ADDITIVE_TYPE_CLASSES, PLASTIC_TYPE_CLASSES,
    INPUT_RANGES, TARGET_COLUMNS,
)


class MixInput(BaseModel):
    plastic_type:    str   = Field(..., description="Plastic aggregate type")
    replacement_pct: float = Field(..., ge=0.0, le=40.0,
                                   description="Plastic replacement % by volume")
    particle_size_mm: float = Field(..., ge=0.5, le=20.0,
                                    description="Plastic particle size in mm")
    wc_ratio:        float = Field(..., ge=0.35, le=0.65,
                                   description="Water-to-cement ratio")
    additive_type:   str   = Field(..., description="Supplementary cementitious material type")
    additive_pct:    float = Field(..., ge=0.0, le=30.0,
                                   description="Additive % by mass of binder")
    curing_temp_c:   float = Field(..., ge=20.0, le=80.0,
                                   description="Curing temperature in °C")
    curing_days:     int   = Field(..., ge=3, le=90,
                                   description="Curing duration in days")

    class Config:
        json_schema_extra = {
            "example": {
                "plastic_type": "PET",
                "replacement_pct": 15.0,
                "particle_size_mm": 4.0,
                "wc_ratio": 0.45,
                "additive_type": "fly_ash",
                "additive_pct": 10.0,
                "curing_temp_c": 27.0,
                "curing_days": 28,
            }
        }

    def validate_categoricals(self) -> None:
        if self.plastic_type not in PLASTIC_TYPE_CLASSES:
            raise ValueError(f"plastic_type must be one of {PLASTIC_TYPE_CLASSES}")
        if self.additive_type not in ADDITIVE_TYPE_CLASSES:
            raise ValueError(f"additive_type must be one of {ADDITIVE_TYPE_CLASSES}")


class PropertyResult(BaseModel):
    mean:       Optional[float]
    ci_90_low:  Optional[float]
    ci_90_high: Optional[float]


class PredictionResponse(BaseModel):
    predictions:          Dict[str, PropertyResult]
    shap_values:          Dict[str, Dict[str, float]]
    uncertainty_flag:     bool
    low_coverage_targets: List[str]

    class Config:
        json_schema_extra = {
            "example": {
                "predictions": {
                    "compressive_strength_mpa": {"mean": 32.1, "ci_90_low": 28.5, "ci_90_high": 35.7}
                },
                "shap_values": {},
                "uncertainty_flag": False,
                "low_coverage_targets": [],
            }
        }


class HealthResponse(BaseModel):
    status: str
    module: str


class SchemaResponse(BaseModel):
    input_fields:  Dict[str, dict]
    output_fields: List[str]
    plastic_type_classes:  List[str]
    additive_type_classes: List[str]

# ═══════════════════════════════════════════════════════════
# M4 — Application Recommendation Schemas
# ═══════════════════════════════════════════════════════════

class M4MixInput(BaseModel):
    """Mix parameters + M1 predicted properties for M4 recommendation."""

    # 8 mix parameters (same as MixInput)
    plastic_type:     str   = Field(..., description="Plastic type")
    replacement_pct:  float = Field(..., ge=0.0,  le=40.0)
    particle_size_mm: float = Field(..., ge=0.5,  le=20.0)
    wc_ratio:         float = Field(..., ge=0.35, le=0.65)
    additive_type:    str   = Field(..., description="Additive type")
    additive_pct:     float = Field(..., ge=0.0,  le=30.0)
    curing_temp_c:    float = Field(..., ge=20.0, le=80.0)
    curing_days:      int   = Field(..., ge=3,    le=90)

    # 7 M1 predicted properties
    compressive_strength_mpa: float = Field(..., ge=0.0)
    flexural_strength_mpa:    float = Field(..., ge=0.0)
    split_tensile_mpa:        float = Field(..., ge=0.0)
    density_kgm3:             float = Field(..., ge=500.0)
    water_absorption_pct:     float = Field(..., ge=0.0)
    thermal_conductivity_wm:  float = Field(..., ge=0.0)
    durability_index:         float = Field(..., ge=0.0, le=100.0)

    class Config:
        json_schema_extra = {
            "example": {
                "plastic_type": "LDPE",
                "replacement_pct": 30.0,
                "particle_size_mm": 2.0,
                "wc_ratio": 0.45,
                "additive_type": "fibres",
                "additive_pct": 0.5,
                "curing_temp_c": 25.0,
                "curing_days": 28,
                "compressive_strength_mpa": 22.82,
                "flexural_strength_mpa": 3.8,
                "split_tensile_mpa": 2.1,
                "density_kgm3": 1050.0,
                "water_absorption_pct": 4.2,
                "thermal_conductivity_wm": 0.42,
                "durability_index": 68.0,
            }
        }


class RAGAnalogueSchema(BaseModel):
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


class CostBenefitSchema(BaseModel):
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


class RecommendationResponse(BaseModel):
    primary_application:     str
    primary_confidence_pct:  float
    suitable_applications:   List[str]
    suitability_scores:      Dict[str, float]
    cost_benefit:            CostBenefitSchema
    rag_analogues:           List[RAGAnalogueSchema]

    class Config:
        json_schema_extra = {
            "example": {
                "primary_application": "plastic_sand_paver",
                "primary_confidence_pct": 87.3,
                "suitable_applications": ["plastic_sand_paver", "paving_block_light"],
                "suitability_scores": {"plastic_sand_paver": 78.5, "paving_block_light": 61.2},
                "cost_benefit": {
                    "plastic_mix_cost_inr_m3": 4120.0,
                    "conventional_cost_inr_m3": 5180.0,
                    "cost_saving_inr_m3": 1060.0,
                    "cost_saving_pct": 20.5,
                    "plastic_mix_cost_inr_m2": 588.6,
                    "conventional_cost_inr_m2": 740.0,
                    "cost_saving_inr_m2": 151.4,
                    "product_yield_m2_per_m3": 7.0,
                    "plastic_kg_per_m3": 140.2,
                    "additive_kg_per_m3": 1.9,
                },
                "rag_analogues": [],
            }
        }

# ═══════════════════════════════════════════════════════════
# M3 — Sustainability Scoring Schemas
# ═══════════════════════════════════════════════════════════

class ScoreRequest(BaseModel):
    """8 mix parameters + 7 M1 properties → M3 sustainability score."""
    plastic_type:             str   = Field(..., description="Plastic type")
    replacement_pct:          float = Field(..., ge=0.0,  le=40.0)
    particle_size_mm:         float = Field(..., ge=0.5,  le=20.0)
    wc_ratio:                 float = Field(..., ge=0.35, le=0.65)
    additive_type:            str   = Field(..., description="Additive type")
    additive_pct:             float = Field(..., ge=0.0,  le=30.0)
    curing_temp_c:            float = Field(..., ge=20.0, le=80.0)
    curing_days:              int   = Field(..., ge=3,    le=90)
    compressive_strength_mpa: float = Field(..., ge=0.0)
    flexural_strength_mpa:    float = Field(..., ge=0.0)
    split_tensile_mpa:        float = Field(..., ge=0.0)
    density_kgm3:             float = Field(..., ge=500.0)
    water_absorption_pct:     float = Field(..., ge=0.0)
    thermal_conductivity_wm:  float = Field(..., ge=0.0)
    durability_index:         float = Field(..., ge=0.0, le=100.0)


class ScoreResponse(BaseModel):
    sustainability_score:     float
    sustainability_grade:     str
    embodied_carbon_kgco2e_m3: float
    co2_saving_pct:           float
    plastic_diversion_kg_m3:  float
    pet_bottle_equiv:         float
    bis_overall_pass:         bool
    igbc_total_credits:       float
    griha_material_criterion_pts: float
    leed_total_points:        float
    total_green_credits:      float
    top_negative_factor:      str
    remediation_action_1:     str
    remediation_action_2:     str
    remediation_action_3:     str
    estimated_score_gain:     float


# ═══════════════════════════════════════════════════════════
# M2 — Mix Optimisation Schemas
# ═══════════════════════════════════════════════════════════

class OptimizeRequest(BaseModel):
    """Constraints and objective weights for M2 optimisation."""
    plastic_type:              Optional[str]   = Field(None, description="Fix plastic type or None for free search")
    replacement_pct_max:       float           = Field(40.0, ge=0.0,  le=40.0)
    compressive_strength_min:  float           = Field(20.0, ge=0.0)
    density_max_kgm3:          Optional[float] = Field(None)
    cost_max_inr_per_m3:       Optional[float] = Field(None)
    weight_compressive:        float           = Field(0.40, ge=0.0, le=1.0)
    weight_cost:               float           = Field(0.30, ge=0.0, le=1.0)
    weight_co2:                float           = Field(0.20, ge=0.0, le=1.0)
    weight_plastic_content:    float           = Field(0.10, ge=0.0, le=1.0)
    mode:                      str             = Field("constrained",
                                                       description="constrained | scenario")

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> "OptimizeRequest":
        total = (self.weight_compressive + self.weight_cost +
                 self.weight_co2 + self.weight_plastic_content)
        if abs(total - 1.0) > 0.01:
            raise ValueError(
                f"Objective weights must sum to 1.0 (got {total:.3f}). "
                "Adjust weight_compressive, weight_cost, weight_co2, weight_plastic_content."
            )
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "plastic_type": "PET",
                "replacement_pct_max": 25.0,
                "compressive_strength_min": 20.0,
                "weight_compressive": 0.40,
                "weight_cost": 0.30,
                "weight_co2": 0.20,
                "weight_plastic_content": 0.10,
                "mode": "constrained",
            }
        }


class OptimizeResponse(BaseModel):
    best_mix:               Dict[str, float]
    predicted_cs_mpa:       float
    predicted_cost_inr_m3:  float
    predicted_co2_kgco2e_m3: float
    predicted_plastic_diversion_kg_m3: float
    composite_score:        float
    mode:                   str        