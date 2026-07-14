"""
LIME explainer for local linear attributions.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
from loguru import logger

from modules.m1_prediction.utils.schema import TARGET_COLUMNS

try:
    import lime.lime_tabular
    _LIME_AVAILABLE = True
except ImportError:
    _LIME_AVAILABLE = False


class LIMEExplainer:
    def __init__(self, config, ensemble, preprocessor) -> None:
        self.config       = config
        self.ensemble     = ensemble
        self.preprocessor = preprocessor
        self._explainers: Dict[str, "lime.lime_tabular.LimeTabularExplainer"] = {}
        self._X_train: Optional[np.ndarray] = None

    def fit(self, X_train: np.ndarray) -> None:
        if not _LIME_AVAILABLE:
            logger.warning("lime not installed — LIME explanations disabled")
            return
        self._X_train = X_train
        feature_names = self.preprocessor.feature_names or [f"f{i}" for i in range(X_train.shape[1])]

        for i, target in enumerate(TARGET_COLUMNS):
            def _make_predict_fn(col_idx: int):
                def _fn(X: np.ndarray) -> np.ndarray:
                    means, _, _ = self.ensemble.predict_batch(X)
                    return means[:, col_idx]
                return _fn

            try:
                exp = lime.lime_tabular.LimeTabularExplainer(
                    training_data=X_train,
                    feature_names=feature_names,
                    mode="regression",
                    random_state=42,
                )
                self._explainers[target] = (exp, _make_predict_fn(i))
            except Exception as exc:
                logger.warning(f"LIME fit [{target}]: {exc}")

        logger.info("LIMEExplainer fitted")

    def explain_prediction(self, X_instance: np.ndarray, target: str) -> Dict[str, float]:
        if target not in self._explainers:
            return {}
        cfg = (self.config or {}).get("explainability", {}).get("lime", {})
        n_samples = cfg.get("n_samples", 1000)
        exp_obj, predict_fn = self._explainers[target]
        try:
            explanation = exp_obj.explain_instance(
                data_row=X_instance[0],
                predict_fn=predict_fn,
                num_samples=n_samples,
            )
            return dict(explanation.as_list())
        except Exception as exc:
            logger.warning(f"LIME explain [{target}]: {exc}")
            return {}

    def explain_contrastive(
        self, X_instance: np.ndarray, target: str, threshold: float
    ) -> List[dict]:
        """
        If predicted < threshold, identify top-3 single-parameter changes.
        Returns list of {feature, change_direction, estimated_gain}.
        """
        attrs = self.explain_prediction(X_instance, target)
        if not attrs:
            return []
        feat_names = self.preprocessor.feature_names or []
        neg_attrs  = [(f, v) for f, v in attrs.items() if v < 0]
        neg_attrs.sort(key=lambda x: x[1])
        results = []
        for feat, val in neg_attrs[:3]:
            results.append({
                "feature":         feat,
                "change_direction": "reduce",
                "estimated_gain_mpa": abs(val),
                "suggestion": (
                    f"Reduce '{feat}' to recover ≈{abs(val):.2f} MPa toward threshold {threshold}"
                ),
            })
        return results
