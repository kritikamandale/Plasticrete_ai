"""
pipeline/generate_m3_dataset.py
================================
Generate the M3 sustainability & compliance training dataset.

Usage:
    python pipeline/generate_m3_dataset.py
    python pipeline/generate_m3_dataset.py --rows 2200 --seed 42
    python pipeline/generate_m3_dataset.py --no-m1
    python pipeline/generate_m3_dataset.py --validate

Output: data/processed/m3_training_dataset.csv  (2200 rows x ~70 columns)
"""

import argparse
import sys
import yaml
import json
import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from loguru import logger

# -- Import M3 core modules --------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.m3_sustainability.core.lca_calculator import LCACalculator
from modules.m3_sustainability.core.bis_checker import BISChecker
from modules.m3_sustainability.core.green_rater import GreenRater
from modules.m3_sustainability.core.score_aggregator import ScoreAggregator
from modules.m3_sustainability.core.remediation_advisor import RemediationAdvisor
from modules.m3_sustainability.utils.emission_factors import get_emission_factors
from modules.m3_sustainability.utils.physics_formulas import predict_properties

# -- M1 import (graceful fallback if M1 not trained) -------------------------
try:
    import modules.m1_prediction as m1
    M1_AVAILABLE = True
except Exception as e:
    logger.warning(f"M1 not available ({e}). Using physics formulas only.")
    M1_AVAILABLE = False

PLASTIC_TYPES  = ["PET", "HDPE", "LDPE", "PVC", "PP", "Mixed"]
ADDITIVE_TYPES = ["fly_ash", "silica_fume", "fibres", "none"]


def parse_args():
    p = argparse.ArgumentParser(description="Generate M3 training dataset")
    p.add_argument("--config",   default="configs/m3_config.yaml")
    p.add_argument("--rows",     type=int, default=2200)
    p.add_argument("--seed",     type=int, default=42)
    p.add_argument("--no-m1",    action="store_true")
    p.add_argument("--validate", action="store_true")
    return p.parse_args()


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def sample_mix_params(rng: np.random.Generator, strategy: str = "uniform") -> dict:
    ptype = rng.choice(PLASTIC_TYPES)
    atype = rng.choice(ADDITIVE_TYPES)

    if strategy == "realistic":
        rep_pct = float(rng.triangular(0, 15, 40))
        wc      = float(rng.triangular(0.35, 0.45, 0.65))
        add_pct = float(rng.triangular(0, 10, 30)) if atype != "none" else 0.0
        days    = int(rng.choice([7, 14, 28, 56, 90], p=[0.10, 0.15, 0.50, 0.15, 0.10]))
        ps      = float(rng.triangular(1.0, 5.0, 20.0))
        temp    = float(rng.triangular(20, 25, 80))
    elif strategy == "stress":
        rep_pct = float(rng.choice([0, 5, 35, 40]))
        wc      = float(rng.choice([0.35, 0.60, 0.65]))
        add_pct = float(rng.choice([0, 30]))
        days    = int(rng.choice([3, 7, 90]))
        ps      = float(rng.choice([0.5, 10, 20]))
        temp    = float(rng.choice([20, 60, 80]))
    else:  # uniform
        rep_pct = float(rng.uniform(0, 40))
        wc      = float(rng.uniform(0.35, 0.65))
        add_pct = float(rng.uniform(0, 30)) if atype != "none" else 0.0
        days    = int(rng.integers(3, 91))
        ps      = float(rng.uniform(0.5, 20))
        temp    = float(rng.uniform(20, 80))

    if atype == "none":
        add_pct = 0.0

    return {
        "plastic_type":     str(ptype),
        "replacement_pct":  round(rep_pct, 2),
        "particle_size_mm": round(ps, 2),
        "wc_ratio":         round(wc, 3),
        "additive_type":    str(atype),
        "additive_pct":     round(add_pct, 2),
        "curing_temp_c":    round(temp, 1),
        "curing_days":      days,
    }


