"""
Deterministic LCA carbon calculator.

Masses, cost, and CO2 come from modules.shared.mass_balance so M2, M3, M5,
and the sustainability page cannot disagree. Emission factors are the ICE v4.1
rows in data/external/mass_balance_factors.json.
"""
from dataclasses import dataclass

from modules.shared.mass_balance import compute as compute_mass_balance

BASELINE_CO2_KGM3 = 365.71   # conventional M20 from Goh et al. 2022


@dataclass
class LCAResult:
    # Component masses
    cement_kgm3:        float
    water_kgm3:         float
    fine_agg_kgm3:      float
    coarse_agg_kgm3:    float
    plastic_mass_kgm3:  float
    additive_mass_kgm3: float

    # Component CO2e contributions
    co2_cement_kgm3:   float
    co2_water_kgm3:    float
    co2_sand_kgm3:     float
    co2_coarse_kgm3:   float
    co2_plastic_kgm3:  float
    co2_additive_kgm3: float

    # Totals
    embodied_carbon_kgco2e_m3: float
    co2_saving_kgco2e_m3:      float
    co2_saving_pct:             float

    # Plastic diversion
    plastic_diversion_kg_m3: float
    pet_bottle_equiv:         int


class LCACalculator:
    """
    Computes embodied carbon for a plastic concrete mix.

    Mix composition model follows IS 10262:2019 M20 reference:
    - Baseline cement: 383 kg/m3
    - Additive partially replaces cement (additive_pct% of cement mass)
    - Fine aggregate: 680 kg/m3 * (1 - replacement_pct/100)
    - Plastic mass: replacement_pct/100 * plastic_density

    Emission factors from ICE Database v4.1 (Circular Ecology, 2025).
    Plastic types carry NEGATIVE emission factors (carbon credits for
    diverting post-consumer waste from landfill/incineration).
    """

    def __init__(self, config: dict, ef: dict, densities: dict):
        self.config   = config
        self.ef       = ef
        self.density  = densities

    def compute(self, params: dict, m1_props: dict = None) -> LCAResult:
        balance = compute_mass_balance(params)
        by_name = {row["material"]: row for row in balance["rows"]}

        def co2_of(name: str) -> float:
            return float(by_name[name]["co2_kgco2e_m3"])

        additive_name = next(
            name for name in by_name
            if name not in {
                "OPC cement", "River sand", "Coarse aggregate", "Water", "Batching overhead",
            } and not name.startswith("Plastic")
        )

        return LCAResult(
            cement_kgm3               = balance["cement_kg_m3"],
            water_kgm3                = balance["water_kg_m3"],
            fine_agg_kgm3             = balance["sand_kg_m3"],
            coarse_agg_kgm3           = balance["coarse_agg_kg_m3"],
            plastic_mass_kgm3         = balance["plastic_kg_m3"],
            additive_mass_kgm3        = balance["additive_kg_m3"],
            co2_cement_kgm3           = co2_of("OPC cement"),
            co2_water_kgm3            = co2_of("Water"),
            co2_sand_kgm3             = co2_of("River sand"),
            co2_coarse_kgm3           = co2_of("Coarse aggregate"),
            co2_plastic_kgm3          = co2_of(f"Plastic ({balance['plastic_type']})"),
            co2_additive_kgm3         = co2_of(additive_name),
            embodied_carbon_kgco2e_m3 = balance["co2_kgco2e_m3"],
            co2_saving_kgco2e_m3      = balance["co2_saving_kgco2e_m3"],
            co2_saving_pct            = balance["co2_saving_pct"],
            plastic_diversion_kg_m3   = balance["plastic_kg_m3"],
            pet_bottle_equiv          = int(balance["pet_bottle_equiv"]),
        )
