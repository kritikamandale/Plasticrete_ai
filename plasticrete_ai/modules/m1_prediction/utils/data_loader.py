"""
Loads all raw CSV sources, maps them to canonical schema columns, merges into
master_dataset.csv, and prints a coverage report.
"""
from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from loguru import logger

from modules.m1_prediction.utils.schema import (
    ADDITIVE_PCT, ADDITIVE_TYPE, ADDITIVE_TYPE_CLASSES, COMPRESSIVE_STRENGTH,
    CURING_DAYS, CURING_TEMP_C, DENSITY, DURABILITY_INDEX, FLEXURAL_STRENGTH,
    INPUT_FEATURES, MIX_ID, PARTICLE_SIZE_MM, PLASTIC_TYPE, PLASTIC_TYPE_CLASSES,
    REPLACEMENT_PCT, SOURCE_DOI, SPLIT_TENSILE, STUDY_TYPE, TARGET_COLUMNS,
    THERMAL_CONDUCTIVITY, WATER_ABSORPTION, WC_RATIO, MIN_COVERAGE_ROWS,
    INPUT_RANGES, TARGET_RANGES,
)

RAW_DIR       = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


# ---------------------------------------------------------------------------
# Per-source column mapping functions
# ---------------------------------------------------------------------------

def _load_uci_yeh(path: Path) -> pd.DataFrame:
    """UCI Yeh (1030 rows) â€” no plastic, used for DNN pretraining."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Typical UCI Yeh columns: cement, blast_furnace_slag, fly_ash, water,
    # superplasticizer, coarse_aggregate, fine_aggregate, age, concrete_compressive_strength
    cement_col = next((c for c in df.columns if "cement" in c), None)
    water_col  = next((c for c in df.columns if "water" in c), None)
    fly_ash_col = next((c for c in df.columns if "fly_ash" in c or "flyash" in c), None)
    slag_col   = next((c for c in df.columns if "slag" in c or "blast" in c), None)
    age_col    = next((c for c in df.columns if "age" in c), None)
    cs_col     = next((c for c in df.columns if "compressive" in c or "strength" in c), None)

    out = pd.DataFrame()

    if cement_col and water_col:
        out[WC_RATIO] = df[water_col] / df[cement_col]
    else:
        out[WC_RATIO] = 0.45

    if fly_ash_col and cement_col:
        fly_ash = df[fly_ash_col].fillna(0)
        slag    = df[slag_col].fillna(0) if slag_col else 0
        binder  = df[cement_col] + slag + fly_ash
        out[ADDITIVE_TYPE] = np.where(fly_ash > 0, "fly_ash", "none")
        out[ADDITIVE_PCT]  = np.where(binder > 0, fly_ash / binder * 100, 0.0)
    else:
        out[ADDITIVE_TYPE] = "none"
        out[ADDITIVE_PCT]  = 0.0

    out[PLASTIC_TYPE]    = "None"
    out[REPLACEMENT_PCT] = 0.0
    out[PARTICLE_SIZE_MM] = np.nan
    out[CURING_TEMP_C]   = 20.0
    out[CURING_DAYS]     = df[age_col].values if age_col else 28

    if cs_col:
        out[COMPRESSIVE_STRENGTH] = df[cs_col].values
    else:
        out[COMPRESSIVE_STRENGTH] = np.nan

    for t in [FLEXURAL_STRENGTH, SPLIT_TENSILE, DENSITY, WATER_ABSORPTION,
              THERMAL_CONDUCTIVITY, DURABILITY_INDEX]:
        out[t] = np.nan

    out[SOURCE_DOI] = "10.1061/(ASCE)0899-1561(1998)10:1(52)"
    out[STUDY_TYPE] = "pretraining"
    out[MIX_ID]     = [f"uci_{i}" for i in range(len(out))]
    return out


def _load_mendeley_rubberized(path: Path) -> pd.DataFrame:
    """Mendeley rubberized concrete â€” plastic surrogate for pretraining."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_").replace("/", "_") for c in df.columns]

    out = pd.DataFrame()

    rubber_col = next((c for c in df.columns if "rubber" in c and "content" in c), None)
    wc_col     = next((c for c in df.columns if c in ("wc_ratio", "w_c", "w/c", "wc")), None)
    days_col   = next((c for c in df.columns if "curing" in c or "age" in c or "day" in c), None)
    cs_col     = next((c for c in df.columns if "compressive" in c or "cs" in c or "strength" in c), None)

    out[REPLACEMENT_PCT] = df[rubber_col].values if rubber_col else 0.0
    out[WC_RATIO]        = df[wc_col].values if wc_col else 0.45
    out[CURING_DAYS]     = df[days_col].values if days_col else 28
    out[PLASTIC_TYPE]    = "Mixed"
    out[ADDITIVE_TYPE]   = "none"
    out[ADDITIVE_PCT]    = 0.0
    out[CURING_TEMP_C]   = 20.0
    out[PARTICLE_SIZE_MM] = np.nan

    if cs_col:
        out[COMPRESSIVE_STRENGTH] = df[cs_col].values
    else:
        out[COMPRESSIVE_STRENGTH] = np.nan

    for t in [FLEXURAL_STRENGTH, SPLIT_TENSILE, DENSITY, WATER_ABSORPTION,
              THERMAL_CONDUCTIVITY, DURABILITY_INDEX]:
        out[t] = np.nan

    out[SOURCE_DOI] = "mendeley_rubberized_concrete"
    out[STUDY_TYPE] = "pretraining"
    out[MIX_ID]     = [f"mend_{i}" for i in range(len(out))]
    return out


