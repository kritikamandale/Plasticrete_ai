"""
Feature vector builder for M4 classifiers.
"""
from __future__ import annotations

import numpy as np

from modules.m4_recommendation.model import classifiers


def build_feature_vector(mix_params: dict, m1_properties: dict) -> np.ndarray:
    """Build and return a (1, 15) feature array from mix params and M1 predictions."""
    plastic_map  = classifiers.config.get("plastic_type_map",
                       {"PET": 0, "HDPE": 1, "LDPE": 2, "PVC": 3, "PP": 4, "Mixed": 5})
    additive_map = classifiers.config.get("additive_type_map",
                       {"none": 0, "fly_ash": 1, "silica_fume": 2, "fibres": 3})

    feat = [
        plastic_map.get(mix_params["plastic_type"], 0),
        mix_params["replacement_pct"],
        mix_params["particle_size_mm"],
        mix_params["wc_ratio"],
        additive_map.get(mix_params.get("additive_type", "none"), 0),
        mix_params.get("additive_pct", 0.0),
        mix_params.get("curing_temp_c", 25.0),
        mix_params.get("curing_days", 28),
        m1_properties["compressive_strength_mpa"],
        m1_properties["flexural_strength_mpa"],
        m1_properties["split_tensile_mpa"],
        m1_properties["density_kgm3"],
        m1_properties["water_absorption_pct"],
        m1_properties["thermal_conductivity_wm"],
        m1_properties["durability_index"],
    ]
    return np.array([feat], dtype=float)
