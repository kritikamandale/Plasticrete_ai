"""
XGBoost multi-output regressor: one XGBRegressor per target, with NaN masking.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from loguru import logger

from modules.m1_prediction.utils.schema import MIN_COVERAGE_ROWS, TARGET_COLUMNS

try:
    import xgboost as xgb
except ImportError:
    xgb = None  # type: ignore

try:
    import torch as _torch
    _CUDA_AVAILABLE = _torch.cuda.is_available()
except ImportError:
    _CUDA_AVAILABLE = False


class XGBoostMultiOutput:
    """One XGBRegressor per target, trained only on rows where that target is non-NaN."""

    DEFAULT_PARAMS = dict(
        n_estimators=1000,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        early_stopping_rounds=50,
        tree_method="hist",
        device="cpu",
        eval_metric="rmse",
    )

    def __init__(self, config: Optional[dict] = None) -> None:
        cfg = (config or {}).get("xgboost", {})
        params = {**self.DEFAULT_PARAMS}
        for k in ("n_estimators", "max_depth", "learning_rate", "subsample",
                  "colsample_bytree", "min_child_weight", "gamma", "reg_alpha",
                  "reg_lambda", "early_stopping_rounds", "tree_method"):
            if k in cfg:
                params[k] = cfg[k]

        if _CUDA_AVAILABLE:
            params["device"] = "cuda"

        self.params = params
        self.models: Dict[str, "xgb.XGBRegressor"] = {}
        self.low_coverage_targets: List[str] = []
        self._feature_names: List[str] = []

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        feature_names: Optional[List[str]] = None,
        tune: bool = False,
    ) -> None:
        if xgb is None:
            raise ImportError("xgboost is not installed.")

        if feature_names:
            self._feature_names = feature_names

        for i, target in enumerate(TARGET_COLUMNS):
            train_mask = ~np.isnan(y_train[:, i])
            val_mask   = ~np.isnan(y_val[:, i])

            n_train = train_mask.sum()
            if n_train < MIN_COVERAGE_ROWS:
                logger.warning(f"XGB: skipping {target} â€” only {n_train} training rows (min={MIN_COVERAGE_ROWS})")
                self.low_coverage_targets.append(target)
                continue

            Xt = X_train[train_mask]
            yt = y_train[train_mask, i]
            Xv = X_val[val_mask] if val_mask.any() else X_val[:1]
            yv = y_val[val_mask, i] if val_mask.any() else y_val[:1, i]

            if tune:
                best_params = self._optuna_tune(Xt, yt, i, target)
                fit_params = {**self.params, **best_params}
            else:
                fit_params = self.params.copy()

            model = xgb.XGBRegressor(**fit_params)
            model.fit(
                Xt, yt,
                eval_set=[(Xv, yv)],
                verbose=False,
            )
            self.models[target] = model
            logger.info(f"XGB {target}: trained on {n_train} rows, best_iteration={model.best_iteration}")

    def _optuna_tune(self, X: np.ndarray, y: np.ndarray, col_idx: int, target: str) -> dict:
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        def objective(trial: "optuna.Trial") -> float:
            import xgboost as xgb_inner
            from sklearn.model_selection import cross_val_score
            params = dict(
                n_estimators=trial.suggest_int("n_estimators", 200, 1000),
                max_depth=trial.suggest_int("max_depth", 3, 9),
                learning_rate=trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                subsample=trial.suggest_float("subsample", 0.6, 1.0),
                colsample_bytree=trial.suggest_float("colsample_bytree", 0.5, 1.0),
                min_child_weight=trial.suggest_int("min_child_weight", 1, 10),
                reg_alpha=trial.suggest_float("reg_alpha", 1e-4, 10.0, log=True),
                reg_lambda=trial.suggest_float("reg_lambda", 1e-4, 10.0, log=True),
                tree_method="hist",
                eval_metric="rmse",
            )
            m = xgb_inner.XGBRegressor(**params)
            scores = cross_val_score(m, X, y, cv=5, scoring="neg_root_mean_squared_error")
            return -scores.mean()

        study = optuna.create_study(direction="minimize")
        n_trials = 100
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        logger.info(f"Optuna [{target}]: best RMSE={study.best_value:.4f}, params={study.best_params}")
        return study.best_params

    def predict(self, X: np.ndarray) -> np.ndarray:
        out = np.full((len(X), len(TARGET_COLUMNS)), np.nan)
        for i, target in enumerate(TARGET_COLUMNS):
            if target in self.models:
                out[:, i] = self.models[target].predict(X)
        return out

    def get_feature_importances(self) -> Dict[str, np.ndarray]:
        return {
            t: m.feature_importances_
            for t, m in self.models.items()
        }

    def save(self, save_dir: str | Path) -> None:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        for target, model in self.models.items():
            model.save_model(str(save_dir / f"xgb_{target}.json"))
        import joblib
        joblib.dump(
            {"low_coverage_targets": self.low_coverage_targets,
             "feature_names": self._feature_names},
            save_dir / "xgb_meta.joblib",
        )
        logger.info(f"XGBoost models saved â†’ {save_dir}")

    @classmethod
    def load(cls, save_dir: str | Path, config: Optional[dict] = None) -> "XGBoostMultiOutput":
        if xgb is None:
            raise ImportError("xgboost is not installed.")
        save_dir = Path(save_dir)
        obj = cls(config)
        import joblib
        meta = joblib.load(save_dir / "xgb_meta.joblib")
        obj.low_coverage_targets = meta.get("low_coverage_targets", [])
        obj._feature_names       = meta.get("feature_names", [])
        for target in TARGET_COLUMNS:
            model_path = save_dir / f"xgb_{target}.json"
            if model_path.exists():
                m = xgb.XGBRegressor()
                m.load_model(str(model_path))
                obj.models[target] = m
        return obj

