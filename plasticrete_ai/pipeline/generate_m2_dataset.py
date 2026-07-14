"""
PlastiCrete AI - Module 2 Dataset Generation Script
Generates 2,100+ row synthetic training dataset for the Intelligent Mix Optimisation Engine
"""

# ============================================================
# SECTION A - Imports and Constants
# ============================================================
import numpy as np
import pandas as pd
import json
from pathlib import Path
from scipy.stats.qmc import LatinHypercube

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

BASE_DIR = Path(__file__).parent.parent

# Load lookup files
with open(BASE_DIR / "data/external/plastic_props_m2.json") as f:
    PLASTIC_PROPS = json.load(f)

with open(BASE_DIR / "data/external/material_costs_inr.json") as f:
    MATERIAL_COSTS_INR = json.load(f)

with open(BASE_DIR / "data/external/ice_emission_factors_m2.json") as f:
    ICE_EF = json.load(f)

with open(BASE_DIR / "data/external/plastic_co2_credits.json") as f:
    PLASTIC_CO2_CREDIT = json.load(f)

PLASTIC_TYPES = ["PET", "HDPE", "LDPE", "PVC", "PP", "Mixed"]
ADDITIVE_TYPES = ["fly_ash", "silica_fume", "fibres", "none"]
CURING_DAYS_OPTIONS = [3, 7, 14, 28, 56, 90]
CURING_DAYS_WEIGHTS = [0.05, 0.15, 0.20, 0.35, 0.15, 0.10]

ADDITIVE_BOOST = {"fly_ash": 0.12, "silica_fume": 0.22, "fibres": 0.08, "none": 0.0}

# Normalisation constants for objective scoring
# (calibrated from actual physics output ranges with 150-coefficient CS formula)
CS_MAX = 60.0
COST_MIN = 4500.0
COST_MAX = 8000.0
CO2_MAX = 550.0
PLAST_MAX = 65.0

# Default weights
W_CS = 0.40
W_COST = 0.25
W_CO2 = 0.20
W_PLAST = 0.15


# ============================================================
# SECTION B - Physics Engine Functions
# ============================================================

def compute_m1_properties(row: dict, add_noise: bool = True) -> dict:
    plastic_type = row["plastic_type"]
    replacement_pct = row["replacement_pct"]
    particle_size_mm = row["particle_size_mm"]
    wc_ratio = row["wc_ratio"]
    additive_type = row["additive_type"]
    additive_pct = row["additive_pct"]
    curing_temp_c = row["curing_temp_c"]
    curing_days = row["curing_days"]

    props = PLASTIC_PROPS[plastic_type]

    # --- Compressive Strength ---
    cs_base = 150.0 * np.exp(-3.5 * wc_ratio)

    if replacement_pct <= 15:
        strength_loss = props["strength_penalty_per_pct"] * replacement_pct
    else:
        strength_loss = (
            props["strength_penalty_per_pct"] * 15
            + props["strength_penalty_per_pct"] * 1.5 * (replacement_pct - 15)
        )

    additive_factor = 1 + ADDITIVE_BOOST[additive_type] * (additive_pct / 10.0)

    particle_factor = 1.0 - 0.012 * (particle_size_mm - 2.0)
    particle_factor = np.clip(particle_factor, 0.75, 1.10)

    curing_factor = 0.65 + 0.35 * np.log(max(curing_days, 1)) / np.log(28)
    curing_factor = np.clip(curing_factor, 0.40, 1.20)

    temp_factor = 1.0 - 0.003 * max(0, curing_temp_c - 25)
    temp_factor = np.clip(temp_factor, 0.85, 1.0)

    noise_cs = np.random.normal(0, 0.8) if add_noise else 0.0
    compressive_strength_mpa = max(2.0,
        (cs_base + strength_loss) * additive_factor * particle_factor
        * curing_factor * temp_factor + noise_cs
    )
    compressive_strength_mpa = float(np.clip(compressive_strength_mpa, 2.0, 88.0))

    # --- Flexural Strength ---
    flex_ratio = 0.15 - 0.0015 * replacement_pct
    if additive_type == "fibres":
        flex_ratio += 0.04
    noise_flex = np.random.normal(0, 0.15) if add_noise else 0.0
    flexural_strength_mpa = float(np.clip(
        max(0.5, compressive_strength_mpa * flex_ratio + noise_flex), 0.5, 14.0
    ))

    # --- Split Tensile Strength ---
    split_ratio = 0.10 - 0.0010 * replacement_pct
    if additive_type == "fibres":
        split_ratio += 0.02
    noise_split = np.random.normal(0, 0.10) if add_noise else 0.0
    split_tensile_mpa = float(np.clip(
        max(0.3, compressive_strength_mpa * split_ratio + noise_split), 0.3, 9.5
    ))

    # --- Density ---
    rho_concrete = 2400.0
    rho_plastic = props["density_kg_m3"]
    rho_aggregate = 2650.0
    noise_den = np.random.normal(0, 15) if add_noise else 0.0
    density_kgm3 = float(np.clip(
        max(1100.0, rho_concrete - (replacement_pct / 100.0) * (rho_aggregate - rho_plastic) + noise_den),
        1100.0, 2600.0
    ))

    # --- Water Absorption ---
    wa_base = props["water_absorption_base"]
    additive_reduction = (additive_pct * 0.05 if additive_type in ["fly_ash", "silica_fume"] else 0)
    noise_wa = np.random.normal(0, 0.3) if add_noise else 0.0
    water_absorption_pct = float(np.clip(
        max(0.5, 3.0 + (replacement_pct / 10.0) * 1.8 + wa_base - additive_reduction + noise_wa),
        0.5, 22.0
    ))

    # --- Thermal Conductivity ---
    tc_plain = 1.75
    tc_effect = props["thermal_effect"]
    noise_tc = np.random.normal(0, 0.05) if add_noise else 0.0
    thermal_conductivity_wm = float(np.clip(
        max(0.15, tc_plain + tc_effect * replacement_pct + noise_tc),
        0.15, 2.40
    ))

    # --- Durability Index ---
    durability_raw = (
        0.40 * (compressive_strength_mpa / 60.0)
        + 0.25 * (1 - water_absorption_pct / 20.0)
        + 0.20 * (curing_days / 90.0)
        + 0.15 * (1 - replacement_pct / 40.0)
    )
    durability_index = float(np.clip(durability_raw * 100, 0, 100))

    return {
        "compressive_strength_mpa": compressive_strength_mpa,
        "flexural_strength_mpa": flexural_strength_mpa,
        "split_tensile_mpa": split_tensile_mpa,
        "density_kgm3": density_kgm3,
        "water_absorption_pct": water_absorption_pct,
        "thermal_conductivity_wm": thermal_conductivity_wm,
        "durability_index": durability_index,
    }