def get_m1_properties(params: dict) -> dict:
    result = m1.predict(params)
    return {
        "compressive_strength_mpa": float(result.compressive_strength_mpa or 0.0),
        "flexural_strength_mpa":    float(result.flexural_strength_mpa    or 0.0),
        "split_tensile_mpa":        float(result.split_tensile_mpa        or 0.0),
        "density_kgm3":             float(result.density_kgm3             or 2000.0),
        "water_absorption_pct":     float(result.water_absorption_pct     or 5.0),
        "thermal_conductivity_wm":  float(result.thermal_conductivity_wm  or 1.0),
        "durability_index":         float(result.durability_index         or 50.0),
    }


def build_row(
    row_id: str,
    params: dict,
    props: dict,
    method: str,
    lca_calc: LCACalculator,
    bis_check: BISChecker,
    green_rater: GreenRater,
    scorer: ScoreAggregator,
    advisor: RemediationAdvisor,
) -> dict:
    lca   = lca_calc.compute(params, props)
    bis   = bis_check.check(props)
    green = green_rater.rate(params, props, lca)
    score = scorer.score(params, lca, bis, green)
    remed = advisor.advise(params, props, lca, bis, score)

    return {
        # Metadata
        "row_id":            row_id,
        "generation_method": method,
        # 8 Mix Inputs
        "plastic_type":      params["plastic_type"],
        "replacement_pct":   params["replacement_pct"],
        "particle_size_mm":  params["particle_size_mm"],
        "wc_ratio":          params["wc_ratio"],
        "additive_type":     params["additive_type"],
        "additive_pct":      params["additive_pct"],
        "curing_temp_c":     params["curing_temp_c"],
        "curing_days":       params["curing_days"],
        # 7 M1 Predicted Properties
        "compressive_strength_mpa": props["compressive_strength_mpa"],
        "flexural_strength_mpa":    props["flexural_strength_mpa"],
        "split_tensile_mpa":        props["split_tensile_mpa"],
        "density_kgm3":             props["density_kgm3"],
        "water_absorption_pct":     props["water_absorption_pct"],
        "thermal_conductivity_wm":  props["thermal_conductivity_wm"],
        "durability_index":         props["durability_index"],
        # GROUP A: LCA / Carbon
        "cement_kgm3":               lca.cement_kgm3,
        "water_kgm3":                lca.water_kgm3,
        "fine_agg_kgm3":             lca.fine_agg_kgm3,
        "coarse_agg_kgm3":           lca.coarse_agg_kgm3,
        "plastic_mass_kgm3":         lca.plastic_mass_kgm3,
        "additive_mass_kgm3":        lca.additive_mass_kgm3,
        "co2_cement_kgm3":           lca.co2_cement_kgm3,
        "co2_water_kgm3":            lca.co2_water_kgm3,
        "co2_sand_kgm3":             lca.co2_sand_kgm3,
        "co2_coarse_kgm3":           lca.co2_coarse_kgm3,
        "co2_plastic_kgm3":          lca.co2_plastic_kgm3,
        "co2_additive_kgm3":         lca.co2_additive_kgm3,
        "embodied_carbon_kgco2e_m3": lca.embodied_carbon_kgco2e_m3,
        "baseline_concrete_co2":     365.71,
        "co2_saving_kgco2e_m3":      lca.co2_saving_kgco2e_m3,
        "co2_saving_pct":            lca.co2_saving_pct,
        "plastic_diversion_kg_m3":   lca.plastic_diversion_kg_m3,
        "pet_bottle_equiv":          lca.pet_bottle_equiv,
        # GROUP B: BIS Compliance
        "is_516_grade":           bis.is_516_grade,
        "is_516_compliant":       int(bis.is_516_compliant),
        "is_1237_compliant":      int(bis.is_1237_compliant),
        "is_1237_cs_margin_mpa":  bis.is_1237_cs_margin,
        "is_1237_wa_margin_pct":  bis.is_1237_wa_margin,
        "is_2185_pt1_compliant":  int(bis.is_2185_pt1_compliant),
        "is_2185_cs_margin_mpa":  bis.is_2185_cs_margin,
        "is_2185_pt2_compliant":  int(bis.is_2185_pt2_compliant),
        "is_5816_compliant":      int(bis.is_5816_compliant),
        "nbc_2016_structural":    int(bis.nbc_structural),
        "nbc_2016_nonstructural": int(bis.nbc_nonstructural),
        "bis_overall_pass":       int(bis.bis_overall_pass),
        "n_standards_passed":     bis.n_standards_passed,
        # GROUP C: Green Rating
        "igbc_recycled_content_credit":   green.igbc_recycled_content,
        "igbc_regional_materials_credit": green.igbc_regional_materials,
        "igbc_indoor_air_credit":         green.igbc_indoor_air,
        "igbc_total_credits":             green.igbc_total,
        "griha_embodied_energy_point":    green.griha_embodied_energy,
        "griha_waste_management_point":   green.griha_waste_management,
        "griha_material_criterion_pts":   green.griha_total,
        "leed_bpdo_credit":               green.leed_bpdo,
        "leed_construction_waste_credit": green.leed_construction_waste,
        "leed_total_points":              green.leed_total,
        "total_green_credits":            green.total_green_credits,
        # GROUP D: Sustainability Score
        "score_carbon_component":        score.score_carbon_component,
        "score_plastic_diversion_comp":  score.score_plastic_diversion_comp,
        "score_recycled_content_comp":   score.score_recycled_content_comp,
        "score_bis_compliance_comp":     score.score_bis_compliance_comp,
        "score_green_rating_comp":       score.score_green_rating_comp,
        "sustainability_score":          score.sustainability_score,
        "sustainability_grade":          score.sustainability_grade,
        # GROUP E: Remediation
        "top_negative_factor":   remed.top_negative_factor,
        "remediation_action_1":  remed.remediation_action_1,
        "remediation_action_2":  remed.remediation_action_2,
        "remediation_action_3":  remed.remediation_action_3,
        "estimated_score_gain":  remed.estimated_score_gain,
    }


