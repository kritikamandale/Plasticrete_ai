"""
Stateless feature engineering transformations applied after encoding.
All column name references use constants from schema.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from modules.m1_prediction.utils.schema import (
    CURING_DAYS, INTERACTION_PCT_AD, INTERACTION_PCT_WC, LOG_CURING_DAYS,
    LOG_PARTICLE_SIZE, PARTICLE_SIZE_MM, PLASTIC_NONE_FLAG, PLASTIC_TYPE,
    REPLACEMENT_PCT, ADDITIVE_PCT, WC_RATIO, DERIVED_FEATURES,
)


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add engineered features to df in-place (returns df for chaining).
    Operates on the raw (pre-scaled) numeric frame where plastic_type has
    already been label-encoded (0..N) or is still a string.
    """
    df = df.copy()

    psize = df[PARTICLE_SIZE_MM].values.astype(float) if PARTICLE_SIZE_MM in df.columns else np.zeros(len(df))
    df[LOG_PARTICLE_SIZE] = np.log1p(np.where(np.isnan(psize), 0.0, psize))

    days = df[CURING_DAYS].values.astype(float) if CURING_DAYS in df.columns else np.full(len(df), 28.0)
    df[LOG_CURING_DAYS] = np.log1p(np.where(np.isnan(days), 0.0, days))

    if PLASTIC_TYPE in df.columns:
        pt = df[PLASTIC_TYPE]
        if pt.dtype == object:
            df[PLASTIC_NONE_FLAG] = (pt == "None").astype(float)
        else:
            # After ordinal encoding, "None" class index is 6
            df[PLASTIC_NONE_FLAG] = (pt == 6).astype(float)
    else:
        df[PLASTIC_NONE_FLAG] = 0.0

    r  = df[REPLACEMENT_PCT].fillna(0).values.astype(float)
    wc = df[WC_RATIO].fillna(0.45).values.astype(float)
    ad = df[ADDITIVE_PCT].fillna(0).values.astype(float)

    df[INTERACTION_PCT_WC] = r * wc
    df[INTERACTION_PCT_AD] = r * ad

    return df


def get_all_feature_names(base_features: list[str]) -> list[str]:
    """Return the ordered list of all features after engineering."""
    return base_features + [f for f in DERIVED_FEATURES if f not in base_features]
