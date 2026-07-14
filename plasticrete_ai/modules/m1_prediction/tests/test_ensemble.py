"""
Tests for PlastiCreteEnsemble: PredictionResult fields, batch shape, weights, uncertainty flag.
"""
import numpy as np
import pytest

from modules.m1_prediction.utils.schema import PredictionResult, TARGET_COLUMNS


# ---------------------------------------------------------------------------
# Minimal stubs — avoids training real models in unit tests
# ---------------------------------------------------------------------------

class _FakeXGB:
    low_coverage_targets = []
    def predict(self, X):
        return np.ones((len(X), 7)) * 30.0
    def save(self, d): pass

class _FakeRF:
    low_coverage_targets = []
    def predict_with_std(self, X):
        mean = np.ones((len(X), 7)) * 30.0
        std  = np.ones((len(X), 7)) * 1.0
        return mean, std
    def save(self, d): pass

class _WideBandRF:
    """RF that returns very wide std to trigger uncertainty_flag."""
    low_coverage_targets = []
    def predict_with_std(self, X):
        mean = np.ones((len(X), 7)) * 10.0
        std  = np.ones((len(X), 7)) * 8.0   # 90% CI width = 2*1.645*8 ≈ 26 >> 30% of 10
        return mean, std
    def save(self, d): pass

class _FakeDNN:
    def predict(self, X):
        return np.ones((len(X), 7)) * 30.0
    def predict_mc_dropout(self, X, n_passes=50):
        mean = np.ones((len(X), 7)) * 30.0
        std  = np.ones((len(X), 7)) * 0.5
        return mean, std
    def save(self, p): pass

class _FakePreprocessor:
    feature_names = ["f0", "f1"]
    target_scalers = {}

    def transform_input(self, d):
        return np.zeros((1, 2))

    def inverse_transform_targets(self, y):
        return y.copy()


def _make_ensemble(rf=None):
    from modules.m1_prediction.model.ensemble import PlastiCreteEnsemble
    xgb  = _FakeXGB()
    _rf  = rf or _FakeRF()
    dnn  = _FakeDNN()
    prep = _FakePreprocessor()
    ens  = PlastiCreteEnsemble(xgb, _rf, dnn, prep, config={})
    return ens


class TestPredictReturnType:
    def test_returns_prediction_result(self):
        ens    = _make_ensemble()
        result = ens.predict({"plastic_type": "PET", "replacement_pct": 10.0,
                               "particle_size_mm": 4.0, "wc_ratio": 0.45,
                               "additive_type": "none", "additive_pct": 0.0,
                               "curing_temp_c": 27.0, "curing_days": 28})
        assert isinstance(result, PredictionResult)

    def test_all_target_fields_present(self):
        ens    = _make_ensemble()
        result = ens.predict({})
        d      = result.to_dict()
        for t in TARGET_COLUMNS:
            assert t in d, f"Missing target '{t}' in to_dict()"

    def test_ci_keys_match_targets(self):
        ens    = _make_ensemble()
        result = ens.predict({})
        for t in TARGET_COLUMNS:
            assert t in result.ci_low,  f"Missing ci_low[{t}]"
            assert t in result.ci_high, f"Missing ci_high[{t}]"


class TestPredictBatch:
    def test_returns_three_arrays(self):
        ens = _make_ensemble()
        X   = np.zeros((5, 2))
        out = ens.predict_batch(X)
        assert len(out) == 3

    def test_shape_n_by_7(self):
        ens = _make_ensemble()
        X   = np.zeros((8, 2))
        means, ci_low, ci_high = ens.predict_batch(X)
        for arr in (means, ci_low, ci_high):
            assert arr.shape == (8, 7), f"Expected (8,7), got {arr.shape}"

    def test_ci_low_le_mean_le_ci_high(self):
        ens = _make_ensemble()
        X   = np.zeros((10, 2))
        means, ci_low, ci_high = ens.predict_batch(X)
        assert np.all(ci_low <= means + 1e-6)
        assert np.all(means <= ci_high + 1e-6)


class TestUncertaintyFlag:
    def test_flag_triggers_wide_ci(self):
        ens = _make_ensemble(rf=_WideBandRF())
        ens.config = {
            "ensemble": {"uncertainty_flag_threshold": {t: 0.10 for t in TARGET_COLUMNS}}
        }
        ens._uncertainty_thresholds = {t: 0.10 for t in TARGET_COLUMNS}
        result = ens.predict({})
        assert result.uncertainty_flag is True

    def test_flag_off_narrow_ci(self):
        ens = _make_ensemble()   # std=1.0, mean=30, rel_width ≈ 0.11
        ens._uncertainty_thresholds = {t: 0.50 for t in TARGET_COLUMNS}
        result = ens.predict({})
        assert result.uncertainty_flag is False


class TestWeights:
    def test_default_weights_sum_to_one(self):
        ens = _make_ensemble()
        for target, w in ens.weights.items():
            assert abs(sum(w) - 1.0) < 1e-6, f"Weights for {target} don't sum to 1: {w}"

    def test_compute_weights_sum_to_one(self):
        ens = _make_ensemble()
        X_val = np.zeros((20, 2))
        y_val = np.ones((20, 7)) * 30.0
        y_val[:, 2] = np.nan   # split_tensile has no data
        ens.compute_weights(X_val, y_val)
        for target, w in ens.weights.items():
            assert abs(sum(w) - 1.0) < 1e-6, f"Weights after compute don't sum to 1: {target} {w}"