def validate_dataset(df: pd.DataFrame) -> None:
    logger.info("=" * 65)
    logger.info("M3 DATASET VALIDATION REPORT")
    logger.info(f"Total rows:    {len(df)}")
    logger.info(f"Total columns: {len(df.columns)}")
    logger.info("-" * 65)

    assert len(df.columns) >= 60, f"Too few columns: {len(df.columns)}"

    for method in df["generation_method"].unique():
        n = (df["generation_method"] == method).sum()
        logger.info(f"  {method:<20}: {n} rows")

    logger.info("\nPlastic type distribution:")
    for pt in PLASTIC_TYPES:
        n   = (df["plastic_type"] == pt).sum()
        pct = n / len(df) * 100
        logger.info(f"  {pt:<8}: {n:>4} rows ({pct:5.1f}%)")

    logger.info("\nSustainability grade distribution:")
    for g in ["A", "B", "C", "D"]:
        n   = (df["sustainability_grade"] == g).sum()
        pct = n / len(df) * 100
        logger.info(f"  Grade {g}: {n:>4} rows ({pct:5.1f}%)")

    bis_pass = df["bis_overall_pass"].sum()
    logger.info(f"\nBIS overall pass: {bis_pass}/{len(df)} ({bis_pass/len(df)*100:.1f}%)")

    logger.info(f"\nEmbodied carbon range:")
    logger.info(f"  Min: {df['embodied_carbon_kgco2e_m3'].min():.1f} kg CO2e/m3")
    logger.info(f"  Max: {df['embodied_carbon_kgco2e_m3'].max():.1f} kg CO2e/m3")
    logger.info(f"  Mean:{df['embodied_carbon_kgco2e_m3'].mean():.1f} kg CO2e/m3")

    critical = ["embodied_carbon_kgco2e_m3", "sustainability_score",
                "bis_overall_pass", "total_green_credits"]
    for col in critical:
        n_nan = df[col].isna().sum()
        assert n_nan == 0, f"NaN in critical column '{col}': {n_nan} rows"
        logger.info(f"  OK {col}: no NaN")

    logger.info("=" * 65)
    logger.info("VALIDATION PASSED")
    logger.info("=" * 65)


