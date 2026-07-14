"""
PlastiCreteEnsemble: weighted combination of XGBoost + RF + DNN with uncertainty.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from loguru import logger
from sklearn.metrics import r2_score

from modules.m1_prediction.utils.preprocessor import Preprocessor
from modules.m1_prediction.utils.schema import (
    COMPRESSIVE_STRENGTH, TARGET_COLUMNS, PredictionResult,
)
from modules.m1_prediction.model.xgboost_model import XGBoostMultiOutput
from modules.m1_prediction.model.random_forest_model import RandomForestMultiOutput
from modules.m1_prediction.model.dnn_model import DNNModel


_DEFAULT_WEIGHTS = [0.40, 0.35, 0.25]  # [xgb, rf, dnn]
_CI_Z = 1.645  # 90% CI


class PlastiCreteEnsemble:

    def __init__(
        self,
        xgb_model: XGBoostMultiOutput,
        rf_model: RandomForestMultiOutput,
        dnn_model: DNNModel,
        preprocessor: Preprocessor,
        config: Optional[dict] = None,
    ) -> None:
        self.xgb = xgb_model
        self.rf  = rf_model
        self.dnn = dnn_model
        self.preprocessor = preprocessor
        self.config = config or {}
        self.weights: Dict[str, List[float]] = {
            t: list(_DEFAULT_WEIGHTS) for t in TARGET_COLUMNS
        }
        self._shap_explainer = None  # lazily initialised
        self._uncertainty_thresholds = (
            self.config.get("ensemble", {})
            .get("uncertainty_flag_threshold", {})
        )
        if not self._uncertainty_thresholds:
            self._uncertainty_thresholds = {t: 0.30 for t in TARGET_COLUMNS}

    # ------------------------------------------------------------------
    # Weight computation (per-target validation R2)
    # ------------------------------------------------------------------

    def compute_weights(self, X_val: np.ndarray, y_val: np.ndarray) -> None:
        """Compute R2-based weights on validation set. Fallback if < 10 rows."""
        xgb_preds = self.xgb.predict(X_val)
        rf_preds, _ = self.rf.predict_with_std(X_val)
        dnn_preds   = self.dnn.predict(X_val)

        header = f"{'Target':<35} {'XGB':>6} {'RF':>6} {'DNN':>6} -> {'w_xgb':>6} {'w_rf':>6} {'w_dnn':>6}"
        logger.info("Ensemble weight computation:")
        logger.info("-" * len(header))
        logger.info(header)
        logger.info("-" * len(header))

        for i, target in enumerate(TARGET_COLUMNS):
            mask = ~np.isnan(y_val[:, i])
            if mask.sum() < 10:
                self.weights[target] = list(_DEFAULT_WEIGHTS)
                logger.info(f"  {target:<35}  <10 val rows -> fallback weights")
                continue

            yt = y_val[mask, i]
            scores = []
            for preds in [xgb_preds, rf_preds, dnn_preds]:
                pt = preds[mask, i]
                if np.isnan(pt).all():
                    scores.append(0.0)
                else:
                    scores.append(max(0.0, r2_score(yt, pt)))

            total = sum(scores)
            if total < 1e-8:
                w = list(_DEFAULT_WEIGHTS)
            else:
                w = [s / total for s in scores]

            self.weights[target] = w
            logger.info(
                f"  {target:<35} {scores[0]:>6.3f} {scores[1]:>6.3f} {scores[2]:>6.3f}"
                f" -> {w[0]:>6.3f} {w[1]:>6.3f} {w[2]:>6.3f}"
            )

    # ------------------------------------------------------------------
    # Single prediction with uncertainty + SHAP
    # ------------------------------------------------------------------

    def predict(self, input_dict: dict) -> PredictionResult:
        X = self.preprocessor.transform_input(input_dict)  # (1, n_features)

        xgb_pred = self.xgb.predict(X)                          # (1, 7)
        rf_mean, rf_std = self.rf.predict_with_std(X)           # (1, 7)
        dnn_mean, dnn_std = self.dnn.predict_mc_dropout(X)      # (1, 7)

        # Weighted mean
        means_scaled = np.zeros((1, len(TARGET_COLUMNS)))
        for i, target in enumerate(TARGET_COLUMNS):
            w = self.weights[target]
            means_scaled[0, i] = (
                w[0] * xgb_pred[0, i] +
                w[1] * rf_mean[0, i] +
                w[2] * dnn_mean[0, i]
            )

        # Combined uncertainty: take max of RF std, DNN std, disagreement std
        disagreement = np.std(
            [xgb_pred[0], rf_mean[0], dnn_mean[0]], axis=0, keepdims=True
        )
        final_std = np.maximum(rf_std, np.maximum(dnn_std, disagreement))  # (1, 7)

        # Inverse-transform to original units
        means = self.preprocessor.inverse_transform_targets(means_scaled)[0]
        stds  = self._scale_std_to_original(final_std[0])

        ci_low  = {t: float(means[i] - _CI_Z * stds[i]) for i, t in enumerate(TARGET_COLUMNS)}
        ci_high = {t: float(means[i] + _CI_Z * stds[i]) for i, t in enumerate(TARGET_COLUMNS)}

        # Uncertainty flag
        unc_flag = False
        for i, t in enumerate(TARGET_COLUMNS):
            if means[i] and abs(means[i]) > 1e-6:
                width_rel = (ci_high[t] - ci_low[t]) / abs(means[i])
                thr = self._uncertainty_thresholds.get(t, 0.30)
                if width_rel > thr:
                    unc_flag = True
                    break

        # SHAP (lazily compute)
        shap_vals: Dict[str, Dict[str, float]] = {}
        if self._shap_explainer is not None:
            try:
                shap_vals = self._shap_explainer.explain_all_targets(X)
            except Exception as exc:
                logger.warning(f"SHAP failed: {exc}")

        low_coverage = list(
            set(self.xgb.low_coverage_targets) |
            set(self.rf.low_coverage_targets)
        )

        result = PredictionResult(
            compressive_strength_mpa  = _safe_float(means, TARGET_COLUMNS.index(COMPRESSIVE_STRENGTH)),
            flexural_strength_mpa     = _safe_float(means, 1),
            split_tensile_mpa         = _safe_float(means, 2),
            density_kgm3              = _safe_float(means, 3),
            water_absorption_pct      = _safe_float(means, 4),
            thermal_conductivity_wm   = _safe_float(means, 5),
            durability_index          = _safe_float(means, 6),
            ci_low                    = ci_low,
            ci_high                   = ci_high,
            shap_values               = shap_vals,
            uncertainty_flag          = unc_flag,
            low_coverage_targets      = low_coverage,
        )
        return result

    def _scale_std_to_original(self, std_scaled: np.ndarray) -> np.ndarray:
        """Convert per-target standard deviation from scaled to original units."""
        std_orig = std_scaled.copy()
        for i, t in enumerate(TARGET_COLUMNS):
            sc = self.preprocessor.target_scalers.get(t)
            if sc is not None and hasattr(sc, "scale_"):
                std_orig[i] = std_scaled[i] * sc.scale_[0]
        return std_orig

    # ------------------------------------------------------------------
    # Batch prediction (fast -- no SHAP, no MC Dropout)
    # ------------------------------------------------------------------

    def predict_batch(
        self, X: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Vectorised prediction for M2 optimisation loop. No SHAP, RF std only.
        Returns (means, ci_low, ci_high) each shape (n_samples, 7) in original units.
        """
        xgb_pred = self.xgb.predict(X)
        rf_mean, rf_std = self.rf.predict_with_std(X)
        dnn_pred = self.dnn.predict(X)

        means_scaled = np.zeros_like(xgb_pred)
        for i, target in enumerate(TARGET_COLUMNS):
            w = self.weights[target]
            means_scaled[:, i] = (
                w[0] * xgb_pred[:, i] +
                w[1] * rf_mean[:, i] +
                w[2] * dnn_pred[:, i]
            )

        means   = self.preprocessor.inverse_transform_targets(means_scaled)
        stds_orig = np.zeros_like(rf_std)
        for i, t in enumerate(TARGET_COLUMNS):
            sc = self.preprocessor.target_scalers.get(t)
            if sc is not None and hasattr(sc, "scale_"):
                stds_orig[:, i] = rf_std[:, i] * sc.scale_[0]
            else:
                stds_orig[:, i] = rf_std[:, i]

        ci_low  = means - _CI_Z * stds_orig
        ci_high = means + _CI_Z * stds_orig
        return means, ci_low, ci_high

    def set_shap_explainer(self, explainer) -> None:
        self._shap_explainer = explainer

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, save_dir: str | Path) -> None:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        self.xgb.save(save_dir / "xgboost")
        self.rf.save(save_dir / "random_forest")
        self.dnn.save(save_dir / "dnn_model.pt")
        self.preprocessor.save(save_dir / "preprocessor")

        with open(save_dir / "ensemble_weights.json", "w") as f:
            json.dump(self.weights, f, indent=2)
        with open(save_dir / "ensemble_config.json", "w") as f:
            json.dump(self.config, f, indent=2)

        logger.info(f"PlastiCreteEnsemble saved -> {save_dir}")

    @classmethod
    def from_saved(cls, save_dir: str | Path, config: Optional[dict] = None) -> "PlastiCreteEnsemble":
        save_dir = Path(save_dir)

        cfg_path = save_dir / "ensemble_config.json"
        if cfg_path.exists() and config is None:
            with open(cfg_path) as f:
                config = json.load(f)

        preprocessor = Preprocessor.load(save_dir / "preprocessor")
        xgb = XGBoostMultiOutput.load(save_dir / "xgboost", config)
        rf  = RandomForestMultiOutput.load(save_dir / "random_forest", config)
        dnn = DNNModel.load(save_dir / "dnn_model.pt", config)

        obj = cls(xgb, rf, dnn, preprocessor, config)

        weights_path = save_dir / "ensemble_weights.json"
        if weights_path.exists():
            with open(weights_path) as f:
                obj.weights = json.load(f)

        logger.info(f"PlastiCreteEnsemble loaded from {save_dir}")
        return obj


def _safe_float(arr: np.ndarray, idx: int) -> Optional[float]:
    v = float(arr[idx])
    return None if np.isnan(v) else v

