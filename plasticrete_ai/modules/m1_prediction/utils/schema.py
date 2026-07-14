"""
Single source of truth for all column names, class lists, ranges, and the
PredictionResult contract.  Every other file imports constants from here —
no hardcoded strings elsewhere.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Input feature constants
# ---------------------------------------------------------------------------
PLASTIC_TYPE       = "plastic_type"
REPLACEMENT_PCT    = "replacement_pct"
PARTICLE_SIZE_MM   = "particle_size_mm"
WC_RATIO           = "wc_ratio"
ADDITIVE_TYPE      = "additive_type"
ADDITIVE_PCT       = "additive_pct"
CURING_TEMP_C      = "curing_temp_c"
CURING_DAYS        = "curing_days"

INPUT_FEATURES: List[str] = [
    PLASTIC_TYPE, REPLACEMENT_PCT, PARTICLE_SIZE_MM, WC_RATIO,
    ADDITIVE_TYPE, ADDITIVE_PCT, CURING_TEMP_C, CURING_DAYS,
]

# ---------------------------------------------------------------------------
# Target output constants
# ---------------------------------------------------------------------------
COMPRESSIVE_STRENGTH = "compressive_strength_mpa"
FLEXURAL_STRENGTH    = "flexural_strength_mpa"
SPLIT_TENSILE        = "split_tensile_mpa"
DENSITY              = "density_kgm3"
WATER_ABSORPTION     = "water_absorption_pct"
THERMAL_CONDUCTIVITY = "thermal_conductivity_wm"
DURABILITY_INDEX     = "durability_index"

TARGET_COLUMNS: List[str] = [
    COMPRESSIVE_STRENGTH, FLEXURAL_STRENGTH, SPLIT_TENSILE,
    DENSITY, WATER_ABSORPTION, THERMAL_CONDUCTIVITY, DURABILITY_INDEX,
]

# ---------------------------------------------------------------------------
# Metadata columns
# ---------------------------------------------------------------------------
SOURCE_DOI = "source_doi"
STUDY_TYPE = "study_type"   # "experimental" | "synthetic" | "pretraining"
MIX_ID     = "mix_id"

# ---------------------------------------------------------------------------
# Categorical class lists
# ---------------------------------------------------------------------------
PLASTIC_TYPE_CLASSES:  List[str] = ["PET", "HDPE", "LDPE", "PVC", "PP", "Mixed"]
ADDITIVE_TYPE_CLASSES: List[str] = ["fly_ash", "silica_fume", "fibres", "none"]

# ---------------------------------------------------------------------------
# Valid ranges — used for input validation AND CTGAN rejection sampling
# ---------------------------------------------------------------------------
INPUT_RANGES: Dict[str, tuple] = {
    REPLACEMENT_PCT:  (0.0,  40.0),
    PARTICLE_SIZE_MM: (0.5,  20.0),
    WC_RATIO:         (0.35, 0.65),
    ADDITIVE_PCT:     (0.0,  30.0),
    CURING_TEMP_C:    (20.0, 80.0),
    CURING_DAYS:      (3,    90),
}

TARGET_RANGES: Dict[str, tuple] = {
    COMPRESSIVE_STRENGTH: (0.0,    90.0),
    FLEXURAL_STRENGTH:    (0.0,    15.0),
    SPLIT_TENSILE:        (0.0,    10.0),
    DENSITY:              (1200.0, 2600.0),
    WATER_ABSORPTION:     (0.0,    25.0),
    THERMAL_CONDUCTIVITY: (0.10,   2.50),
    DURABILITY_INDEX:     (0.0,    100.0),
}

MIN_COVERAGE_ROWS = 50  # skip training a target model if fewer rows than this

# ---------------------------------------------------------------------------
# Derived feature name constants (produced by feature_engineering.py)
# ---------------------------------------------------------------------------
LOG_PARTICLE_SIZE  = "log_particle_size_mm"
LOG_CURING_DAYS    = "log_curing_days"
PLASTIC_NONE_FLAG  = "is_plain_concrete"
INTERACTION_PCT_WC = "replacement_pct_x_wc_ratio"
INTERACTION_PCT_AD = "replacement_pct_x_additive_pct"

DERIVED_FEATURES: List[str] = [
    LOG_PARTICLE_SIZE, LOG_CURING_DAYS, PLASTIC_NONE_FLAG,
    INTERACTION_PCT_WC, INTERACTION_PCT_AD,
]


# ---------------------------------------------------------------------------
# PredictionResult — the typed return value of predict()
# M2/M3/M4 unpack this dataclass — never change field names without bumping
# CONTRACT version
# ---------------------------------------------------------------------------
@dataclass
class PredictionResult:
    compressive_strength_mpa:  Optional[float] = None
    flexural_strength_mpa:     Optional[float] = None
    split_tensile_mpa:         Optional[float] = None
    density_kgm3:              Optional[float] = None
    water_absorption_pct:      Optional[float] = None
    thermal_conductivity_wm:   Optional[float] = None
    durability_index:          Optional[float] = None
    ci_low:                    Dict[str, float] = field(default_factory=dict)
    ci_high:                   Dict[str, float] = field(default_factory=dict)
    shap_values:               Dict[str, Dict[str, float]] = field(default_factory=dict)
    uncertainty_flag:          bool = False
    low_coverage_targets:      List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialise to a plain JSON-compatible dict."""
        return {
            COMPRESSIVE_STRENGTH: self.compressive_strength_mpa,
            FLEXURAL_STRENGTH:    self.flexural_strength_mpa,
            SPLIT_TENSILE:        self.split_tensile_mpa,
            DENSITY:              self.density_kgm3,
            WATER_ABSORPTION:     self.water_absorption_pct,
            THERMAL_CONDUCTIVITY: self.thermal_conductivity_wm,
            DURABILITY_INDEX:     self.durability_index,
            "ci_low":             self.ci_low,
            "ci_high":            self.ci_high,
            "shap_values":        self.shap_values,
            "uncertainty_flag":   self.uncertainty_flag,
            "low_coverage_targets": self.low_coverage_targets,
        }
