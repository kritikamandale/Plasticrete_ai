"""
Feature encoding and surrogate prediction helper.
Requires surrogate models to be loaded via model.surrogate before calling.
"""
from __future__ import annotations

import numpy as np

from modules.m2_optimization.model import surrogate


def predict(
    plastic: str,
    additive: str,
    rep_pct: float,
    psize: float,
    wc: float,
    add_pct: float,
    cure_t: float,
    cure_d: int | float,
) -> tuple[float, float, float, float]:
    """Encode → scale → predict CS / cost / CO2 / plastic-diversion from surrogate models."""
    pt_enc = surrogate.le_plastic.transform([plastic])[0]
    at_enc = surrogate.le_additive.transform([additive])[0]

    X_raw    = np.array([[pt_enc, at_enc, rep_pct, psize, wc, add_pct, cure_t, float(cure_d)]])
    X_scaled = surrogate.scaler_X.transform(X_raw)

    cs_s   = surrogate.xgb_cs.predict(X_scaled)[0]
    cost_s = surrogate.xgb_cost.predict(X_scaled)[0]
    co2_s  = surrogate.xgb_co2.predict(X_scaled)[0]
    div_s  = surrogate.xgb_div.predict(X_scaled)[0]

    cs   = float(surrogate.scaler_cs.inverse_transform([[cs_s]])[0][0])
    cost = float(surrogate.scaler_cost.inverse_transform([[cost_s]])[0][0])
    co2  = float(surrogate.scaler_co2.inverse_transform([[co2_s]])[0][0])
    div  = float(surrogate.scaler_div.inverse_transform([[div_s]])[0][0])
    return cs, cost, co2, div
