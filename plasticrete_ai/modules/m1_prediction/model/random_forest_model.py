"""
Random Forest multi-output: one RF per target, OOB score, uncertainty via tree variance.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
from loguru import logger
from sklearn.ensemble import RandomForestRegressor

from modules.m1_prediction.utils.schema import MIN_COVERAGE_ROWS, TARGET_COLUMNS


class RandomForestMultiOutput:
    """One RandomForestRegressor per target, with NaN masking and uncertainty output."""

    def __init__(self, config: Optional[dict] = None) -> None:
        cfg = (config or {}).get("random_forest", {})
        self.n_estimators     = cfg.get("n_estimators", 500)
        self.max_features     = cfg.get("max_features", "sqrt")
        self.min_samples_split = cfg.get("min_samples_split", 4)
        self.min_samples_leaf  = cfg.get("min_samples_leaf", 2)

        self.models: Dict[str, RandomForestRegressor] = {}
        self.low_coverage_targets: List[str] = []
        self._feature_names: List[str] = []

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        feature_names: Optional[List[str]] = None,
    ) -> None:
        if feature_names:
            self._feature_names = feature_names

        for i, target in enumerate(TARGET_COLUMNS):
            mask = ~np.isnan(y_train[:, i])
            n = mask.sum()
            if n < MIN_COVERAGE_ROWS:
                logger.warning(f"RF: skipping {target} â€” only {n} rows (min={MIN_COVERAGE_ROWS})")
                self.low_coverage_targets.append(target)
                continue

            model = RandomForestRegressor(
                n_estimators=self.n_estimators,
                max_features=self.max_features,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
                oob_score=True,
                bootstrap=True,
                n_jobs=-1,
                random_state=42,
            )
            model.fit(X_train[mask], y_train[mask, i])
            self.models[target] = model
            logger.info(f"RF {target}: trained on {n} rows, OOB RÂ²={model.oob_score_:.4f}")

    def predict(self, X: np.ndarray) -> np.ndarray:
        out = np.full((len(X), len(TARGET_COLUMNS)), np.nan)
        for i, target in enumerate(TARGET_COLUMNS):
            if target in self.models:
                out[:, i] = self.models[target].predict(X)
        return out

    def predict_with_std(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Returns (mean, std) from individual tree predictions."""
        mean = np.full((len(X), len(TARGET_COLUMNS)), np.nan)
        std  = np.full((len(X), len(TARGET_COLUMNS)), np.nan)
        for i, target in enumerate(TARGET_COLUMNS):
            if target not in self.models:
                continue
            model = self.models[target]
            # Stack predictions from each tree: shape (n_estimators, n_samples)
            tree_preds = np.stack([tree.predict(X) for tree in model.estimators_])
            mean[:, i] = tree_preds.mean(axis=0)
            std[:, i]  = tree_preds.std(axis=0)
        return mean, std

    def save(self, save_dir: str | Path) -> None:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "models": self.models,
                "low_coverage_targets": self.low_coverage_targets,
                "feature_names": self._feature_names,
                "n_estimators": self.n_estimators,
            },
            save_dir / "rf_models.joblib",
        )
        logger.info(f"RF models saved â†’ {save_dir / 'rf_models.joblib'}")

    @classmethod
    def load(cls, save_dir: str | Path, config: Optional[dict] = None) -> "RandomForestMultiOutput":
        save_dir = Path(save_dir)
        obj = cls(config)
        artifact = joblib.load(save_dir / "rf_models.joblib")
        obj.models                = artifact["models"]
        obj.low_coverage_targets  = artifact["low_coverage_targets"]
        obj._feature_names        = artifact["feature_names"]
        obj.n_estimators          = artifact["n_estimators"]
        return obj

