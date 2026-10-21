"""
Contract and unit tests for Module 3 — Sustainability & Compliance Scoring Engine.
"""
from __future__ import annotations

import pytest
import modules.m3_sustainability as m3


@pytest.fixture(scope="module", autouse=True)
def setup_m3():
    m3.load_models()


SAMPLE_MIX = {
    "plastic_type": "PET",
    "replacement_pct": 15.0,
    "particle_size_mm": 4.0,
    "wc_ratio": 0.45,
    "additive_type": "fly_ash",
    "additive_pct": 10.0,
    "curing_temp_c": 27.0,
    "curing_days": 28,
}

SAMPLE_M1_PROPS = {
    "compressive_strength_mpa": 28.5,
    "flexural_strength_mpa": 4.2,
    "split_tensile_mpa": 2.8,
    "density_kgm3": 2250.0,
    "water_absorption_pct": 4.5,
    "thermal_conductivity_wm": 0.85,
    "durability_index": 72.0,
}

REQUIRED_SCORE_KEYS = {
    "sustainability_score",
    "sustainability_grade",
    "embodied_carbon_kgco2e_m3",
    "co2_saving_pct",
    "plastic_diversion_kg_m3",
    "pet_bottle_equiv",
    "bis_overall_pass",
    "igbc_total_credits",
    "griha_material_criterion_pts",
    "leed_total_points",
    "total_green_credits",
    "top_negative_factor",
    "remediation_action_1",
    "remediation_action_2",
    "remediation_action_3",
    "estimated_score_gain",
    "mass_balance",
    "use_class_gates",
}


class TestM3Contract:
    def test_public_surface(self):
        """Verify public API functions exist."""
        assert hasattr(m3, "load_models")
        assert hasattr(m3, "score_mix")
        assert callable(m3.load_models)
        assert callable(m3.score_mix)

    def test_load_models_idempotent(self):
        """Calling load_models multiple times should not raise errors."""
        m3.load_models()
        m3.load_models()

    def test_score_mix_returns_all_keys(self):
        """score_mix must return exactly the 16 ScoreResponse fields."""
        result = m3.score_mix(SAMPLE_MIX, SAMPLE_M1_PROPS)
        assert isinstance(result, dict)
        assert set(result.keys()) == REQUIRED_SCORE_KEYS

    def test_score_mix_value_types_and_ranges(self):
        """Verify value types and realistic domains."""
        result = m3.score_mix(SAMPLE_MIX, SAMPLE_M1_PROPS)

        assert isinstance(result["sustainability_score"], (int, float))
        assert 0.0 <= result["sustainability_score"] <= 100.0

        assert isinstance(result["sustainability_grade"], str)
        assert len(result["sustainability_grade"]) > 0

        assert isinstance(result["embodied_carbon_kgco2e_m3"], (int, float))
        assert isinstance(result["co2_saving_pct"], (int, float))
        assert isinstance(result["plastic_diversion_kg_m3"], (int, float))
        assert result["plastic_diversion_kg_m3"] > 0

        assert isinstance(result["pet_bottle_equiv"], (int, float))
        assert result["pet_bottle_equiv"] >= 0

        assert isinstance(result["bis_overall_pass"], bool)
        assert isinstance(result["igbc_total_credits"], (int, float))
        assert isinstance(result["griha_material_criterion_pts"], (int, float))
        assert isinstance(result["leed_total_points"], (int, float))
        assert isinstance(result["total_green_credits"], (int, float))

        assert isinstance(result["top_negative_factor"], str)
        assert isinstance(result["remediation_action_1"], str)
        assert isinstance(result["remediation_action_2"], str)
        assert isinstance(result["remediation_action_3"], str)
        assert isinstance(result["estimated_score_gain"], (int, float))

    def test_score_mix_different_plastics(self):
        """Test sustainability scoring across different plastic types."""
        for ptype in ["PET", "HDPE", "LDPE", "PVC", "PP", "Mixed"]:
            mix = dict(SAMPLE_MIX, plastic_type=ptype)
            res = m3.score_mix(mix, SAMPLE_M1_PROPS)
            assert res["sustainability_score"] > 0
            assert res["plastic_diversion_kg_m3"] > 0