def compute_mix_quantities(row: dict) -> dict:
    plastic_type = row["plastic_type"]
    replacement_pct = row["replacement_pct"]
    wc_ratio = row["wc_ratio"]
    additive_pct = row["additive_pct"]

    props = PLASTIC_PROPS[plastic_type]

    cement_kg = 350.0 / (1 + 0.2 * replacement_pct / 10)
    water_kg = cement_kg * wc_ratio
    fine_agg_kg = 700.0 - (replacement_pct / 100.0) * 300.0
    coarse_agg_kg = 1100.0
    plastic_kg = (replacement_pct / 100.0) * 300.0 * props["density_kg_m3"] / 2650.0
    additive_kg = (additive_pct / 100.0) * cement_kg

    return {
        "cement_kg": cement_kg,
        "water_kg": water_kg,
        "fine_agg_kg": fine_agg_kg,
        "coarse_agg_kg": coarse_agg_kg,
        "plastic_kg": plastic_kg,
        "additive_kg": additive_kg,
    }


def compute_cost(row: dict, mix: dict) -> dict:
    plastic_type = row["plastic_type"]
    additive_type = row["additive_type"]

    props = PLASTIC_PROPS[plastic_type]

    plastic_cost = mix["plastic_kg"] * props["cost_rs_per_kg"]
    additive_cost = 0.0
    if additive_type != "none":
        additive_cost = mix["additive_kg"] * MATERIAL_COSTS_INR[additive_type]

    cement_cost = mix["cement_kg"] * 7.0
    aggregate_cost = mix["water_kg"] * 0.10 + mix["fine_agg_kg"] * 1.50 + mix["coarse_agg_kg"] * 1.20

    cost_inr_per_m3 = cement_cost + aggregate_cost + plastic_cost + additive_cost + 50.0

    return {
        "cost_inr_per_m3": float(cost_inr_per_m3),
        "cement_cost_inr": float(cement_cost),
        "aggregate_cost_inr": float(aggregate_cost),
        "plastic_cost_inr": float(plastic_cost),
        "additive_cost_inr": float(additive_cost),
    }


def compute_co2(row: dict, mix: dict) -> dict:
    plastic_type = row["plastic_type"]
    additive_type = row["additive_type"]

    co2_from_cement = mix["cement_kg"] * 0.830
    co2_from_aggregates = mix["fine_agg_kg"] * 0.005 + mix["coarse_agg_kg"] * 0.007
    additive_ef = ICE_EF.get(additive_type, 0.0)
    co2_from_additive = mix["additive_kg"] * additive_ef
    transport_mass = mix["cement_kg"] + mix["fine_agg_kg"] + mix["coarse_agg_kg"]
    co2_transport = transport_mass * 0.025
    plastic_credit = mix["plastic_kg"] * PLASTIC_CO2_CREDIT[plastic_type]

    co2_kgco2e_per_m3 = co2_from_cement + co2_from_aggregates + co2_from_additive + co2_transport + plastic_credit

    return {
        "co2_kgco2e_per_m3": float(co2_kgco2e_per_m3),
        "co2_from_cement_kgco2e": float(co2_from_cement),
        "co2_from_aggregates_kgco2e": float(co2_from_aggregates),
        "co2_from_additive_kgco2e": float(co2_from_additive),
        "co2_transport_kgco2e": float(co2_transport),
        "co2_plastic_credit_kgco2e": float(plastic_credit),
    }


def compute_composite_score(cs: float, cost: float, co2: float, plastic_kg: float,
                             w_cs: float = W_CS, w_cost: float = W_COST,
                             w_co2: float = W_CO2, w_plast: float = W_PLAST) -> float:
    cs_norm = cs / CS_MAX
    cost_norm = 1.0 - (cost - COST_MIN) / (COST_MAX - COST_MIN)
    co2_norm = 1.0 - co2 / CO2_MAX
    plast_norm = plastic_kg / PLAST_MAX

    score = w_cs * cs_norm + w_cost * cost_norm + w_co2 * co2_norm + w_plast * plast_norm
    return float(np.clip(score, 0.0, 1.0))


def compute_feasibility(m1_props: dict, co2: float) -> bool:
    return bool(
        m1_props["compressive_strength_mpa"] >= 10.0
        and m1_props["density_kgm3"] >= 1200.0
        and m1_props["water_absorption_pct"] <= 15.0
        and co2 <= 450.0
    )


def compute_cs_for_row(row: dict) -> float:
    plastic_type = row["plastic_type"]
    replacement_pct = row["replacement_pct"]
    particle_size_mm = row["particle_size_mm"]
    wc_ratio = row["wc_ratio"]
    additive_type = row["additive_type"]
    additive_pct = row["additive_pct"]
    curing_temp_c = row["curing_temp_c"]
    curing_days = row["curing_days"]

    props = PLASTIC_PROPS[plastic_type]
    cs_base = 150.0 * np.exp(-3.5 * wc_ratio)

    if replacement_pct <= 15:
        strength_loss = props["strength_penalty_per_pct"] * replacement_pct
    else:
        strength_loss = (
            props["strength_penalty_per_pct"] * 15
            + props["strength_penalty_per_pct"] * 1.5 * (replacement_pct - 15)
        )

    additive_factor = 1 + ADDITIVE_BOOST[additive_type] * (additive_pct / 10.0)
    particle_factor = np.clip(1.0 - 0.012 * (particle_size_mm - 2.0), 0.75, 1.10)
    curing_factor = np.clip(0.65 + 0.35 * np.log(max(curing_days, 1)) / np.log(28), 0.40, 1.20)
    temp_factor = np.clip(1.0 - 0.003 * max(0, curing_temp_c - 25), 0.85, 1.0)

    cs = float(np.clip(
        max(2.0, (cs_base + strength_loss) * additive_factor * particle_factor * curing_factor * temp_factor),
        2.0, 88.0
    ))
    return cs


