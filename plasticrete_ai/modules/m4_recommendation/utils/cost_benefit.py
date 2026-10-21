"""
Cost-benefit economics calculator for M4.

Plastic kilograms and rupees come from the shared mass balance. The per-m2
yield is still the product geometry in the market table.
"""
from __future__ import annotations

from modules.m4_recommendation.utils.schema import CostBenefit
from modules.m4_recommendation.model import classifiers
from modules.shared.mass_balance import compute as compute_mass_balance
from modules.shared.mass_balance import conventional_mix


def calculate(mix_params: dict, primary_application: str) -> CostBenefit:
    """Compute plastic-concrete vs conventional mix economics."""
    balance = compute_mass_balance(mix_params)
    conventional = conventional_mix()

    try:
        yields = classifiers.market["product_area_yield"]
        yield_m2 = float(yields.get(primary_application, 1.0) or 1.0)
    except Exception:
        yield_m2 = 7.0
    if yield_m2 <= 0:
        yield_m2 = 1.0

    cost_plastic = balance["cost_inr_m3"]
    cost_conv = conventional["cost_inr_m3"]
    saving_m3 = cost_conv - cost_plastic
    saving_pct = (saving_m3 / cost_conv) * 100 if cost_conv else 0.0

    return CostBenefit(
        plastic_mix_cost_inr_m3  = round(cost_plastic, 2),
        conventional_cost_inr_m3 = round(cost_conv, 2),
        cost_saving_inr_m3       = round(saving_m3, 2),
        cost_saving_pct          = round(saving_pct, 2),
        plastic_mix_cost_inr_m2  = round(cost_plastic / yield_m2, 2),
        conventional_cost_inr_m2 = round(cost_conv / yield_m2, 2),
        cost_saving_inr_m2       = round(saving_m3 / yield_m2, 2),
        product_yield_m2_per_m3  = yield_m2,
        plastic_kg_per_m3        = balance["plastic_kg_m3"],
        additive_kg_per_m3       = balance["additive_kg_m3"],
    )
