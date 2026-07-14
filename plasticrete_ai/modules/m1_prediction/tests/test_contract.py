"""
Contract tests: public API import surface, circular imports, PredictionResult serialisation.
"""
import json

import numpy as np
import pytest


class TestPublicImport:
    def test_can_import_three_functions(self):
        from modules.m1_prediction import predict, predict_batch, load_ensemble
        assert callable(predict)
        assert callable(predict_batch)
        assert callable(load_ensemble)

    def test_get_preprocessor_importable(self):
        from modules.m1_prediction import get_preprocessor
        assert callable(get_preprocessor)

    def test_prediction_result_importable(self):
        from modules.m1_prediction import PredictionResult
        assert PredictionResult is not None

    def test_no_circular_import(self):
        import importlib
        # Re-importing should not raise
        import modules.m1_prediction as m1
        importlib.reload(m1)


class TestPredictionResultContract:
    def _make_result(self):
        from modules.m1_prediction.utils.schema import PredictionResult, TARGET_COLUMNS
        return PredictionResult(
            compressive_strength_mpa=32.1,
            flexural_strength_mpa=4.5,
            split_tensile_mpa=None,
            density_kgm3=2200.0,
            water_absorption_pct=5.0,
            thermal_conductivity_wm=0.85,
            durability_index=78.0,
            ci_low={t: 0.0 for t in TARGET_COLUMNS},
            ci_high={t: 50.0 for t in TARGET_COLUMNS},
            shap_values={"compressive_strength_mpa": {"replacement_pct": -0.5}},
            uncertainty_flag=False,
            low_coverage_targets=["durability_index"],
        )

    def test_to_dict_is_json_serialisable(self):
        result = self._make_result()
        d = result.to_dict()
        serialised = json.dumps(d)  # must not raise
        assert isinstance(serialised, str)

    def test_to_dict_contains_all_targets(self):
        from modules.m1_prediction.utils.schema import TARGET_COLUMNS
        result = self._make_result()
        d = result.to_dict()
        for t in TARGET_COLUMNS:
            assert t in d, f"to_dict() missing target '{t}'"

    def test_none_values_preserved_in_dict(self):
        result = self._make_result()
        d = result.to_dict()
        from modules.m1_prediction.utils.schema import SPLIT_TENSILE
        assert d[SPLIT_TENSILE] is None

    def test_field_names_stable(self):
        """
        Verify the exact PredictionResult field names match the CONTRACT spec.
        Any change here is a breaking change → must bump CONTRACT version.
        """
        from modules.m1_prediction.utils.schema import PredictionResult
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(PredictionResult)}
        required = {
            "compressive_strength_mpa", "flexural_strength_mpa", "split_tensile_mpa",
            "density_kgm3", "water_absorption_pct", "thermal_conductivity_wm",
            "durability_index", "ci_low", "ci_high", "shap_values",
            "uncertainty_flag", "low_coverage_targets",
        }
        missing = required - field_names
        assert not missing, f"Breaking change: PredictionResult missing fields: {missing}"


class TestSchemaConstants:
    def test_target_columns_order(self):
        from modules.m1_prediction.utils.schema import (
            TARGET_COLUMNS, COMPRESSIVE_STRENGTH, FLEXURAL_STRENGTH,
        )
        assert TARGET_COLUMNS[0] == COMPRESSIVE_STRENGTH
        assert TARGET_COLUMNS[1] == FLEXURAL_STRENGTH
        assert len(TARGET_COLUMNS) == 7

    def test_input_features_count(self):
        from modules.m1_prediction.utils.schema import INPUT_FEATURES
        assert len(INPUT_FEATURES) == 8