def compute_sensitivity(row: dict) -> dict:
    continuous_inputs = {
        "replacement_pct":  (0.0, 40.0),
        "particle_size_mm": (0.5, 20.0),
        "wc_ratio":         (0.35, 0.65),
        "additive_pct":     (0.0, 30.0),
        "curing_temp_c":    (20.0, 80.0),
    }

    base_cs = compute_cs_for_row(row)
    deltas = {}
    abs_deltas_plus = {}

    for inp, (lo, hi) in continuous_inputs.items():
        val = row[inp]
        plus_val = float(np.clip(val * 1.10, lo, hi))
        minus_val = float(np.clip(val * 0.90, lo, hi))

        row_plus = dict(row)
        row_plus[inp] = plus_val
        cs_plus = compute_cs_for_row(row_plus)

        row_minus = dict(row)
        row_minus[inp] = minus_val
        cs_minus = compute_cs_for_row(row_minus)

        deltas[f"sens_{inp}_plus10_cs_delta"] = float(cs_plus - base_cs)
        deltas[f"sens_{inp}_minus10_cs_delta"] = float(cs_minus - base_cs)
        abs_deltas_plus[inp] = abs(cs_plus - base_cs)

    most_sensitive_input = max(abs_deltas_plus, key=abs_deltas_plus.get)
    risk_flag = int(any(v > 5.0 for v in abs_deltas_plus.values()))

    deltas["most_sensitive_input"] = most_sensitive_input
    deltas["risk_flag"] = risk_flag
    return deltas


def compute_scenario_scores(cs: float, cost: float, co2: float, plastic_kg: float) -> dict:
    # Strength-optimised weights
    s_str = compute_composite_score(cs, cost, co2, plastic_kg, 0.70, 0.10, 0.10, 0.10)
    # Cost-optimised weights
    s_cost = compute_composite_score(cs, cost, co2, plastic_kg, 0.20, 0.60, 0.10, 0.10)
    # Sustainability-optimised weights
    s_sust = compute_composite_score(cs, cost, co2, plastic_kg, 0.20, 0.10, 0.35, 0.35)

    scores = {"strength": s_str, "cost": s_cost, "sustainability": s_sust}
    best = max(scores, key=scores.get)

    return {
        "scenario_strength_score": s_str,
        "scenario_cost_score": s_cost,
        "scenario_sustainability_score": s_sust,
        "best_scenario": best,
    }


def build_full_row(row_dict: dict, row_type: str, pareto_rank: int = 0) -> dict:
    m1 = compute_m1_properties(row_dict)
    mix = compute_mix_quantities(row_dict)
    cost_data = compute_cost(row_dict, mix)
    co2_data = compute_co2(row_dict, mix)
    plastic_kg = mix["plastic_kg"]

    composite_score = compute_composite_score(
        m1["compressive_strength_mpa"],
        cost_data["cost_inr_per_m3"],
        co2_data["co2_kgco2e_per_m3"],
        plastic_kg
    )
    feasible = compute_feasibility(m1, co2_data["co2_kgco2e_per_m3"])
    sensitivity = compute_sensitivity(row_dict)
    scenario = compute_scenario_scores(
        m1["compressive_strength_mpa"],
        cost_data["cost_inr_per_m3"],
        co2_data["co2_kgco2e_per_m3"],
        plastic_kg
    )

    # Engineered features
    replacement_pct = row_dict["replacement_pct"]
    particle_size_mm = row_dict["particle_size_mm"]
    curing_days = row_dict["curing_days"]
    wc_ratio = row_dict["wc_ratio"]
    additive_pct = row_dict["additive_pct"]
    curing_temp_c = row_dict["curing_temp_c"]
    plastic_type = row_dict["plastic_type"]

    log_replacement_pct = float(np.log1p(replacement_pct))
    log_particle_size_mm = float(np.log(max(particle_size_mm, 0.01)))
    log_curing_days = float(np.log(max(curing_days, 1)))
    replacement_pct_x_wc = float(replacement_pct * wc_ratio)
    replacement_pct_x_add = float(replacement_pct * additive_pct)
    inv_wc_ratio = float(1.0 / wc_ratio)
    plastic_volume_fraction = float(replacement_pct / 100.0)
    plastic_density_kg_m3 = float(PLASTIC_PROPS[plastic_type]["density_kg_m3"])
    curing_maturity_index = float(curing_days * curing_temp_c)
    is_plain_concrete = int(replacement_pct == 0.0)

    full = {
        # Metadata
        "mix_id": "",  # assigned later
        "data_source": "synthetic_physics_m2",
        "row_type": row_type,
        "pareto_rank": pareto_rank,
        # Inputs
        "plastic_type": plastic_type,
        "replacement_pct": float(replacement_pct),
        "particle_size_mm": float(particle_size_mm),
        "wc_ratio": float(wc_ratio),
        "additive_type": row_dict["additive_type"],
        "additive_pct": float(additive_pct),
        "curing_temp_c": float(curing_temp_c),
        "curing_days": int(curing_days),
        # M1 outputs
        "compressive_strength_mpa": m1["compressive_strength_mpa"],
        "flexural_strength_mpa": m1["flexural_strength_mpa"],
        "split_tensile_mpa": m1["split_tensile_mpa"],
        "density_kgm3": m1["density_kgm3"],
        "water_absorption_pct": m1["water_absorption_pct"],
        "thermal_conductivity_wm": m1["thermal_conductivity_wm"],
        "durability_index": m1["durability_index"],
        # M2 objectives
        "cost_inr_per_m3": cost_data["cost_inr_per_m3"],
        "co2_kgco2e_per_m3": co2_data["co2_kgco2e_per_m3"],
        "plastic_diversion_kg_per_m3": float(plastic_kg),
        "composite_objective_score": composite_score,
        "is_feasible": feasible,
        # Cost breakdown
        "cement_kg_per_m3": float(mix["cement_kg"]),
        "water_kg_per_m3": float(mix["water_kg"]),
        "fine_agg_kg_per_m3": float(mix["fine_agg_kg"]),
        "coarse_agg_kg_per_m3": float(mix["coarse_agg_kg"]),
        "plastic_kg_per_m3": float(plastic_kg),
        "additive_kg_per_m3": float(mix["additive_kg"]),
        "cement_cost_inr": cost_data["cement_cost_inr"],
        "aggregate_cost_inr": cost_data["aggregate_cost_inr"],
        "plastic_cost_inr": cost_data["plastic_cost_inr"],
        "additive_cost_inr": cost_data["additive_cost_inr"],
        # CO2 breakdown
        "co2_from_cement_kgco2e": co2_data["co2_from_cement_kgco2e"],
        "co2_from_aggregates_kgco2e": co2_data["co2_from_aggregates_kgco2e"],
        "co2_from_additive_kgco2e": co2_data["co2_from_additive_kgco2e"],
        "co2_transport_kgco2e": co2_data["co2_transport_kgco2e"],
        "co2_plastic_credit_kgco2e": co2_data["co2_plastic_credit_kgco2e"],
        # Scenario scores
        "scenario_strength_score": scenario["scenario_strength_score"],
        "scenario_cost_score": scenario["scenario_cost_score"],
        "scenario_sustainability_score": scenario["scenario_sustainability_score"],
        "best_scenario": scenario["best_scenario"],
        # Sensitivity
        "sens_replacement_pct_plus10_cs_delta": sensitivity["sens_replacement_pct_plus10_cs_delta"],
        "sens_replacement_pct_minus10_cs_delta": sensitivity["sens_replacement_pct_minus10_cs_delta"],
        "sens_particle_size_mm_plus10_cs_delta": sensitivity["sens_particle_size_mm_plus10_cs_delta"],
        "sens_particle_size_mm_minus10_cs_delta": sensitivity["sens_particle_size_mm_minus10_cs_delta"],
        "sens_wc_ratio_plus10_cs_delta": sensitivity["sens_wc_ratio_plus10_cs_delta"],
        "sens_wc_ratio_minus10_cs_delta": sensitivity["sens_wc_ratio_minus10_cs_delta"],
        "sens_additive_pct_plus10_cs_delta": sensitivity["sens_additive_pct_plus10_cs_delta"],
        "sens_additive_pct_minus10_cs_delta": sensitivity["sens_additive_pct_minus10_cs_delta"],
        "sens_curing_temp_c_plus10_cs_delta": sensitivity["sens_curing_temp_c_plus10_cs_delta"],
        "sens_curing_temp_c_minus10_cs_delta": sensitivity["sens_curing_temp_c_minus10_cs_delta"],
        "most_sensitive_input": sensitivity["most_sensitive_input"],
        "risk_flag": sensitivity["risk_flag"],
        # Engineered features
        "log_replacement_pct": log_replacement_pct,
        "log_particle_size_mm": log_particle_size_mm,
        "log_curing_days": log_curing_days,
        "replacement_pct_x_wc": replacement_pct_x_wc,
        "replacement_pct_x_add": replacement_pct_x_add,
        "inv_wc_ratio": inv_wc_ratio,
        "plastic_volume_fraction": plastic_volume_fraction,
        "plastic_density_kg_m3": plastic_density_kg_m3,
        "curing_maturity_index": curing_maturity_index,
        "is_plain_concrete": is_plain_concrete,
    }
    return full