def ensure_plastic_coverage(rows: list, rng: np.random.Generator,
                             lca_calc, bis_check, green_rater, scorer, advisor,
                             min_per_type: int = 300) -> list:
    """Top-up any plastic type that has fewer than min_per_type rows."""
    df_tmp = pd.DataFrame(rows)
    counts = df_tmp["plastic_type"].value_counts()
    extra  = []
    row_counter = len(rows)
    for ptype in PLASTIC_TYPES:
        current = counts.get(ptype, 0)
        needed  = min_per_type - current
        if needed <= 0:
            continue
        logger.info(f"Topping up {ptype}: adding {needed} rows")
        for _ in range(needed):
            atype  = str(rng.choice(ADDITIVE_TYPES))
            add_pct= float(rng.uniform(0, 20)) if atype != "none" else 0.0
            params = {
                "plastic_type":     ptype,
                "replacement_pct":  round(float(rng.uniform(5, 35)), 2),
                "particle_size_mm": round(float(rng.uniform(1, 15)), 2),
                "wc_ratio":         round(float(rng.uniform(0.38, 0.58)), 3),
                "additive_type":    atype,
                "additive_pct":     round(add_pct, 2),
                "curing_temp_c":    round(float(rng.uniform(20, 60)), 1),
                "curing_days":      int(rng.integers(7, 56)),
            }
            props = predict_properties(params)
            row_counter += 1
            row = build_row(
                f"M3_{row_counter:05d}", params, props, "augmented",
                lca_calc, bis_check, green_rater, scorer, advisor
            )
            extra.append(row)
    return rows + extra


