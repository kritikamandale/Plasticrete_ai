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
        """Verify run_optimization returns the correct response shape (mocked predict)."""
        from modules.m2_optimization.model import surrogate
        import modules.m2_optimization.utils.encoding as enc

        # Patch surrogate.is_loaded so load_models is skipped
        monkeypatch.setattr(surrogate, "_loaded", True)
        monkeypatch.setattr(enc, "predict", lambda *a, **k: (30.0, 4000.0, 300.0, 120.0))

        from modules.m2_optimization.model.optimizer import run
        result = run(
            constraints={"compressive_strength_min": 20.0, "replacement_pct_max": 30.0},
            weights={"compressive_strength": 0.4, "cost_per_m3": 0.3,
                     "co2_per_m3": 0.2, "plastic_content_pct": 0.1},
        )
        required_keys = {
            "best_mix", "predicted_cs_mpa", "predicted_cost_inr_m3",
            "predicted_co2_kgco2e_m3", "predicted_plastic_diversion_kg_m3",
            "composite_score", "mode",
        }
        assert required_keys == set(result.keys())
