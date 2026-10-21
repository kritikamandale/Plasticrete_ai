"""
One bill of materials, one cost, one CO2 number.

M2, M3, M5, and the sustainability page all call ``compute``. Quantities and
money are integer hundredths so a spreadsheet of the displayed rows matches
the totals. Factors are read from data/external/mass_balance_factors.json.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_FACTOR_PATH = Path(__file__).resolve().parents[2] / "data" / "external" / "mass_balance_factors.json"

_MILLION = 1_000_000


def _div_round(numer: int, denom: int) -> int:
    """Integer division, half away from zero."""
    if denom < 0:
        numer, denom = -numer, -denom
    if numer >= 0:
        return (numer + denom // 2) // denom
    return -((-numer + denom // 2) // denom)


def _str_to_millionths(text: str) -> int:
    neg = text.strip().startswith("-")
    raw = text.strip()[1:] if neg else text.strip()
    if "." in raw:
        whole, frac = raw.split(".", 1)
        frac = (frac + "000000")[:6]
    else:
        whole, frac = raw, "000000"
    mag = int(whole or "0") * _MILLION + int(frac)
    return -mag if neg else mag


def _hundredths_to_float(hundredths: int) -> float:
    sign = "-" if hundredths < 0 else ""
    mag = abs(hundredths)
    return float(f"{sign}{mag // 100}.{mag % 100:02d}")


def _mul(qty_hundredths: int, factor_millionths: int) -> int:
    """Quantity in 0.01 units times a factor in 1e-6 units → product in 0.01 units."""
    return _div_round(qty_hundredths * factor_millionths, _MILLION)


@lru_cache(maxsize=1)
def load_factors() -> dict:
    with open(_FACTOR_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def _factor(table: dict, key: str) -> dict:
    try:
        return table[key]
    except KeyError as exc:
        raise KeyError(f"Mass-balance table has no entry for {key}") from exc


def _qty_hundredths(params: dict, factors: dict) -> dict[str, int]:
    ref = factors["reference"]
    binder = _str_to_millionths(ref["cement_kg_m3"]) // 10_000  # hundredths
    sand_ref = _str_to_millionths(ref["fine_aggregate_kg_m3"]) // 10_000
    coarse = _str_to_millionths(ref["coarse_aggregate_kg_m3"]) // 10_000
    ssd = int(factors["reference"]["aggregate_ssd_density_kg_m3"])

    additive_type = params.get("additive_type") or "none"
    add_pct_milli = _div_round(int(round(float(params.get("additive_pct", 0.0)) * 1000)), 1)
    if additive_type == "none":
        add_pct_milli = 0
    additive = _div_round(binder * add_pct_milli, 100_000)
    cement = binder - additive

    wc_milli = _div_round(int(round(float(params.get("wc_ratio", 0.5)) * 1000)), 1)
    water = _div_round(wc_milli * binder, 1_000)

    rep_milli = _div_round(int(round(float(params.get("replacement_pct", 0.0)) * 1000)), 1)
    sand_removed = _div_round(rep_milli * sand_ref, 100_000)
    sand = sand_ref - sand_removed

    plastic_type = params.get("plastic_type") or "PET"
    density = int(_factor(factors["densities_kg_m3"], plastic_type)["value"])
    # plastic kg hundredths = round(rep_pct * 680 * density / 2650)
    # rep_milli is rep_pct * 1000, sand reference mass is inside the 680 constant via sand_ref.
    # plastic_h = rep_milli * sand_ref_kg * density / (1000 * ssd)
    sand_kg = sand_ref // 100
    plastic = _div_round(rep_milli * sand_kg * density, 1000 * ssd)

    return {
        "cement": cement,
        "additive": additive,
        "sand": sand,
        "coarse": coarse,
        "plastic": plastic,
        "water": water,
        "overhead": 100,  # 1.00 unit, so the overhead factor is INR per m3
        "additive_type": additive_type,
        "plastic_type": plastic_type,
    }


def _row(material: str, qty_h: int, co2_key: str, cost_key: str, factors: dict) -> dict:
    co2 = _factor(factors["emission_factors_kgco2e_per_kg"], co2_key)
    cost = _factor(factors["costs_inr_per_kg"], cost_key)
    co2_h = _mul(qty_h, _str_to_millionths(co2["value"]))
    cost_h = _mul(qty_h, _str_to_millionths(cost["value"]))
    return {
        "material": material,
        "quantity_kg_m3": _hundredths_to_float(qty_h),
        "co2_factor_kg_per_kg": float(co2["value"]),
        "co2_factor_source": co2["source"],
        "co2_factor_date": co2["date"],
        "co2_kgco2e_m3": _hundredths_to_float(co2_h),
        "cost_factor_inr_per_kg": float(cost["value"]),
        "cost_factor_source": cost["source"],
        "cost_factor_date": cost["date"],
        "cost_inr_m3": _hundredths_to_float(cost_h),
        "_co2_h": co2_h,
        "_cost_h": cost_h,
    }


_ADDITIVE_LABELS = {
    "fly_ash": "Fly ash",
    "silica_fume": "Silica fume",
    "fibres": "Plastic fibres",
    "none": "No SCM",
}


def compute(params: dict) -> dict:
    """
    Bill of materials for one cubic metre.

    ``params`` needs plastic_type, replacement_pct, wc_ratio, additive_type,
    additive_pct. Particle size and curing do not change the mass balance.
    """
    factors = load_factors()
    qty = _qty_hundredths(params, factors)
    additive_type = qty["additive_type"]
    plastic_type = qty["plastic_type"]

    rows = [
        _row("OPC cement", qty["cement"], "cement_opc", "cement_opc", factors),
        _row(
            _ADDITIVE_LABELS.get(additive_type, additive_type),
            qty["additive"],
            additive_type,
            additive_type,
            factors,
        ),
        _row("River sand", qty["sand"], "sand_river", "sand_river", factors),
        _row("Coarse aggregate", qty["coarse"], "coarse_aggregate", "coarse_aggregate", factors),
        _row(f"Plastic ({plastic_type})", qty["plastic"], plastic_type, plastic_type, factors),
        _row("Water", qty["water"], "water", "water", factors),
        _row("Batching overhead", qty["overhead"], "overhead", "overhead", factors),
    ]

    co2_h = sum(row["_co2_h"] for row in rows)
    cost_h = sum(row["_cost_h"] for row in rows)
    baseline_h = _str_to_millionths(factors["baseline_co2_kgco2e_m3"]) // 10_000
    saving_h = baseline_h - co2_h
    if baseline_h == 0:
        saving_pct_h = 0
    else:
        saving_pct_h = _div_round(saving_h * 10_000, baseline_h)

    # 0.025 kg is 25 g. Quantity is stored in hundredths of a kilogram (10 g),
    # so whole bottles = plastic_hundredths * 10 g / 25 g.
    bottles = (qty["plastic"] * 2) // 5 if qty["plastic"] > 0 else 0

    public_rows = []
    for row in rows:
        public = {key: value for key, value in row.items() if not key.startswith("_")}
        public_rows.append(public)

    return {
        "table_id": factors["table_id"],
        "factor_date": factors["factor_date"],
        "basis": factors["basis"],
        "rows": public_rows,
        "cement_kg_m3": _hundredths_to_float(qty["cement"]),
        "sand_kg_m3": _hundredths_to_float(qty["sand"]),
        "coarse_agg_kg_m3": _hundredths_to_float(qty["coarse"]),
        "plastic_kg_m3": _hundredths_to_float(qty["plastic"]),
        "water_kg_m3": _hundredths_to_float(qty["water"]),
        "additive_kg_m3": _hundredths_to_float(qty["additive"]),
        "cost_inr_m3": _hundredths_to_float(cost_h),
        "co2_kgco2e_m3": _hundredths_to_float(co2_h),
        "co2_saving_kgco2e_m3": _hundredths_to_float(saving_h),
        "co2_saving_pct": _hundredths_to_float(saving_pct_h),
        "baseline_co2_kgco2e_m3": _hundredths_to_float(baseline_h),
        "baseline_source": factors["baseline_source"],
        "baseline_date": factors["baseline_date"],
        "pet_bottle_equiv": int(bottles),
        "plastic_type": plastic_type,
        "additive_type": additive_type,
    }


def conventional_mix() -> dict:
    """IS 10262 M20 with no plastic and no SCM, w/b = 0.50."""
    return compute({
        "plastic_type": "PET",
        "replacement_pct": 0.0,
        "wc_ratio": 0.50,
        "additive_type": "none",
        "additive_pct": 0.0,
    })
