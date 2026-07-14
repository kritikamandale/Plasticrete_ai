"""
Cost-benefit economics calculator for M4.
"""
from __future__ import annotations

from modules.m4_recommendation.utils.schema import CostBenefit
from modules.m4_recommendation.model import classifiers

_PLASTIC_DENSITY = {"PET": 1380, "HDPE": 960, "LDPE": 920, "PVC": 1400, "PP": 905, "Mixed": 1100}


def calculate(mix_params: dict, primary_application: str) -> CostBenefit:
    """Compute plastic-concrete vs conventional mix economics."""
    prices = classifiers.market["market_prices"]
    yields = classifiers.market["product_area_yield"]
    conv   = classifiers.market["conventional_mix_m20"]

    ptype = mix_params["plastic_type"]
    atype = mix_params.get("additive_type", "none")
    rep   = mix_params["replacement_pct"] / 100.0
    rho_p = _PLASTIC_DENSITY.get(ptype, 1100)

    agg_kg        = conv["coarse_agg_20mm"]
    plastic_vol   = rep * (agg_kg / 2350)
    plastic_kg    = plastic_vol * rho_p
    agg_remaining = agg_kg - rep * agg_kg
    add_kg        = (mix_params.get("additive_pct", 0.0) / 100.0) * conv["cement_opc53"] \
                    if atype != "none" else 0.0

    cost_plastic = (
        conv["cement_opc53"] * prices["cement_opc53"]
        + conv["river_sand"] * prices["river_sand"]
        + agg_remaining      * prices["coarse_agg_20mm"]
        + conv["water"]      * prices["water"]
        + plastic_kg         * prices.get(ptype, 3.5)
        + add_kg             * prices.get(atype, 0.0)
    )
    cost_conv  = sum(conv[m] * prices[m] for m in conv)
    yield_m2   = yields.get(primary_application, 1.0)
    saving_m3  = cost_conv - cost_plastic
    saving_pct = (saving_m3 / cost_conv) * 100

    return CostBenefit(
        plastic_mix_cost_inr_m3  = round(cost_plastic, 2),
        conventional_cost_inr_m3 = round(cost_conv, 2),
        cost_saving_inr_m3       = round(saving_m3, 2),
        cost_saving_pct          = round(saving_pct, 2),
        plastic_mix_cost_inr_m2  = round(cost_plastic / yield_m2, 2),
        conventional_cost_inr_m2 = round(cost_conv / yield_m2, 2),
        cost_saving_inr_m2       = round(saving_m3 / yield_m2, 2),
        product_yield_m2_per_m3  = yield_m2,
        plastic_kg_per_m3        = round(plastic_kg, 2),
        additive_kg_per_m3       = round(add_kg, 2),
    )
