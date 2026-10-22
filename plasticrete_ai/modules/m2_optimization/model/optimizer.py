"""
Constrained Optuna search whose strength comes from M1 and whose
cost, CO2, and plastic mass come from the shared mass balance.
"""
from __future__ import annotations

from modules.m2_optimization.utils.schema import (
    PLASTIC_TYPES, ADDITIVE_TYPES,
    CS_NORM_MAX, COST_NORM_MAX, CO2_NORM_MAX, DIV_NORM_MAX,
)
from modules.shared.mass_balance import compute as compute_mass_balance
from modules.shared.use_class_gate import evaluate_classes

_TARGET_NAMES = (
    "compressive_strength_mpa",
    "flexural_strength_mpa",
    "split_tensile_mpa",
    "density_kgm3",
    "water_absorption_pct",
    "thermal_conductivity_wm",
    "durability_index",
)

_PASSING_GATES = ("allowed", "lab_trial")


def _m1_properties(mix: dict) -> dict:
    """Mean and 90% bounds from M1 predict_batch. Column 0 is compressive strength."""
    import modules.m1_prediction as m1

    prepared = dict(mix)
    prepared["curing_days"] = int(prepared["curing_days"])
    features = m1.get_preprocessor().transform_input(prepared)
    means, low, high = m1.predict_batch(features)
    props: dict[str, float] = {}
    ci_low: dict[str, float] = {}
    ci_high: dict[str, float] = {}
    for index, name in enumerate(_TARGET_NAMES):
        props[name] = float(means[0, index])
        ci_low[name] = float(low[0, index])
        ci_high[name] = float(high[0, index])
    props["ci_low"] = ci_low
    props["ci_high"] = ci_high
    return props


def _mix_from_trial(plastic: str, additive: str, rep: float, psize: float,
                    wc: float, add_pct: float, cure_t: float, cure_d: int) -> dict:
    return {
        "plastic_type": plastic,
        "additive_type": additive,
        "replacement_pct": float(rep),
        "particle_size_mm": float(psize),
        "wc_ratio": float(wc),
        "additive_pct": float(add_pct),
        "curing_temp_c": float(cure_t),
        "curing_days": int(cure_d),
    }


def _recipe(mix: dict, balance: dict) -> dict:
    return {
        "plastic_type": mix["plastic_type"],
        "additive_type": mix["additive_type"],
        "replacement_pct": round(mix["replacement_pct"], 3),
        "particle_size_mm": round(mix["particle_size_mm"], 3),
        "wc_ratio": round(mix["wc_ratio"], 3),
        "additive_pct": round(mix["additive_pct"], 3),
        "curing_temp_c": round(mix["curing_temp_c"], 1),
        "curing_days": int(mix["curing_days"]),
        "cement_kg_m3": balance["cement_kg_m3"],
        "sand_kg_m3": balance["sand_kg_m3"],
        "coarse_agg_kg_m3": balance["coarse_agg_kg_m3"],
        "plastic_kg_m3": balance["plastic_kg_m3"],
        "water_kg_m3": balance["water_kg_m3"],
        "additive_kg_m3": balance["additive_kg_m3"],
    }


def _point(label: str, selected: bool, record: dict) -> dict:
    return {
        "label": label,
        "selected": selected,
        "predicted_cs_mpa": round(record["cs"], 3),
        "predicted_cs_low": round(record["cs_low"], 3),
        "predicted_cs_high": round(record["ci_high"]["compressive_strength_mpa"], 3),
        "predicted_cost_inr_m3": round(record["cost"], 2),
        "predicted_co2_kgco2e_m3": round(record["co2"], 3),
        "predicted_plastic_diversion_kg_m3": round(record["div"], 3),
        "recipe": _recipe(record["mix"], record["balance"]),
    }


def _tradeoffs(feasible: list[dict], chosen: dict | None) -> list[dict]:
    pool = list(feasible)
    if chosen is not None and all(item is not chosen for item in pool):
        pool.append(chosen)
    if not pool:
        return []

    def distinct(candidates: list[dict]) -> list[dict]:
        seen = set()
        out = []
        for item in candidates:
            key = (
                item["mix"]["plastic_type"],
                item["mix"]["additive_type"],
                round(item["mix"]["replacement_pct"], 3),
                round(item["mix"]["wc_ratio"], 3),
            )
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out

    ordered = []
    if chosen is not None:
        ordered.append(("balanced", chosen))
    ordered.append(("max_strength", max(pool, key=lambda item: item["cs"])))
    ordered.append(("max_diversion", max(pool, key=lambda item: item["div"])))
    ordered.append(("min_cost", min(pool, key=lambda item: item["cost"])))

    points = []
    used = set()
    for label, record in ordered:
        ident = id(record)
        if ident in used:
            continue
        used.add(ident)
        points.append(_point(label, record is chosen, record))
        if len(points) == 3:
            break
    if chosen is not None and not any(point["selected"] for point in points):
        points[0] = _point("balanced", True, chosen)
    return points