# ============================================================
# SECTION C - Row Generation Functions
# ============================================================

def generate_lhs_batch(n: int = 900) -> pd.DataFrame:
    rng_lhs = np.random.default_rng(RANDOM_SEED)
    sampler = LatinHypercube(d=5, seed=RANDOM_SEED)
    samples = sampler.random(n=n)

    ranges = [
        (0.0, 40.0),   # replacement_pct
        (0.5, 20.0),   # particle_size_mm
        (0.35, 0.65),  # wc_ratio
        (0.0, 30.0),   # additive_pct
        (20.0, 80.0),  # curing_temp_c
    ]

    scaled = np.zeros_like(samples)
    for i, (lo, hi) in enumerate(ranges):
        scaled[:, i] = samples[:, i] * (hi - lo) + lo

    # Plastic type: ensure ~150 rows each
    plastic_types_arr = []
    per_type = n // len(PLASTIC_TYPES)
    for pt in PLASTIC_TYPES:
        plastic_types_arr.extend([pt] * per_type)
    remainder = n - len(plastic_types_arr)
    plastic_types_arr.extend(np.random.choice(PLASTIC_TYPES, remainder).tolist())
    np.random.shuffle(plastic_types_arr)

    # Additive type
    add_probs = [0.30, 0.25, 0.15, 0.30]
    additive_types_arr = np.random.choice(ADDITIVE_TYPES, n, p=add_probs).tolist()

    # Curing days
    curing_days_arr = np.random.choice(CURING_DAYS_OPTIONS, n, p=CURING_DAYS_WEIGHTS).tolist()

    rows = []
    for i in range(n):
        row_dict = {
            "plastic_type": plastic_types_arr[i],
            "replacement_pct": float(scaled[i, 0]),
            "particle_size_mm": float(scaled[i, 1]),
            "wc_ratio": float(scaled[i, 2]),
            "additive_type": additive_types_arr[i],
            "additive_pct": float(scaled[i, 3]),
            "curing_temp_c": float(scaled[i, 4]),
            "curing_days": int(curing_days_arr[i]),
        }
        rows.append(build_full_row(row_dict, "lhs_sample", 0))

    return pd.DataFrame(rows)


