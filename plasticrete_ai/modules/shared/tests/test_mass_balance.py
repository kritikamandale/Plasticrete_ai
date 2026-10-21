"""Mass balance is the single recipe, cost, and CO2 calculation."""
from __future__ import annotations

import json
from pathlib import Path

from modules.shared.mass_balance import compute, conventional_mix, load_factors

_ROOT = Path(__file__).resolve().parents[3]
_WEB_COPY = _ROOT.parent / "plasticrete_web" / "src" / "data" / "mass_balance_factors.json"

_SAMPLE = {
    "plastic_type": "PET",
    "replacement_pct": 15.0,
    "particle_size_mm": 4.0,
    "wc_ratio": 0.45,
    "additive_type": "fly_ash",
    "additive_pct": 10.0,
    "curing_temp_c": 27.0,
    "curing_days": 28,
}


def test_reference_mix_quantities_match_the_spreadsheet():
    balance = compute(_SAMPLE)
    assert balance["cement_kg_m3"] == 344.70
    assert balance["additive_kg_m3"] == 38.30
    assert balance["sand_kg_m3"] == 578.00
    assert balance["coarse_agg_kg_m3"] == 1210.00
    assert balance["plastic_kg_m3"] == 53.12
    assert balance["water_kg_m3"] == 172.35
    assert balance["pet_bottle_equiv"] == 2124


def test_displayed_rows_sum_to_the_totals():
    balance = compute(_SAMPLE)
    co2 = round(sum(row["co2_kgco2e_m3"] for row in balance["rows"]), 2)
    cost = round(sum(row["cost_inr_m3"] for row in balance["rows"]), 2)
    assert balance["co2_kgco2e_m3"] == co2
    assert balance["cost_inr_m3"] == cost
    assert balance["co2_kgco2e_m3"] == 239.24
    assert balance["cost_inr_m3"] == 7235.50
    assert balance["co2_saving_kgco2e_m3"] == 126.47
    assert balance["co2_saving_pct"] == 34.58


def test_every_row_carries_a_source_and_a_date():
    balance = compute(_SAMPLE)
    assert balance["table_id"] == "plasticrete-mass-balance-v1"
    assert balance["factor_date"] == "2026-03-01"
    for row in balance["rows"]:
        assert row["co2_factor_source"]
        assert row["co2_factor_date"]
        assert row["cost_factor_source"]
        assert row["cost_factor_date"]


def test_zero_plastic_has_no_diversion_and_full_sand():
    balance = compute({
        "plastic_type": "HDPE",
        "replacement_pct": 0,
        "wc_ratio": 0.50,
        "additive_type": "none",
        "additive_pct": 10,
    })
    assert balance["plastic_kg_m3"] == 0.0
    assert balance["additive_kg_m3"] == 0.0
    assert balance["cement_kg_m3"] == 383.00
    assert balance["sand_kg_m3"] == 680.00
    assert balance["pet_bottle_equiv"] == 0


def test_conventional_baseline_is_stable():
    first = conventional_mix()
    second = conventional_mix()
    assert first["cost_inr_m3"] == second["cost_inr_m3"]
    assert first["plastic_kg_m3"] == 0.0
    assert first["co2_kgco2e_m3"] > 0


def test_web_copy_matches_the_canonical_table():
    canonical = load_factors()
    assert _WEB_COPY.exists(), f"missing frontend copy at {_WEB_COPY}"
    with open(_WEB_COPY, encoding="utf-8") as handle:
        web = json.load(handle)
    assert web == canonical