def main():
    args   = parse_args()
    config = load_config(args.config)

    # Configure logger
    log_path = Path(config["logging"]["log_file"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(log_path, level=config["logging"]["level"])

    n_rows = args.rows
    rng    = np.random.default_rng(args.seed)

    # Load reference data
    ef        = get_emission_factors(config)
    densities = {
        k: v["density_kgm3"]
        for k, v in load_json(config["external_data"]["plastic_density_path"])["densities"].items()
    }

    # Initialise M1 if available
    use_m1 = M1_AVAILABLE and not args.no_m1
    if use_m1:
        try:
            with open(config["m1"]["config_path"]) as f:
                m1_config = yaml.safe_load(f)
            m1.load_ensemble(config["m1"]["model_dir"], m1_config)
            logger.info("M1 ensemble loaded. Using M1 predictions for 1400 rows.")
        except Exception as e:
            logger.warning(f"M1 load failed: {e}. Falling back to physics formulas.")
            use_m1 = False

    # Initialise M3 scoring engines
    lca_calc   = LCACalculator(config, ef, densities)
    bis_check  = BISChecker()
    green_rater= GreenRater(config)
    scorer     = ScoreAggregator(config)
    advisor    = RemediationAdvisor()

    # Determine row counts
    n_m1_rows      = config["dataset"]["row_splits"]["m1_predicted"] if use_m1 else 0
    n_physics_rows = n_rows - n_m1_rows
    n_stress       = int(n_physics_rows * 0.15)
    n_realistic    = int(n_physics_rows * 0.55)
    n_uniform      = n_physics_rows - n_stress - n_realistic

    logger.info(f"Generating {n_rows} total rows:")
    logger.info(f"  M1 predicted:      {n_m1_rows}")
    logger.info(f"  Physics realistic: {n_realistic}")
    logger.info(f"  Physics uniform:   {n_uniform}")
    logger.info(f"  Physics stress:    {n_stress}")

    rows = []
    row_counter = 0

    # BATCH 1: M1 predicted rows
    if use_m1 and n_m1_rows > 0:
        logger.info("Generating M1-predicted rows...")
        for i in tqdm(range(n_m1_rows), desc="M1 rows"):
            strategy = ["uniform", "realistic", "realistic"][i % 3]
            params   = sample_mix_params(rng, strategy)
            try:
                props = get_m1_properties(params)
            except Exception as e:
                logger.warning(f"M1 failed on row {i}: {e}. Using physics.")
                props = predict_properties(params)
            row_counter += 1
            rows.append(build_row(
                f"M3_{row_counter:05d}", params, props, "m1_predicted",
                lca_calc, bis_check, green_rater, scorer, advisor
            ))

    # BATCH 2: Realistic physics rows
    logger.info("Generating realistic physics rows...")
    for _ in tqdm(range(n_realistic), desc="Realistic"):
        params = sample_mix_params(rng, "realistic")
        props  = predict_properties(params)
        row_counter += 1
        rows.append(build_row(
            f"M3_{row_counter:05d}", params, props, "physics_formula",
            lca_calc, bis_check, green_rater, scorer, advisor
        ))

    # BATCH 3: Uniform physics rows
    logger.info("Generating uniform physics rows...")
    for _ in tqdm(range(n_uniform), desc="Uniform"):
        params = sample_mix_params(rng, "uniform")
        props  = predict_properties(params)
        row_counter += 1
        rows.append(build_row(
            f"M3_{row_counter:05d}", params, props, "physics_formula",
            lca_calc, bis_check, green_rater, scorer, advisor
        ))

    # BATCH 4: Stress test rows
    logger.info("Generating stress test rows (corner cases)...")
    for _ in tqdm(range(n_stress), desc="Stress"):
        params = sample_mix_params(rng, "stress")
        props  = predict_properties(params)
        row_counter += 1
        rows.append(build_row(
            f"M3_{row_counter:05d}", params, props, "augmented",
            lca_calc, bis_check, green_rater, scorer, advisor
        ))

    # Ensure minimum plastic type coverage (>=300 per type)
    rows = ensure_plastic_coverage(
        rows, rng, lca_calc, bis_check, green_rater, scorer, advisor,
        min_per_type=300
    )

    # Build DataFrame and save
    df = pd.DataFrame(rows)
    # Trim to exactly n_rows if top-up pushed us over (keep all if under)
    if len(df) > n_rows + 200:
        df = df.sample(n=n_rows, random_state=args.seed).reset_index(drop=True)

    logger.info(f"Dataset built: {len(df)} rows x {len(df.columns)} columns")

    out_path = Path(config["dataset"]["output_path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    logger.info(f"Saved -> {out_path}")

    # Validate
    validate_dataset(df)

    # Summary
    print("\n" + "=" * 65)
    print("  PlastiCrete AI - M3 Training Dataset Complete")
    print(f"   Rows generated:     {len(df)}")
    print(f"   Columns:            {len(df.columns)}")
    print(f"   File:               {out_path}")
    print(f"   CO2e range:         {df['embodied_carbon_kgco2e_m3'].min():.1f}"
          f" - {df['embodied_carbon_kgco2e_m3'].max():.1f} kg CO2e/m3")
    print(f"   Score range:        {df['sustainability_score'].min():.1f}"
          f" - {df['sustainability_score'].max():.1f}")
    print(f"   BIS pass rate:      {df['bis_overall_pass'].mean()*100:.1f}%")
    print(f"   Grade A/B/C/D:      "
          f"{(df['sustainability_grade']=='A').sum()}/"
          f"{(df['sustainability_grade']=='B').sum()}/"
          f"{(df['sustainability_grade']=='C').sum()}/"
          f"{(df['sustainability_grade']=='D').sum()}")
    pt_counts = df["plastic_type"].value_counts()
    print(f"   Plastic coverage:   " +
          " ".join(f"{pt}={pt_counts.get(pt,0)}" for pt in PLASTIC_TYPES))
    print("\n   Next: Paste the M3 model training prompt to train:")
    print("   - LCA regression model (predict embodied_carbon_kgco2e_m3)")
    print("   - BIS compliance classifier (predict bis_overall_pass)")
    print("   - Sustainability score regressor (predict sustainability_score)")
    print("   - Green rating classifier (predict total_green_credits)")
    print("=" * 65)


if __name__ == "__main__":
    main()