def generate_grid_batch(n: int = 600) -> pd.DataFrame:
    rows = []

    # Sub-batch 2a: Plastic type x replacement % grid (target 240)
    repl_vals = [0, 5, 10, 15, 20, 25, 30, 35, 40]
    base_combos = [(pt, rp) for pt in PLASTIC_TYPES for rp in repl_vals]  # 54 combos
    # Repeat to fill 240
    n_2a = 240
    repeated = (base_combos * ((n_2a // len(base_combos)) + 1))[:n_2a]
    for pt, rp in repeated:
        row_dict = {
            "plastic_type": pt,
            "replacement_pct": float(rp),
            "particle_size_mm": float(np.random.uniform(0.5, 20.0)),
            "wc_ratio": float(np.random.uniform(0.35, 0.65)),
            "additive_type": np.random.choice(ADDITIVE_TYPES, p=[0.30, 0.25, 0.15, 0.30]),
            "additive_pct": float(np.random.uniform(0, 30)),
            "curing_temp_c": float(np.random.uniform(20, 80)),
            "curing_days": int(np.random.choice(CURING_DAYS_OPTIONS, p=CURING_DAYS_WEIGHTS)),
        }
        rows.append(build_full_row(row_dict, "grid", 0))

    # Sub-batch 2b: wc_ratio x additive grid (120)
    wc_vals = [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65]
    add_pct_vals = [0, 5, 10, 15, 20, 25, 30]
    combos_b = [(wc, at, ap)
                for wc in wc_vals
                for at in ADDITIVE_TYPES
                for ap in [5, 15, 25]]
    n_2b = 120
    repeated_b = (combos_b * ((n_2b // len(combos_b)) + 1))[:n_2b]
    for wc, at, ap in repeated_b:
        row_dict = {
            "plastic_type": np.random.choice(PLASTIC_TYPES),
            "replacement_pct": float(np.random.uniform(0, 40)),
            "particle_size_mm": float(np.random.uniform(0.5, 20.0)),
            "wc_ratio": float(wc),
            "additive_type": at,
            "additive_pct": float(ap),
            "curing_temp_c": float(np.random.uniform(20, 80)),
            "curing_days": int(np.random.choice(CURING_DAYS_OPTIONS, p=CURING_DAYS_WEIGHTS)),
        }
        rows.append(build_full_row(row_dict, "grid", 0))

    # Sub-batch 2c: curing_days x curing_temp grid (120)
    cd_vals = [3, 7, 14, 28, 56, 90]
    ct_vals = [20, 30, 40, 50, 60, 70, 80]
    combos_c = [(cd, ct) for cd in cd_vals for ct in ct_vals]  # 42 combos
    n_2c = 120
    repeated_c = (combos_c * ((n_2c // len(combos_c)) + 1))[:n_2c]
    for cd, ct in repeated_c:
        row_dict = {
            "plastic_type": np.random.choice(PLASTIC_TYPES),
            "replacement_pct": float(np.random.uniform(0, 40)),
            "particle_size_mm": float(np.random.uniform(0.5, 20.0)),
            "wc_ratio": float(np.random.uniform(0.35, 0.65)),
            "additive_type": np.random.choice(ADDITIVE_TYPES, p=[0.30, 0.25, 0.15, 0.30]),
            "additive_pct": float(np.random.uniform(0, 30)),
            "curing_temp_c": float(ct),
            "curing_days": int(cd),
        }
        rows.append(build_full_row(row_dict, "grid", 0))

    # Sub-batch 2d: Extreme/corner cases (120)
    extreme_specs = []
    # High plastic + low wc
    for _ in range(20):
        extreme_specs.append({
            "plastic_type": np.random.choice(PLASTIC_TYPES),
            "replacement_pct": float(np.random.uniform(35, 40)),
            "particle_size_mm": float(np.random.uniform(0.5, 20.0)),
            "wc_ratio": float(np.random.uniform(0.35, 0.40)),
            "additive_type": np.random.choice(ADDITIVE_TYPES),
            "additive_pct": float(np.random.uniform(0, 30)),
            "curing_temp_c": float(np.random.uniform(20, 80)),
            "curing_days": int(np.random.choice(CURING_DAYS_OPTIONS, p=CURING_DAYS_WEIGHTS)),
        })
    # Low plastic + high additive
    for _ in range(20):
        extreme_specs.append({
            "plastic_type": np.random.choice(PLASTIC_TYPES),
            "replacement_pct": float(np.random.uniform(0, 5)),
            "particle_size_mm": float(np.random.uniform(0.5, 20.0)),
            "wc_ratio": float(np.random.uniform(0.35, 0.65)),
            "additive_type": np.random.choice(["fly_ash", "silica_fume", "fibres"]),
            "additive_pct": float(np.random.uniform(20, 30)),
            "curing_temp_c": float(np.random.uniform(20, 80)),
            "curing_days": int(np.random.choice(CURING_DAYS_OPTIONS, p=CURING_DAYS_WEIGHTS)),
        })
    # High curing days + low temp
    for _ in range(20):
        extreme_specs.append({
            "plastic_type": np.random.choice(PLASTIC_TYPES),
            "replacement_pct": float(np.random.uniform(0, 40)),
            "particle_size_mm": float(np.random.uniform(0.5, 20.0)),
            "wc_ratio": float(np.random.uniform(0.35, 0.65)),
            "additive_type": np.random.choice(ADDITIVE_TYPES),
            "additive_pct": float(np.random.uniform(0, 30)),
            "curing_temp_c": 20.0,
            "curing_days": int(np.random.choice([56, 90])),
        })
    # All plastic types at 0% replacement (baseline)
    for pt in PLASTIC_TYPES:
        for _ in range(2):
            extreme_specs.append({
                "plastic_type": pt,
                "replacement_pct": 0.0,
                "particle_size_mm": float(np.random.uniform(0.5, 20.0)),
                "wc_ratio": float(np.random.uniform(0.35, 0.65)),
                "additive_type": np.random.choice(ADDITIVE_TYPES),
                "additive_pct": float(np.random.uniform(0, 30)),
                "curing_temp_c": float(np.random.uniform(20, 80)),
                "curing_days": int(np.random.choice(CURING_DAYS_OPTIONS, p=CURING_DAYS_WEIGHTS)),
            })
    # All additive types at 0%
    for at in ADDITIVE_TYPES:
        extreme_specs.append({
            "plastic_type": np.random.choice(PLASTIC_TYPES),
            "replacement_pct": float(np.random.uniform(0, 40)),
            "particle_size_mm": float(np.random.uniform(0.5, 20.0)),
            "wc_ratio": float(np.random.uniform(0.35, 0.65)),
            "additive_type": at,
            "additive_pct": 0.0,
            "curing_temp_c": float(np.random.uniform(20, 80)),
            "curing_days": int(np.random.choice(CURING_DAYS_OPTIONS, p=CURING_DAYS_WEIGHTS)),
        })
    # PVC at high replacement
    for _ in range(10):
        extreme_specs.append({
            "plastic_type": "PVC",
            "replacement_pct": float(np.random.uniform(30, 40)),
            "particle_size_mm": float(np.random.uniform(0.5, 20.0)),
            "wc_ratio": float(np.random.uniform(0.35, 0.65)),
            "additive_type": np.random.choice(ADDITIVE_TYPES),
            "additive_pct": float(np.random.uniform(0, 30)),
            "curing_temp_c": float(np.random.uniform(20, 80)),
            "curing_days": int(np.random.choice(CURING_DAYS_OPTIONS, p=CURING_DAYS_WEIGHTS)),
        })
    # PP + silica_fume high-performance
    for _ in range(10):
        extreme_specs.append({
            "plastic_type": "PP",
            "replacement_pct": float(np.random.uniform(5, 10)),
            "particle_size_mm": float(np.random.uniform(0.5, 5.0)),
            "wc_ratio": float(np.random.uniform(0.35, 0.45)),
            "additive_type": "silica_fume",
            "additive_pct": float(np.random.uniform(10, 20)),
            "curing_temp_c": float(np.random.uniform(20, 40)),
            "curing_days": int(np.random.choice([28, 56, 90])),
        })

    # Trim or pad to exactly 120
    extreme_specs = extreme_specs[:120]
    while len(extreme_specs) < 120:
        extreme_specs.append({
            "plastic_type": np.random.choice(PLASTIC_TYPES),
            "replacement_pct": float(np.random.uniform(0, 40)),
            "particle_size_mm": float(np.random.uniform(0.5, 20.0)),
            "wc_ratio": float(np.random.uniform(0.35, 0.65)),
            "additive_type": np.random.choice(ADDITIVE_TYPES),
            "additive_pct": float(np.random.uniform(0, 30)),
            "curing_temp_c": float(np.random.uniform(20, 80)),
            "curing_days": int(np.random.choice(CURING_DAYS_OPTIONS, p=CURING_DAYS_WEIGHTS)),
        })

    for spec in extreme_specs:
        rows.append(build_full_row(spec, "grid", 0))

    return pd.DataFrame(rows)


def generate_pareto_batch(n: int = 300) -> pd.DataFrame:
    rows = []

    # a) Strength Pareto boundary (100 rows)
    for _ in range(100):
        pt = np.random.choice(["PET", "PP"])
        row_dict = {
            "plastic_type": pt,
            "replacement_pct": float(np.random.uniform(0, 10)),
            "particle_size_mm": float(np.random.uniform(0.5, 5.0)),
            "wc_ratio": float(np.random.uniform(0.35, 0.42)),
            "additive_type": "silica_fume",
            "additive_pct": float(np.random.uniform(10, 25)),
            "curing_temp_c": float(np.random.uniform(20, 40)),
            "curing_days": int(np.random.choice([28, 56, 90])),
        }
        rows.append(build_full_row(row_dict, "pareto_candidate", 0))

    # b) Cost Pareto boundary (100 rows)
    for _ in range(100):
        pt = np.random.choice(["Mixed", "PVC"])
        at = np.random.choice(["fly_ash", "none"], p=[0.6, 0.4])
        row_dict = {
            "plastic_type": pt,
            "replacement_pct": float(np.random.uniform(20, 35)),
            "particle_size_mm": float(np.random.uniform(0.5, 20.0)),
            "wc_ratio": float(np.random.uniform(0.45, 0.55)),
            "additive_type": at,
            "additive_pct": float(np.random.uniform(0, 15) if at != "none" else 0),
            "curing_temp_c": float(np.random.uniform(20, 60)),
            "curing_days": int(np.random.choice(CURING_DAYS_OPTIONS, p=CURING_DAYS_WEIGHTS)),
        }
        rows.append(build_full_row(row_dict, "pareto_candidate", 0))

    # c) Sustainability / CO2 Pareto boundary (100 rows)
    for _ in range(100):
        pt = np.random.choice(["HDPE", "PP"])
        row_dict = {
            "plastic_type": pt,
            "replacement_pct": float(np.random.uniform(25, 40)),
            "particle_size_mm": float(np.random.uniform(0.5, 20.0)),
            "wc_ratio": float(np.random.uniform(0.45, 0.60)),
            "additive_type": "fly_ash",
            "additive_pct": float(np.random.uniform(10, 20)),
            "curing_temp_c": float(np.random.uniform(20, 25)),
            "curing_days": int(np.random.choice([14, 28])),
        }
        rows.append(build_full_row(row_dict, "pareto_candidate", 0))

    df = pd.DataFrame(rows)

    # Compute Pareto ranks in [CS, cost, CO2] space
    # Maximise CS, minimise cost, minimise CO2
    cs_vals = df["compressive_strength_mpa"].values
    cost_vals = df["cost_inr_per_m3"].values
    co2_vals = df["co2_kgco2e_per_m3"].values

    pareto_ranks = np.zeros(len(df), dtype=int)
    for i in range(len(df)):
        dominated = False
        for j in range(len(df)):
            if i == j:
                continue
            # j dominates i if j is at least as good in all objectives and strictly better in at least one
            if (cs_vals[j] >= cs_vals[i] and
                    cost_vals[j] <= cost_vals[i] and
                    co2_vals[j] <= co2_vals[i] and
                    (cs_vals[j] > cs_vals[i] or cost_vals[j] < cost_vals[i] or co2_vals[j] < co2_vals[i])):
                dominated = True
                break
        if not dominated:
            pareto_ranks[i] = 1

    df["pareto_rank"] = pareto_ranks
    return df


def generate_noise_batch(base_df: pd.DataFrame, top_n: int = 100, perturbs: int = 2) -> pd.DataFrame:
    top_rows = base_df.nlargest(top_n, "composite_objective_score")

    rows = []
    for _, r in top_rows.iterrows():
        for _ in range(perturbs):
            row_dict = {
                "plastic_type": r["plastic_type"],
                "replacement_pct": float(np.clip(r["replacement_pct"] + np.random.normal(0, 1.5), 0.0, 40.0)),
                "particle_size_mm": float(np.clip(r["particle_size_mm"] + np.random.normal(0, 0.5), 0.5, 20.0)),
                "wc_ratio": float(np.clip(r["wc_ratio"] + np.random.normal(0, 0.01), 0.35, 0.65)),
                "additive_type": r["additive_type"],
                "additive_pct": float(np.clip(r["additive_pct"] + np.random.normal(0, 0.8), 0.0, 30.0)),
                "curing_temp_c": float(np.clip(r["curing_temp_c"] + np.random.normal(0, 2.0), 20.0, 80.0)),
                "curing_days": int(np.clip(r["curing_days"] + np.random.randint(-1, 2),
                                           min(CURING_DAYS_OPTIONS), max(CURING_DAYS_OPTIONS))),
            }
            rows.append(build_full_row(row_dict, "noise_augmented", 0))

    return pd.DataFrame(rows)


# ============================================================
# SECTION D - Assembly and Validation
# ============================================================

def assemble_and_validate():
    print("Generating Batch 1: LHS (900 rows)...")
    df_lhs = generate_lhs_batch(900)
    print(f"  LHS generated: {len(df_lhs)} rows")

    print("Generating Batch 2: Grid (600 rows)...")
    df_grid = generate_grid_batch(600)
    print(f"  Grid generated: {len(df_grid)} rows")

    print("Generating Batch 3: Pareto candidates (300 rows)...")
    df_pareto = generate_pareto_batch(300)
    print(f"  Pareto generated: {len(df_pareto)} rows")

    print("Generating Batch 4: Noise augmentation (300 rows)...")
    base_for_noise = pd.concat([df_lhs, df_grid, df_pareto], ignore_index=True)
    df_noise = generate_noise_batch(base_for_noise, top_n=150, perturbs=2)
    print(f"  Noise augmented: {len(df_noise)} rows")

    df = pd.concat([df_lhs, df_grid, df_pareto, df_noise], ignore_index=True)

    # Top-up: ensure every plastic type has >= 300 rows
    MIN_PER_TYPE = 300
    topup_rows = []
    for pt in PLASTIC_TYPES:
        count = (df["plastic_type"] == pt).sum()
        if count < MIN_PER_TYPE:
            needed = MIN_PER_TYPE - count
            print(f"  Top-up: generating {needed} extra rows for plastic_type={pt}")
            for _ in range(needed):
                row_dict = {
                    "plastic_type": pt,
                    "replacement_pct": float(np.random.uniform(0, 40)),
                    "particle_size_mm": float(np.random.uniform(0.5, 20.0)),
                    "wc_ratio": float(np.random.uniform(0.35, 0.65)),
                    "additive_type": np.random.choice(ADDITIVE_TYPES, p=[0.30, 0.25, 0.15, 0.30]),
                    "additive_pct": float(np.random.uniform(0, 30)),
                    "curing_temp_c": float(np.random.uniform(20, 80)),
                    "curing_days": int(np.random.choice(CURING_DAYS_OPTIONS, p=CURING_DAYS_WEIGHTS)),
                }
                topup_rows.append(build_full_row(row_dict, "lhs_sample", 0))
    if topup_rows:
        df_topup = pd.DataFrame(topup_rows)
        df = pd.concat([df, df_topup], ignore_index=True)

    # Assign mix_id
    df["mix_id"] = [f"M2_{i+1:05d}" for i in range(len(df))]

    # Define exact column order
    COLUMN_ORDER = [
        # Metadata
        "mix_id", "data_source", "row_type", "pareto_rank",
        # Inputs
        "plastic_type", "replacement_pct", "particle_size_mm", "wc_ratio",
        "additive_type", "additive_pct", "curing_temp_c", "curing_days",
        # M1 outputs
        "compressive_strength_mpa", "flexural_strength_mpa", "split_tensile_mpa",
        "density_kgm3", "water_absorption_pct", "thermal_conductivity_wm", "durability_index",
        # M2 objectives
        "cost_inr_per_m3", "co2_kgco2e_per_m3", "plastic_diversion_kg_per_m3",
        "composite_objective_score", "is_feasible",
        # Cost breakdown
        "cement_kg_per_m3", "water_kg_per_m3", "fine_agg_kg_per_m3", "coarse_agg_kg_per_m3",
        "plastic_kg_per_m3", "additive_kg_per_m3",
        "cement_cost_inr", "aggregate_cost_inr", "plastic_cost_inr", "additive_cost_inr",
        # CO2 breakdown
        "co2_from_cement_kgco2e", "co2_from_aggregates_kgco2e", "co2_from_additive_kgco2e",
        "co2_transport_kgco2e", "co2_plastic_credit_kgco2e",
        # Scenario scores
        "scenario_strength_score", "scenario_cost_score", "scenario_sustainability_score", "best_scenario",
        # Sensitivity
        "sens_replacement_pct_plus10_cs_delta", "sens_replacement_pct_minus10_cs_delta",
        "sens_particle_size_mm_plus10_cs_delta", "sens_particle_size_mm_minus10_cs_delta",
        "sens_wc_ratio_plus10_cs_delta", "sens_wc_ratio_minus10_cs_delta",
        "sens_additive_pct_plus10_cs_delta", "sens_additive_pct_minus10_cs_delta",
        "sens_curing_temp_c_plus10_cs_delta", "sens_curing_temp_c_minus10_cs_delta",
        "most_sensitive_input", "risk_flag",
        # Engineered features
        "log_replacement_pct", "log_particle_size_mm", "log_curing_days",
        "replacement_pct_x_wc", "replacement_pct_x_add", "inv_wc_ratio",
        "plastic_volume_fraction", "plastic_density_kg_m3",
        "curing_maturity_index", "is_plain_concrete",
    ]

    df = df[COLUMN_ORDER]

    # ---- MANDATORY VALIDATIONS ----
    assert len(df) >= 2100, f"FAIL: Total rows {len(df)} < 2100"
    assert len(df.columns) == 65, f"FAIL: Column count {len(df.columns)} != 65"

    primary_cols = [
        "compressive_strength_mpa", "flexural_strength_mpa", "split_tensile_mpa",
        "density_kgm3", "water_absorption_pct", "thermal_conductivity_wm", "durability_index",
        "cost_inr_per_m3", "co2_kgco2e_per_m3", "plastic_diversion_kg_per_m3",
        "composite_objective_score", "is_feasible",
    ]
    nan_count = df[primary_cols].isnull().sum().sum()
    assert nan_count == 0, f"FAIL: {nan_count} NaN values in primary columns"

    total_nan = df.isnull().sum().sum()
    assert total_nan == 0, f"FAIL: {total_nan} NaN in all columns"

    for pt in PLASTIC_TYPES:
        count = (df["plastic_type"] == pt).sum()
        assert count >= 300, f"FAIL: plastic_type={pt} has only {count} rows (need >= 300)"

    cs_scores = df["composite_objective_score"]
    assert cs_scores.min() >= 0.0 and cs_scores.max() <= 1.0, \
        f"FAIL: composite_objective_score out of [0,1]: [{cs_scores.min():.4f}, {cs_scores.max():.4f}]"

    assert df["is_feasible"].dtype == bool, f"FAIL: is_feasible dtype is {df['is_feasible'].dtype}"

    pareto_ones = (df["pareto_rank"] == 1).sum()
    assert pareto_ones >= 10, f"FAIL: Only {pareto_ones} pareto_rank=1 rows"

    assert df["mix_id"].nunique() == len(df), "FAIL: mix_id not unique"

    # Row type counts
    rt_counts = df["row_type"].value_counts()
    assert rt_counts.get("lhs_sample", 0) >= 800, f"FAIL: lhs_sample count {rt_counts.get('lhs_sample', 0)} < 800"
    assert rt_counts.get("grid", 0) >= 500, f"FAIL: grid count {rt_counts.get('grid', 0)} < 500"
    assert rt_counts.get("pareto_candidate", 0) >= 250, f"FAIL: pareto_candidate count {rt_counts.get('pareto_candidate', 0)} < 250"
    assert rt_counts.get("noise_augmented", 0) >= 250, f"FAIL: noise_augmented count {rt_counts.get('noise_augmented', 0)} < 250"

    print("\nAll mandatory validations PASSED.")

    # ---- QUALITY WARNINGS ----
    cs_mean = df["compressive_strength_mpa"].mean()
    if not (20 <= cs_mean <= 45):
        print(f"WARN: CS mean {cs_mean:.1f} outside expected [20, 45] MPa")

    feas_rate = df["is_feasible"].mean() * 100
    if not (75 <= feas_rate <= 95):
        print(f"WARN: Feasibility rate {feas_rate:.1f}% outside [75%, 95%]")

    for sc in ["strength", "cost", "sustainability"]:
        sc_count = (df["best_scenario"] == sc).sum()
        if sc_count < 100:
            print(f"WARN: best_scenario='{sc}' only {sc_count} rows (< 100)")

    risk_rate = df["risk_flag"].mean() * 100
    if not (15 <= risk_rate <= 45):
        print(f"WARN: risk_flag rate {risk_rate:.1f}% outside [15%, 45%]")

    neg_co2 = (df["co2_kgco2e_per_m3"] < 0).sum()
    if neg_co2 == 0:
        print("WARN: No negative CO2 rows found (expected some with high plastic credit)")

    return df


# ============================================================
# SECTION E - Statistics Report
# ============================================================

def print_report(df: pd.DataFrame):
    rt = df["row_type"].value_counts()
    pt = df["plastic_type"].value_counts()
    sc = df["best_scenario"].value_counts()

    bands = {
        "0-10": ((df["replacement_pct"] >= 0) & (df["replacement_pct"] <= 10)).sum(),
        "10-25": ((df["replacement_pct"] > 10) & (df["replacement_pct"] <= 25)).sum(),
        "25-40": ((df["replacement_pct"] > 25) & (df["replacement_pct"] <= 40)).sum(),
    }

    feas = df["is_feasible"].sum()
    feas_pct = feas / len(df) * 100
    pareto_ones = (df["pareto_rank"] == 1).sum()
    risk_n = df["risk_flag"].sum()
    risk_pct = risk_n / len(df) * 100

    print(f"\nTotal rows:     {len(df)}")
    print(f"Total columns:  {len(df.columns)}")
    print(f"Plastic type counts: {dict(pt)}")
    print(f"replacement_pct bands: {bands}")
    print(f"Feasible rows: {feas} ({feas_pct:.1f}%)")
    print(f"Pareto-rank=1 rows: {pareto_ones}")
    print(f"Best scenario distribution: {dict(sc)}")
    print(f"row_type distribution: {dict(rt)}")
    print(f"risk_flag = 1 rows: {risk_n} ({risk_pct:.1f}%)")

    for col in ["compressive_strength_mpa", "cost_inr_per_m3", "co2_kgco2e_per_m3",
                "plastic_diversion_kg_per_m3", "composite_objective_score"]:
        print(f"{col}: [{df[col].min():.2f}, {df[col].max():.2f}], mean={df[col].mean():.2f}")

    print(f"NaN count in primary columns: 0")


# ============================================================
# SECTION F - Save and Completion Output
# ============================================================

def main():
    out_path = BASE_DIR / "data/processed/m2_training_dataset.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = assemble_and_validate()
    print_report(df)

    df.to_csv(out_path, index=False)

    # Final completion block
    rt = df["row_type"].value_counts()
    pt = df["plastic_type"].value_counts()
    sc = df["best_scenario"].value_counts()
    feas = df["is_feasible"].sum()
    feas_pct = feas / len(df) * 100
    pareto_ones = (df["pareto_rank"] == 1).sum()
    risk_n = df["risk_flag"].sum()
    risk_pct = risk_n / len(df) * 100

    cs = df["compressive_strength_mpa"]
    flex = df["flexural_strength_mpa"]
    den = df["density_kgm3"]
    wa = df["water_absorption_pct"]
    tc = df["thermal_conductivity_wm"]
    di = df["durability_index"]
    cost = df["cost_inr_per_m3"]
    co2 = df["co2_kgco2e_per_m3"]
    plast = df["plastic_diversion_kg_per_m3"]
    obj = df["composite_objective_score"]

    str_n = sc.get("strength", 0); str_pct = str_n / len(df) * 100
    cost_n = sc.get("cost", 0); cost_pct = cost_n / len(df) * 100
    sust_n = sc.get("sustainability", 0); sust_pct = sust_n / len(df) * 100

    lines = [
        "==================================================================",
        "DONE: PlastiCrete AI - M2 Dataset Generation Complete",
        "==================================================================",
        f"Dataset:  data/processed/m2_training_dataset.csv",
        f"Rows:     {len(df)}   (target: 2,100)",
        "Columns:  65    (exact)",
        "NaN:      0",
        "",
        "Plastic coverage:",
        f"  PET:   {pt.get('PET',0)} rows    HDPE:  {pt.get('HDPE',0)} rows",
        f"  LDPE:  {pt.get('LDPE',0)} rows    PVC:   {pt.get('PVC',0)} rows",
        f"  PP:    {pt.get('PP',0)} rows    Mixed: {pt.get('Mixed',0)} rows",
        "",
        f"Feasible rows:      {feas} ({feas_pct:.1f}%)",
        f"Pareto-optimal:     {pareto_ones} rows (pareto_rank=1)",
        f"Risk-flagged mixes: {risk_n} ({risk_pct:.1f}%)",
        "",
        "M1 property ranges:",
        f"  compressive_strength_mpa:    {cs.min():.1f}-{cs.max():.1f} MPa,  mean={cs.mean():.1f}",
        f"  flexural_strength_mpa:       {flex.min():.1f}-{flex.max():.1f} MPa",
        f"  density_kgm3:                {den.min():.0f}-{den.max():.0f} kg/m3",
        f"  water_absorption_pct:        {wa.min():.1f}-{wa.max():.1f} %",
        f"  thermal_conductivity_wm:     {tc.min():.2f}-{tc.max():.2f} W/mK",
        f"  durability_index:            {di.min():.1f}-{di.max():.1f}",
        "",
        "M2 objective ranges:",
        f"  cost_inr_per_m3:             Rs.{cost.min():.0f}-Rs.{cost.max():.0f},    mean=Rs.{cost.mean():.0f}",
        f"  co2_kgco2e_per_m3:           {co2.min():.1f}-{co2.max():.1f} kg,   mean={co2.mean():.1f}",
        f"  plastic_diversion_kg_per_m3: {plast.min():.1f}-{plast.max():.1f} kg,   mean={plast.mean():.1f}",
        f"  composite_objective_score:   {obj.min():.3f}-{obj.max():.3f},       mean={obj.mean():.3f}",
        "",
        "Scenario distribution:",
        f"  strength_optimised:          {str_n} rows ({str_pct:.1f}%)",
        f"  cost_optimised:              {cost_n} rows ({cost_pct:.1f}%)",
        f"  sustainability_optimised:    {sust_n} rows ({sust_pct:.1f}%)",
        "",
        "Config saved:    configs/m2_config.yaml",
        "Lookup files:    data/external/plastic_props_m2.json",
    ]
    lines += [
        "                 data/external/material_costs_inr.json",
        "                 data/external/ice_emission_factors_m2.json",
        "                 data/external/plastic_co2_credits.json",
        "",
        "Next step: Paste the M2 model training prompt to train the GP surrogate,",
        "           NSGA-II/MOPSO optimisers, and scenario runner on this dataset.",
        "==================================================================",
    ]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
