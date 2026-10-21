"""
Contract tests: public API import surface and schema constants for M2.
"""


class TestPublicImport:
    def test_can_import_public_functions(self):
        from modules.m2_optimization import load_models, run_optimization
        assert callable(load_models)
        assert callable(run_optimization)

    def test_no_circular_import(self):
        import importlib
        import modules.m2_optimization as m2
        importlib.reload(m2)


class TestSchemaConstants:
    def test_plastic_types_present(self):
        from modules.m2_optimization.utils.schema import PLASTIC_TYPES
        assert "PET" in PLASTIC_TYPES
        assert "Mixed" in PLASTIC_TYPES
        assert len(PLASTIC_TYPES) == 6

    def test_additive_types_present(self):
        from modules.m2_optimization.utils.schema import ADDITIVE_TYPES
        assert "none" in ADDITIVE_TYPES
        assert len(ADDITIVE_TYPES) == 4

    def test_norm_denominators_positive(self):
        from modules.m2_optimization.utils.schema import (
            CS_NORM_MAX, COST_NORM_MAX, CO2_NORM_MAX, DIV_NORM_MAX,
        )
        assert CS_NORM_MAX > 0
        assert COST_NORM_MAX > 0
        assert CO2_NORM_MAX > 0
        assert DIV_NORM_MAX > 0


class TestOptimizationResultShape:
    def test_result_has_required_keys(self, monkeypatch):
        """Strength is injected. Cost and plastic mass still come from the mass balance."""
        from modules.m2_optimization.model import optimizer

        def fake_m1(mix):
            return {
                "compressive_strength_mpa": 32.0,
                "flexural_strength_mpa": 4.0,
                "split_tensile_mpa": 2.5,
                "density_kgm3": 2200.0,
                "water_absorption_pct": 4.0,
                "thermal_conductivity_wm": 0.8,
                "durability_index": 70.0,
                "ci_low": {
                    "compressive_strength_mpa": 30.5,
                    "water_absorption_pct": 3.0,
                    "density_kgm3": 2100.0,
                },
                "ci_high": {
                    "compressive_strength_mpa": 34.0,
                    "water_absorption_pct": 5.0,
                    "density_kgm3": 2300.0,
                },
            }

        monkeypatch.setattr(optimizer, "_m1_properties", fake_m1)
        result = optimizer.run(
            constraints={
                "plastic_type": "PET",
                "compressive_strength_min": 20.0,
                "replacement_pct_max": 30.0,
                "plastic_diversion_min_kg_m3": 40.0,
                "use_class": "paver",
            },
            weights={"compressive_strength": 0.4, "cost_per_m3": 0.3,
                     "co2_per_m3": 0.2, "plastic_content_pct": 0.1},
            mode="constrained",
        )
        required_keys = {
            "best_mix", "predicted_cs_mpa", "predicted_cost_inr_m3",
            "predicted_co2_kgco2e_m3", "predicted_plastic_diversion_kg_m3",
            "composite_score", "mode", "tradeoff_points", "mass_balance",
            "prediction_source", "feasible",
        }
        assert required_keys <= set(result.keys())
        assert result["prediction_source"] == "m1"
        assert result["best_mix"]["plastic_type"] == "PET"
        assert result["best_mix"]["additive_type"] in {"fly_ash", "silica_fume", "fibres", "none"}
        assert result["mass_balance"]["plastic_kg_m3"] == result["predicted_plastic_diversion_kg_m3"]
        assert result["mass_balance"]["cost_inr_m3"] == result["predicted_cost_inr_m3"]
        assert result["feasible"] is True
        assert 1 <= len(result["tradeoff_points"]) <= 3
        assert any(point["selected"] for point in result["tradeoff_points"])
        labels = {point["label"] for point in result["tradeoff_points"]}
        assert "balanced" in labels or "max_strength" in labels
