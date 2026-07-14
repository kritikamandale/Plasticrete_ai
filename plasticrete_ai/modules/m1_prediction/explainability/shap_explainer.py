"""
SHAP explainer: TreeExplainer for XGB/RF, GradientExplainer for DNN.
Ensemble SHAP = weighted average across models.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

from modules.m1_prediction.utils.schema import TARGET_COLUMNS

try:
    import shap
    _SHAP_AVAILABLE = True
except ImportError:
    _SHAP_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    _MPL_AVAILABLE = True
except ImportError:
    _MPL_AVAILABLE = False


class SHAPExplainer:
    def __init__(self, config, ensemble, preprocessor) -> None:
        self.config       = config
        self.ensemble     = ensemble
        self.preprocessor = preprocessor
        self._xgb_explainers: Dict[str, "shap.TreeExplainer"] = {}
        self._rf_explainers:  Dict[str, "shap.TreeExplainer"] = {}
        self._dnn_explainer = None
        self._background: Optional[np.ndarray] = None
        self._fitted = False

    def fit(self, X_background: np.ndarray) -> None:
        if not _SHAP_AVAILABLE:
            logger.warning("shap not installed — SHAP explanations disabled")
            return

        cfg = (self.config or {}).get("explainability", {}).get("shap", {})
        n_bg = min(cfg.get("background_samples", 100), len(X_background))
        idx  = np.random.choice(len(X_background), n_bg, replace=False)
        self._background = X_background[idx]

        # XGBoost TreeExplainers
        for target, model in self.ensemble.xgb.models.items():
            try:
                self._xgb_explainers[target] = shap.TreeExplainer(model)
            except Exception as exc:
                logger.warning(f"SHAP XGB [{target}]: {exc}")

        # RF TreeExplainers (use 50 trees for speed)
        for target, model in self.ensemble.rf.models.items():
            try:
                self._rf_explainers[target] = shap.TreeExplainer(model)
            except Exception as exc:
                logger.warning(f"SHAP RF [{target}]: {exc}")

        # DNN GradientExplainer
        try:
            import torch
            dnn    = self.ensemble.dnn
            X_t    = torch.tensor(self._background, dtype=torch.float32, device=dnn.device)
            self._dnn_explainer = shap.GradientExplainer(dnn.model, X_t)
        except Exception as exc:
            logger.warning(f"SHAP DNN GradientExplainer: {exc}")

        self._fitted = True
        logger.info("SHAPExplainer fitted")

    def _get_shap_single(self, X_instance: np.ndarray, target: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Returns (xgb_shap, rf_shap, dnn_shap) each shape (n_features,) or zeros."""
        n_feat = X_instance.shape[1]
        zeros  = np.zeros(n_feat)

        xgb_sv = zeros.copy()
        if target in self._xgb_explainers:
            try:
                sv = self._xgb_explainers[target].shap_values(X_instance)
                xgb_sv = np.asarray(sv).ravel()[:n_feat]
            except Exception:
                pass

        rf_sv = zeros.copy()
        if target in self._rf_explainers:
            try:
                sv = self._rf_explainers[target].shap_values(X_instance)
                rf_sv = np.asarray(sv).ravel()[:n_feat]
            except Exception:
                pass

        dnn_sv = zeros.copy()
        if self._dnn_explainer is not None:
            try:
                import torch
                X_t = torch.tensor(X_instance, dtype=torch.float32,
                                   device=self.ensemble.dnn.device)
                sv  = self._dnn_explainer.shap_values(X_t)
                if isinstance(sv, list):
                    idx = TARGET_COLUMNS.index(target) if target in TARGET_COLUMNS else 0
                    dnn_sv = np.asarray(sv[idx]).ravel()[:n_feat]
                else:
                    dnn_sv = np.asarray(sv).ravel()[:n_feat]
            except Exception:
                pass

        return xgb_sv, rf_sv, dnn_sv

    def explain_prediction(self, X_instance: np.ndarray, target: str) -> Dict[str, float]:
        if not self._fitted:
            return {}
        w = self.ensemble.weights.get(target, [0.40, 0.35, 0.25])
        xsv, rsv, dsv = self._get_shap_single(X_instance, target)
        ensemble_sv = w[0] * xsv + w[1] * rsv + w[2] * dsv

        feat_names = self.preprocessor.feature_names or [f"f{i}" for i in range(len(ensemble_sv))]
        return {feat_names[i]: float(ensemble_sv[i]) for i in range(len(feat_names))}

    def explain_all_targets(self, X_instance: np.ndarray) -> Dict[str, Dict[str, float]]:
        if not self._fitted:
            return {}
        return {t: self.explain_prediction(X_instance, t) for t in TARGET_COLUMNS}

    def global_importance(self, X_all: np.ndarray, target: str) -> Dict[str, float]:
        if not self._fitted or target not in self._xgb_explainers:
            return {}
        try:
            sv = self._xgb_explainers[target].shap_values(X_all)
            mean_abs = np.abs(np.asarray(sv)).mean(axis=0)
            feat_names = self.preprocessor.feature_names or [f"f{i}" for i in range(len(mean_abs))]
            ranked = dict(sorted(zip(feat_names, mean_abs.tolist()), key=lambda x: -x[1]))
            return ranked
        except Exception as exc:
            logger.warning(f"global_importance [{target}]: {exc}")
            return {}

    def compliance_remediation_path(
        self, X_instance: np.ndarray, target: str,
        predicted: float, threshold: float,
    ) -> List[dict]:
        """
        If predicted < threshold, find top 3 features with most negative SHAP
        and suggest changes to bring the value above threshold.
        """
        if predicted >= threshold:
            return []
        sv_dict = self.explain_prediction(X_instance, target)
        neg_features = sorted(sv_dict.items(), key=lambda x: x[1])[:3]
        actions = []
        for feat, sv_val in neg_features:
            actions.append({
                "feature":        feat,
                "direction":      "decrease" if sv_val < 0 else "increase",
                "estimated_gain": abs(sv_val),
                "action_text":    (
                    f"Adjusting '{feat}' could recover approximately "
                    f"{abs(sv_val):.2f} units toward BIS compliance."
                ),
            })
        return actions

    def plot_waterfall(self, X_instance: np.ndarray, target: str, save_path: Optional[str] = None) -> None:
        if not _SHAP_AVAILABLE or not _MPL_AVAILABLE or not self._fitted:
            return
        if target not in self._xgb_explainers:
            return
        try:
            sv = self._xgb_explainers[target](X_instance)
            shap.plots.waterfall(sv[0], show=False)
            if save_path:
                plt.savefig(save_path, bbox_inches="tight")
                plt.close()
        except Exception as exc:
            logger.warning(f"plot_waterfall [{target}]: {exc}")

    def plot_summary(self, X_all: np.ndarray, target: str, save_path: Optional[str] = None) -> None:
        if not _SHAP_AVAILABLE or not _MPL_AVAILABLE or not self._fitted:
            return
        if target not in self._xgb_explainers:
            return
        try:
            sv = self._xgb_explainers[target].shap_values(X_all)
            shap.summary_plot(sv, X_all, feature_names=self.preprocessor.feature_names, show=False)
            if save_path:
                plt.savefig(save_path, bbox_inches="tight")
                plt.close()
        except Exception as exc:
            logger.warning(f"plot_summary [{target}]: {exc}")