def run(constraints: dict, weights: dict, mode: str = "constrained") -> dict:
    """
    Search mix designs with Optuna. Strength is M1. Cost, CO2, and plastic
    kilograms are the shared mass balance. Returns the weighted recipe plus
    up to three trade-off points.
    """
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    fixed_plastic = constraints.get("plastic_type")
    rep_max = float(constraints.get("replacement_pct_max", 40.0))
    cs_min = float(constraints.get("compressive_strength_min", 10.0))
    cost_max = constraints.get("cost_max_inr_per_m3")
    density_max = constraints.get("density_max_kgm3")
    diversion_min = constraints.get("plastic_diversion_min_kg_m3")
    use_class = constraints.get("use_class")

    w_cs = float(weights.get("compressive_strength", 0.40))
    w_cost = float(weights.get("cost_per_m3", 0.30))
    w_co2 = float(weights.get("co2_per_m3", 0.20))
    w_div = float(weights.get("plastic_content_pct", 0.10))

    plastic_choices = [fixed_plastic] if fixed_plastic else PLASTIC_TYPES
    feasible: list[dict] = []

    def evaluate(mix: dict) -> dict:
        balance = compute_mass_balance(mix)
        predicted = _m1_properties(mix)
        ci_low = predicted.pop("ci_low")
        ci_high = predicted.pop("ci_high")
        return {
            "mix": mix,
            "balance": balance,
            "props": predicted,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "cs": predicted["compressive_strength_mpa"],
            "cs_low": ci_low["compressive_strength_mpa"],
            "cost": balance["cost_inr_m3"],
            "co2": balance["co2_kgco2e_m3"],
            "div": balance["plastic_kg_m3"],
            "density": predicted["density_kgm3"],
        }

    def is_feasible(record: dict) -> bool:
        if record["cs"] < cs_min:
            return False
        if cost_max is not None and record["cost"] > float(cost_max):
            return False
        if density_max is not None and record["density"] > float(density_max):
            return False
        if diversion_min is not None and record["div"] < float(diversion_min):
            return False
        if use_class:
            gates = evaluate_classes(record["props"], record["ci_low"], record["ci_high"])
            match = next((gate for gate in gates if gate["id"] == use_class), None)
            if match is None or match["status"] not in _PASSING_GATES:
                return False
        return True

    def objective(trial: "optuna.Trial") -> float:
        mix = _mix_from_trial(
            trial.suggest_categorical("plastic_type", plastic_choices),
            trial.suggest_categorical("additive_type", ADDITIVE_TYPES),
            trial.suggest_float("replacement_pct", 0.0, rep_max),
            trial.suggest_float("particle_size_mm", 0.5, 20.0),
            trial.suggest_float("wc_ratio", 0.35, 0.65),
            trial.suggest_float("additive_pct", 0.0, 30.0),
            trial.suggest_float("curing_temp_c", 20.0, 80.0),
            trial.suggest_categorical("curing_days", [3, 7, 14, 28, 56, 90]),
        )
        record = evaluate(mix)
        if not is_feasible(record):
            return 1e9

        n_cs = record["cs"] / CS_NORM_MAX
        n_cost = 1.0 - min(record["cost"] / COST_NORM_MAX, 1.0)
        n_co2 = 1.0 - min(max(record["co2"], 0.0) / CO2_NORM_MAX, 1.0)
        n_div = min(record["div"] / DIV_NORM_MAX, 1.0)
        score = w_cs * n_cs + w_cost * n_cost + w_co2 * n_co2 + w_div * n_div
        record["score"] = score
        feasible.append(record)
        return -score

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42),
    )
    study.optimize(objective, n_trials=80, show_progress_bar=False)

    best_params = study.best_params
    best_mix = _mix_from_trial(
        best_params["plastic_type"],
        best_params["additive_type"],
        best_params["replacement_pct"],
        best_params["particle_size_mm"],
        best_params["wc_ratio"],
        best_params["additive_pct"],
        best_params["curing_temp_c"],
        best_params["curing_days"],
    )
    chosen = next((item for item in reversed(feasible) if item["score"] == -study.best_value), None)
    if chosen is None and feasible:
        chosen = max(feasible, key=lambda item: item["score"])
    reported = chosen if chosen is not None else evaluate(best_mix)
    feasible_flag = chosen is not None and study.best_value < 1e8
    composite = round(-study.best_value, 6) if feasible_flag else 0.0

    return {
        "best_mix": _recipe(reported["mix"], reported["balance"]),
        "predicted_cs_mpa": round(reported["cs"], 3),
        "predicted_cs_low": round(reported["cs_low"], 3),
        "predicted_cs_high": round(reported["ci_high"]["compressive_strength_mpa"], 3),
        "predicted_cost_inr_m3": round(reported["cost"], 2),
        "predicted_co2_kgco2e_m3": round(reported["co2"], 3),
        "predicted_plastic_diversion_kg_m3": round(reported["div"], 3),
        "composite_score": composite,
        "mode": mode,
        "feasible": feasible_flag,
        "prediction_source": "m1",
        "mass_balance": reported["balance"],
        "tradeoff_points": _tradeoffs(feasible, chosen if feasible_flag else None),
        "use_class": use_class,
    }