def _load_nayir_yilmaz_2024(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    col_map = {
        "plastic_type": PLASTIC_TYPE, "plastic_kind": PLASTIC_TYPE,
        "replacement_pct": REPLACEMENT_PCT, "replacement_%": REPLACEMENT_PCT,
        "replacement": REPLACEMENT_PCT, "content_%": REPLACEMENT_PCT,
        "particle_size_mm": PARTICLE_SIZE_MM, "size_mm": PARTICLE_SIZE_MM,
        "wc_ratio": WC_RATIO, "w/c": WC_RATIO, "w_c_ratio": WC_RATIO,
        "additive_type": ADDITIVE_TYPE, "admixture": ADDITIVE_TYPE,
        "additive_pct": ADDITIVE_PCT, "admixture_%": ADDITIVE_PCT,
        "curing_temp_c": CURING_TEMP_C, "temperature": CURING_TEMP_C,
        "curing_days": CURING_DAYS, "age": CURING_DAYS, "days": CURING_DAYS,
        "cs_mpa": COMPRESSIVE_STRENGTH, "compressive_strength": COMPRESSIVE_STRENGTH,
        "fs_mpa": FLEXURAL_STRENGTH, "flexural_strength": FLEXURAL_STRENGTH,
    }
    df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

    out = _ensure_columns(df)
    out[SOURCE_DOI] = "10.1016/nayir_yilmaz_2024"
    out[STUDY_TYPE] = "experimental"
    out[MIX_ID]     = [f"ny24_{i}" for i in range(len(out))]
    return out


def _load_nafees_2022(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    col_map = {
        "plastic_type": PLASTIC_TYPE, "type": PLASTIC_TYPE,
        "replacement_%": REPLACEMENT_PCT, "replacement_pct": REPLACEMENT_PCT,
        "w/c": WC_RATIO, "wc_ratio": WC_RATIO, "w_c": WC_RATIO,
        "cs_mpa": COMPRESSIVE_STRENGTH, "compressive_strength": COMPRESSIVE_STRENGTH,
        "sts_mpa": SPLIT_TENSILE, "split_tensile": SPLIT_TENSILE,
        "curing_days": CURING_DAYS, "age": CURING_DAYS,
        "particle_size_mm": PARTICLE_SIZE_MM, "size": PARTICLE_SIZE_MM,
        "additive_type": ADDITIVE_TYPE, "additive_pct": ADDITIVE_PCT,
    }
    df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

    if CURING_TEMP_C not in df.columns:
        df[CURING_TEMP_C] = 20.0

    out = _ensure_columns(df)
    out[SOURCE_DOI] = "10.3390/ma15010221"
    out[STUDY_TYPE] = "experimental"
    out[MIX_ID]     = [f"naf22_{i}" for i in range(len(out))]
    return out


def _load_chong_shi_2023(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    col_map = {
        "nominal_max_size_mm": PARTICLE_SIZE_MM, "size_mm": PARTICLE_SIZE_MM,
        "particle_size": PARTICLE_SIZE_MM,
        "cs_28day_mpa": COMPRESSIVE_STRENGTH, "compressive_strength": COMPRESSIVE_STRENGTH,
        "wc_ratio": WC_RATIO, "w/c": WC_RATIO,
        "replacement_pct": REPLACEMENT_PCT, "pet_content": REPLACEMENT_PCT,
        "curing_days": CURING_DAYS, "age": CURING_DAYS,
    }
    df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

    df[PLASTIC_TYPE]  = "PET"
    df[ADDITIVE_TYPE] = "none"
    df[ADDITIVE_PCT]  = 0.0
    df[CURING_TEMP_C] = 20.0

    out = _ensure_columns(df)
    out[SOURCE_DOI] = "10.1016/j.jclepro.2023.chong_shi"
    out[STUDY_TYPE] = "experimental"
    out[MIX_ID]     = [f"cs23_{i}" for i in range(len(out))]
    return out


def _load_alkharisi_dahish_2025(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    col_map = {
        "plastic_content": REPLACEMENT_PCT, "plastic_pct": REPLACEMENT_PCT,
        "w/c_ratio": WC_RATIO, "wc_ratio": WC_RATIO,
        "curing_age": CURING_DAYS, "curing_days": CURING_DAYS, "age": CURING_DAYS,
        "cs_mpa": COMPRESSIVE_STRENGTH, "compressive_strength": COMPRESSIVE_STRENGTH,
        "ts_mpa": SPLIT_TENSILE, "tensile_strength": SPLIT_TENSILE,
        "plastic_type": PLASTIC_TYPE,
    }
    df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

    if PLASTIC_TYPE not in df.columns:
        df[PLASTIC_TYPE] = "Mixed"
    df[PARTICLE_SIZE_MM] = np.nan
    df[ADDITIVE_TYPE]    = "none"
    df[ADDITIVE_PCT]     = 0.0
    df[CURING_TEMP_C]    = 20.0

    out = _ensure_columns(df)
    out[SOURCE_DOI] = "10.1016/alkharisi_dahish_2025"
    out[STUDY_TYPE] = "experimental"
    out[MIX_ID]     = [f"ak25_{i}" for i in range(len(out))]
    return out


def _load_manual_extraction(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    out = _ensure_columns(df)
    if SOURCE_DOI not in out.columns:
        out[SOURCE_DOI] = "manual"
    if STUDY_TYPE not in out.columns:
        out[STUDY_TYPE] = "experimental"
    if MIX_ID not in out.columns:
        out[MIX_ID] = [f"man_{i}" for i in range(len(out))]
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add any missing canonical columns as NaN so all sources are uniform."""
    all_cols = INPUT_FEATURES + TARGET_COLUMNS + [SOURCE_DOI, STUDY_TYPE, MIX_ID]
    for col in all_cols:
        if col not in df.columns:
            df[col] = np.nan
    return df[all_cols].copy()


def _generate_synthetic_bootstrap(n: int = 300) -> pd.DataFrame:
    """
    Physically-motivated synthetic data for when real plastic rows are sparse.
    CS formula: 60*(1-0.5*r/100)*(0.35/wc)^0.5 + N(0,5)
    """
    logger.warning("="*60)
    logger.warning("SYNTHETIC BOOTSTRAP ACTIVE â€” no real plastic data found.")
    logger.warning("These rows are physically motivated estimates, not lab data.")
    logger.warning("Replace with real extracted data as soon as available.")
    logger.warning("="*60)

    rng = np.random.default_rng(42)
    r   = rng.uniform(0, 40, n)
    wc  = rng.uniform(0.35, 0.65, n)
    cs  = 60 * (1 - 0.5 * r / 100) * (0.35 / wc) ** 0.5 + rng.normal(0, 5, n)
    cs  = np.clip(cs, 0, 90)

    plastic_types = rng.choice(["PET", "HDPE", "PP", "Mixed"], n)
    add_types     = rng.choice(ADDITIVE_TYPE_CLASSES, n)

    df = pd.DataFrame({
        PLASTIC_TYPE:    plastic_types,
        REPLACEMENT_PCT: r,
        PARTICLE_SIZE_MM: rng.uniform(0.5, 10, n),
        WC_RATIO:         wc,
        ADDITIVE_TYPE:    add_types,
        ADDITIVE_PCT:     rng.uniform(0, 15, n),
        CURING_TEMP_C:    rng.uniform(20, 40, n),
        CURING_DAYS:      rng.choice([7, 14, 28, 56, 90], n),
        COMPRESSIVE_STRENGTH: cs,
        FLEXURAL_STRENGTH:    np.nan,
        SPLIT_TENSILE:        np.nan,
        DENSITY:              np.nan,
        WATER_ABSORPTION:     np.nan,
        THERMAL_CONDUCTIVITY: np.nan,
        DURABILITY_INDEX:     np.nan,
        SOURCE_DOI:  "synthetic_bootstrap",
        STUDY_TYPE:  "synthetic_bootstrap",
        MIX_ID:      [f"syn_{i}" for i in range(n)],
    })
    return df


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def _fetch_uci_yeh(save_path: Path) -> None:
    from ucimlrepo import fetch_ucirepo
    logger.info("Fetching UCI Yeh concrete dataset via ucimlrepo â€¦")
    ds = fetch_ucirepo(id=165)
    combined = pd.concat([ds.data.features, ds.data.targets], axis=1)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(save_path, index=False)
    logger.info(f"Saved UCI Yeh dataset â†’ {save_path}  ({len(combined)} rows)")


def _load_plasticrete_final_2000(path: Path) -> pd.DataFrame:
    """PlastiCreteAI_M1_Final_2000.csv — primary real-data source (2000 rows, all 7 targets)."""
    df = pd.read_csv(path)

    # Normalise column names: strip, lower, collapse spaces/special chars
    df.columns = [c.strip() for c in df.columns]

    col_map = {
        "Plastic type":                    PLASTIC_TYPE,
        "Replacement %":                   REPLACEMENT_PCT,
        "Particle size (mm)":              PARTICLE_SIZE_MM,
        "w/c ratio":                       WC_RATIO,
        "Additive type":                   ADDITIVE_TYPE,
        "Additive %":                      ADDITIVE_PCT,
        "Curing temperature (°C)":    CURING_TEMP_C,
        "Curing temperature (Â°C)":        CURING_TEMP_C,   # encoding fallback
        "Curing duration (days)":          CURING_DAYS,
        "Compressive strength (MPa)":      COMPRESSIVE_STRENGTH,
        "Flexural strength (MPa)":         FLEXURAL_STRENGTH,
        "Split tensile strength (MPa)":    SPLIT_TENSILE,
        "Density (kg/m³)":            DENSITY,
        "Density (kg/mÂ³)":               DENSITY,          # encoding fallback
        "Water absorption (%)":            WATER_ABSORPTION,
        "Thermal conductivity (W/m·K)": THERMAL_CONDUCTIVITY,
        "Thermal conductivity (W/m·K)": THERMAL_CONDUCTIVITY,
        "Thermal conductivity (W/mÂ·K)":   THERMAL_CONDUCTIVITY,  # encoding fallback
        "Durability index":                DURABILITY_INDEX,
    }
    df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

    # Normalise additive type strings to schema canonical values
    additive_map = {
        "none":        "none",
        "silica fume": "silica_fume",
        "silica_fume": "silica_fume",
        "fly ash":     "fly_ash",
        "fly_ash":     "fly_ash",
        "ggbs":        "ggbs",
        "GGBS":        "ggbs",
        "fibres":      "fibres",
        "fiber":       "fibres",
    }
    if ADDITIVE_TYPE in df.columns:
        df[ADDITIVE_TYPE] = df[ADDITIVE_TYPE].str.strip().map(
            lambda v: additive_map.get(str(v).strip(), "none")
        )

    out = _ensure_columns(df)
    out[SOURCE_DOI] = "PlastiCreteAI_M1_Final_2000"
    out[STUDY_TYPE] = "experimental"
    out[MIX_ID]     = [f"pca_{i:05d}" for i in range(len(out))]
    return out


SOURCE_LOADERS = {
    "uci_yeh_concrete.csv":              _load_uci_yeh,
    "mendeley_rubberized.csv":           _load_mendeley_rubberized,
    "PlastiCreteAI_M1_Final_2000.csv":   _load_plasticrete_final_2000,
    "nayir_yilmaz_2024.csv":             _load_nayir_yilmaz_2024,
    "nafees_2022.csv":                   _load_nafees_2022,
    "chong_shi_2023.csv":                _load_chong_shi_2023,
    "alkharisi_dahish_2025.csv":         _load_alkharisi_dahish_2025,
    "manual_extraction.csv":             _load_manual_extraction,
}

PRETRAIN_SOURCES = {"uci_yeh_concrete.csv", "mendeley_rubberized.csv"}


def load_all_sources(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Load all available raw CSVs and merge into a single DataFrame."""
    raw_dir = Path(raw_dir)

    uci_path = raw_dir / "uci_yeh_concrete.csv"
    if not uci_path.exists():
        _fetch_uci_yeh(uci_path)

    frames = []
    for fname, loader in SOURCE_LOADERS.items():
        fpath = raw_dir / fname
        if not fpath.exists():
            logger.warning(f"Source file not found, skipping: {fpath}")
            continue
        try:
            df = loader(fpath)
            logger.info(f"Loaded {fname}: {len(df)} rows")
            _log_target_coverage(df, fname)
            frames.append(df)
        except Exception as exc:
            logger.warning(f"Failed to load {fname}: {exc}")

    if not frames:
        logger.error("No source files loaded at all â€” using synthetic bootstrap only.")
        return _generate_synthetic_bootstrap(300)

    master = pd.concat(frames, ignore_index=True)

    plastic_rows = master[master[PLASTIC_TYPE] != "None"]
    if len(plastic_rows) < MIN_COVERAGE_ROWS:
        logger.warning(f"Only {len(plastic_rows)} plastic-specific rows â€” adding synthetic bootstrap.")
        master = pd.concat([master, _generate_synthetic_bootstrap(300)], ignore_index=True)

    master[MIX_ID] = [f"mix_{i:05d}" for i in range(len(master))]
    return master


def save_master(master: pd.DataFrame, processed_dir: Path = PROCESSED_DIR) -> Path:
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    out_path = processed_dir / "master_dataset.csv"
    master.to_csv(out_path, index=False)
    logger.info(f"master_dataset.csv saved â†’ {out_path}")
    return out_path


def _log_target_coverage(df: pd.DataFrame, source: str) -> None:
    parts = []
    for t in TARGET_COLUMNS:
        if t in df.columns:
            n = df[t].notna().sum()
            if n > 0:
                parts.append(f"{t}: {n}")
    logger.info(f"  {source} targets: {', '.join(parts) if parts else 'none'}")


def print_coverage_report(master: pd.DataFrame) -> None:
    total = len(master)
    sep  = "=" * 57
    thin = "-" * 57
    print("\n" + sep)
    print("M1 DATA COVERAGE REPORT -- master_dataset.csv")
    print(f"Total rows: {total}")
    print(thin)
    for t in TARGET_COLUMNS:
        n   = master[t].notna().sum() if t in master.columns else 0
        pct = n / total * 100 if total > 0 else 0
        flag = "  [LOW]" if n < MIN_COVERAGE_ROWS else ""
        print(f"  {t:<35} {n:>5} rows ({pct:>5.1f}%){flag}")
    print(sep + "\n")

