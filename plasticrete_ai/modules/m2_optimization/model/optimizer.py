"""
Optuna-based constrained Bayesian optimisation for M2.
"""
from __future__ import annotations

from modules.m2_optimization.utils.encoding import predict
from modules.m2_optimization.utils.schema import (
    PLASTIC_TYPES, ADDITIVE_TYPES,
    CS_NORM_MAX, COST_NORM_MAX, CO2_NORM_MAX, DIV_NORM_MAX,
)


def run(constraints: dict, weights: dict, mode: str = "constrained") -> dict:
    """
    Find the optimal mix design using surrogate models and Optuna TPE sampler.

    Args:
        constraints: {plastic_type, replacement_pct_max, compressive_strength_min,
                      density_max_kgm3, cost_max_inr_per_m3}
        weights:     {compressive_strength, cost_per_m3, co2_per_m3, plastic_content_pct}
        mode:        "constrained" or "scenario"

    Returns:
        dict matching all OptimizeResponse fields.
    """
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    fixed_plastic = constraints.get("plastic_type")
    rep_max       = float(constraints.get("replacement_pct_max", 40.0))
    cs_min        = float(constraints.get("compressive_strength_min", 10.0))
    cost_max      = constraints.get("cost_max_inr_per_m3")

    w_cs   = float(weights.get("compressive_strength", 0.40))
    w_cost = float(weights.get("cost_per_m3",           0.30))
    w_co2  = float(weights.get("co2_per_m3",            0.20))
    w_div  = float(weights.get("plastic_content_pct",   0.10))

    plastic_choices = [fixed_plastic] if fixed_plastic else PLASTIC_TYPES

    def objective(trial: "optuna.Trial") -> float:
        plastic  = trial.suggest_categorical("plastic_type",  plastic_choices)
        additive = trial.suggest_categorical("additive_type", ADDITIVE_TYPES)
        rep_pct  = trial.suggest_float("replacement_pct",  0.0, rep_max)
        psize    = trial.suggest_float("particle_size_mm", 0.5, 20.0)
        wc       = trial.suggest_float("wc_ratio",         0.35, 0.65)
        add_pct  = trial.suggest_float("additive_pct",     0.0, 30.0)
        cure_t   = trial.suggest_float("curing_temp_c",    20.0, 80.0)
        cure_d   = trial.suggest_categorical("curing_days", [3, 7, 14, 28, 56, 90])

        cs, cost, co2, div = predict(plastic, additive, rep_pct, psize, wc, add_pct, cure_t, cure_d)

        if cs < cs_min:
            return 1e9
        if cost_max is not None and cost > cost_max:
            return 1e9

        n_cs   = cs   / CS_NORM_MAX
        n_cost = 1.0 - min(cost / COST_NORM_MAX, 1.0)
        n_co2  = 1.0 - min(co2  / CO2_NORM_MAX,  1.0)
        n_div  = min(div / DIV_NORM_MAX, 1.0)

        score = w_cs * n_cs + w_cost * n_cost + w_co2 * n_co2 + w_div * n_div
        return -score  # Optuna minimises

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42),
    )
    study.optimize(objective, n_trials=120, show_progress_bar=False)

    best = study.best_params
    cs, cost, co2, div = predict(
        best["plastic_type"],
        best["additive_type"],
        best["replacement_pct"],
        best["particle_size_mm"],
        best["wc_ratio"],
        best["additive_pct"],
        best["curing_temp_c"],
        best["curing_days"],
    )

    composite_score = -study.best_value if study.best_value < 1e8 else 0.0

    return {
        "best_mix": {
            "replacement_pct":  round(best["replacement_pct"], 3),
            "particle_size_mm": round(best["particle_size_mm"], 3),
            "wc_ratio":         round(best["wc_ratio"], 3),
            "additive_pct":     round(best["additive_pct"], 3),
            "curing_temp_c":    round(best["curing_temp_c"], 1),
            "curing_days":      float(best["curing_days"]),
        },
        "predicted_cs_mpa":                  round(cs,   3),
        "predicted_cost_inr_m3":             round(cost, 2),
        "predicted_co2_kgco2e_m3":           round(co2,  3),
        "predicted_plastic_diversion_kg_m3": round(div,  3),
        "composite_score":                   round(composite_score, 6),
        "mode":                              mode,
    }
