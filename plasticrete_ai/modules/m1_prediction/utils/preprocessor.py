"""
Preprocessor: encoding -> feature engineering -> DOI-grouped split -> impute -> scale.
Fit on train only; transform val/test with train's fitted artifacts.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.impute import KNNImputer
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.preprocessing import OrdinalEncoder, RobustScaler, StandardScaler

from modules.m1_prediction.utils.feature_engineering import add_derived_features, get_all_feature_names
from modules.m1_prediction.utils.schema import (
    ADDITIVE_TYPE, ADDITIVE_TYPE_CLASSES, DERIVED_FEATURES, INPUT_FEATURES,
    MIX_ID, PLASTIC_TYPE, PLASTIC_TYPE_CLASSES, SOURCE_DOI, STUDY_TYPE,
    TARGET_COLUMNS,
)


class Preprocessor:
    """
    Encapsulates all data preparation steps for M1.
    fit() operates on training split only.
    transform_input() is used at inference time.
    """

    def __init__(self) -> None:
        self.encoder = OrdinalEncoder(
            categories=[PLASTIC_TYPE_CLASSES, ADDITIVE_TYPE_CLASSES],
            handle_unknown="use_encoded_value",
            unknown_value=-1,
        )
        self.imputer: Optional[KNNImputer] = None
        self.input_scaler: Optional[RobustScaler] = None
        self.target_scalers: Dict[str, StandardScaler] = {}
        self.feature_names: List[str] = []
        self._fitted = False

    # ------------------------------------------------------------------
    # DOI-grouped splitting
    # ------------------------------------------------------------------

    def split(
        self,
        df: pd.DataFrame,
        test_size: float = 0.15,
        val_size: float = 0.15,
        random_seed: int = 42,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        GroupShuffleSplit on SOURCE_DOI so all rows from a paper stay together.
        Falls back to random split when too few DOI groups are available.
        Returns (train_df, val_df, test_df).
        """
        groups = df[SOURCE_DOI].fillna("unknown").values
        n_groups = len(set(groups))

        # Stage 1: carve out test set
        if n_groups >= 3:
            gss_test = GroupShuffleSplit(
                n_splits=1, test_size=test_size, random_state=random_seed
            )
            train_val_idx, test_idx = next(gss_test.split(df, groups=groups))
            train_val_df = df.iloc[train_val_idx].reset_index(drop=True)
            test_df      = df.iloc[test_idx].reset_index(drop=True)
        else:
            logger.warning(
                "Only {} DOI groups -- random split for test set".format(n_groups)
            )
            idxs = np.arange(len(df))
            tv_idx, t_idx = train_test_split(idxs, test_size=test_size, random_state=random_seed)
            train_val_df = df.iloc[tv_idx].reset_index(drop=True)
            test_df      = df.iloc[t_idx].reset_index(drop=True)

        # Stage 2: carve val from train_val
        groups_tv = train_val_df[SOURCE_DOI].fillna("unknown").values
        n_groups_tv = len(set(groups_tv))
        rel_val = val_size / (1 - test_size)

        if n_groups_tv >= 3:
            gss_val = GroupShuffleSplit(
                n_splits=1, test_size=rel_val, random_state=random_seed
            )
            train_idx, val_idx = next(gss_val.split(train_val_df, groups=groups_tv))
            train_df = train_val_df.iloc[train_idx].reset_index(drop=True)
            val_df   = train_val_df.iloc[val_idx].reset_index(drop=True)
        else:
            logger.warning(
                "Only {} DOI groups in train_val -- random split for val".format(n_groups_tv)
            )
            idxs = np.arange(len(train_val_df))
            tr_idx, v_idx = train_test_split(idxs, test_size=rel_val, random_state=random_seed)
            train_df = train_val_df.iloc[tr_idx].reset_index(drop=True)
            val_df   = train_val_df.iloc[v_idx].reset_index(drop=True)

        logger.info(
            "Split sizes -- train: {}, val: {}, test: {}".format(
                len(train_df), len(val_df), len(test_df)
            )
        )
        return train_df, val_df, test_df

    # ------------------------------------------------------------------
    # Encoding (categorical -> numeric)
    # ------------------------------------------------------------------

    def _encode(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        df = df.copy()
        cat_cols = [PLASTIC_TYPE, ADDITIVE_TYPE]
        for col in cat_cols:
            if col not in df.columns:
                df[col] = "none"
            df[col] = df[col].fillna("none")

        cat_matrix = df[cat_cols].values
        if fit:
            self.encoder.fit(cat_matrix)
        df[cat_cols] = self.encoder.transform(cat_matrix)
        return df

    # ------------------------------------------------------------------
    # Feature matrix extraction
    # ------------------------------------------------------------------

    def _build_X(self, df: pd.DataFrame, fit: bool = False) -> np.ndarray:
        df = self._encode(df, fit=fit)
        df = add_derived_features(df)

        base_features = INPUT_FEATURES[:]
        all_features  = get_all_feature_names(base_features)
        self.feature_names = all_features

        for col in all_features:
            if col not in df.columns:
                df[col] = np.nan

        return df[all_features].values.astype(float)

    # ------------------------------------------------------------------
    # Fit + transform
    # ------------------------------------------------------------------

    def fit_transform(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray,
               np.ndarray, np.ndarray, np.ndarray]:
        """
        Returns (X_train, X_val, X_test, y_train, y_val, y_test) as ndarrays.
        NaN targets are preserved -- never imputed.
        """
        X_train_raw = self._build_X(train_df, fit=True)
        X_val_raw   = self._build_X(val_df, fit=False)
        X_test_raw  = self._build_X(test_df, fit=False)

        # Impute inputs only (KNN on training data)
        self.imputer = KNNImputer(n_neighbors=5)
        X_train = self.imputer.fit_transform(X_train_raw)
        X_val   = self.imputer.transform(X_val_raw)
        X_test  = self.imputer.transform(X_test_raw)

        # Scale inputs with RobustScaler fitted on train
        self.input_scaler = RobustScaler()
        X_train = self.input_scaler.fit_transform(X_train)
        X_val   = self.input_scaler.transform(X_val)
        X_test  = self.input_scaler.transform(X_test)

        # Extract targets (NaN preserved)
        y_train = self._extract_targets(train_df)
        y_val   = self._extract_targets(val_df)
        y_test  = self._extract_targets(test_df)

        # Scale targets per-column (StandardScaler fitted on train non-NaN)
        self.target_scalers = {}
        for i, col in enumerate(TARGET_COLUMNS):
            scaler = StandardScaler()
            col_train = y_train[:, i]
            valid_mask = ~np.isnan(col_train)
            if valid_mask.sum() > 1:
                scaler.fit(col_train[valid_mask].reshape(-1, 1))
                for arr in [y_train, y_val, y_test]:
                    valid = ~np.isnan(arr[:, i])
                    arr[valid, i] = scaler.transform(arr[valid, i].reshape(-1, 1)).ravel()
            self.target_scalers[col] = scaler

        self._fitted = True
        return X_train, X_val, X_test, y_train, y_val, y_test

    def _extract_targets(self, df: pd.DataFrame) -> np.ndarray:
        y = np.full((len(df), len(TARGET_COLUMNS)), np.nan)
        for i, col in enumerate(TARGET_COLUMNS):
            if col in df.columns:
                y[:, i] = pd.to_numeric(df[col], errors="coerce").values
        return y

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def transform_df(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Transform a DataFrame using already-fitted scalers (no re-fit).
        Returns (X_scaled, y) where y NaN targets are preserved.
        Used by trainer for pretrain/finetune sub-splits.
        """
        X_raw = self._build_X(df, fit=False)
        X_imp = self.imputer.transform(X_raw)
        X     = self.input_scaler.transform(X_imp)
        y     = self._extract_targets(df)
        # Scale targets with fitted scalers
        for i, col in enumerate(TARGET_COLUMNS):
            if col in self.target_scalers:
                scaler = self.target_scalers[col]
                valid = ~np.isnan(y[:, i])
                if valid.any() and hasattr(scaler, "scale_") and scaler.scale_ is not None:
                    y[valid, i] = scaler.transform(y[valid, i].reshape(-1, 1)).ravel()
        return X, y

    def transform_input(self, input_dict: dict) -> np.ndarray:
        """Convert a single inference-time input dict -> scaled feature vector (1, n_features)."""
        df = pd.DataFrame([input_dict])
        X_raw = self._build_X(df, fit=False)
        X_imp = self.imputer.transform(X_raw)
        return self.input_scaler.transform(X_imp)

    def inverse_transform_targets(self, y_scaled: np.ndarray) -> np.ndarray:
        """Convert scaled model output back to original units."""
        y = y_scaled.copy()
        for i, col in enumerate(TARGET_COLUMNS):
            if col in self.target_scalers:
                scaler = self.target_scalers[col]
                valid = ~np.isnan(y[:, i])
                if valid.any() and hasattr(scaler, "scale_") and scaler.scale_ is not None:
                    y[valid, i] = scaler.inverse_transform(y[valid, i].reshape(-1, 1)).ravel()
        return y

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        artifact = {
            "encoder":        self.encoder,
            "imputer":        self.imputer,
            "input_scaler":   self.input_scaler,
            "target_scalers": self.target_scalers,
            "feature_names":  self.feature_names,
        }
        joblib.dump(artifact, path / "preprocessor.joblib")
        logger.info("Preprocessor saved -> {}".format(path / "preprocessor.joblib"))

    @classmethod
    def load(cls, path: str | Path) -> "Preprocessor":
        path = Path(path)
        artifact = joblib.load(path / "preprocessor.joblib")
        obj = cls()
        obj.encoder        = artifact["encoder"]
        obj.imputer        = artifact["imputer"]
        obj.input_scaler   = artifact["input_scaler"]
        obj.target_scalers = artifact["target_scalers"]
        obj.feature_names  = artifact["feature_names"]
        obj._fitted        = True
        return obj
