"""
Deterministic LCA carbon calculator.
Formula: CO2e/m3 = sum(mass_kg * EF_kg_CO2e/kg) per material component.
Grounded in ICE Database v4.1 and IS 10262 M20 mix proportioning.
"""
from dataclasses import dataclass

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
        # -- Component masses ------------------------------------------------
        cement_kgm3    = 383.0
        additive_kgm3  = (params["additive_pct"] / 100.0) * cement_kgm3
        cement_kgm3   -= additive_kgm3   # additive partly replaces cement
        water_kgm3     = params["wc_ratio"] * cement_kgm3
        fine_agg_kgm3  = 680.0 * (1.0 - params["replacement_pct"] / 100.0)
        coarse_kgm3    = 1210.0

        ptype           = params["plastic_type"]
        plastic_density = self.density.get(ptype, 1100)
        vol_fraction    = params["replacement_pct"] / 100.0
        plastic_kgm3    = vol_fraction * plastic_density

        # -- CO2e per component ----------------------------------------------
        ef_cement   = self.ef.get("cement_opc", 0.872)
        ef_water    = self.ef.get("water_municipal", 0.0003)
        ef_sand     = self.ef.get("sand_river", 0.0048)
        ef_coarse   = self.ef.get("coarse_aggregate", 0.0048)
        ef_plastic  = self.ef.get(ptype, -1.10)   # negative credit

        atype = params["additive_type"]
        ef_additive_map = {
            "fly_ash":     self.ef.get("fly_ash", 0.004),
            "silica_fume": self.ef.get("silica_fume", 0.014),
            "fibres":      self.ef.get("fibres_plastic", 0.0),
            "none":        0.0,
        }
        ef_additive = ef_additive_map.get(atype, 0.0)

        co2_cement   = cement_kgm3   * ef_cement
        co2_water    = water_kgm3    * ef_water
        co2_sand     = fine_agg_kgm3 * ef_sand
        co2_coarse   = coarse_kgm3   * ef_coarse
        co2_plastic  = plastic_kgm3  * ef_plastic
        co2_additive = additive_kgm3 * ef_additive

        total_co2 = (co2_cement + co2_water + co2_sand +
                     co2_coarse + co2_plastic + co2_additive)

        saving     = BASELINE_CO2_KGM3 - total_co2
        saving_pct = (saving / BASELINE_CO2_KGM3) * 100.0
        pet_equiv  = int(plastic_kgm3 / 0.025)

        return LCAResult(
            cement_kgm3               = round(cement_kgm3, 2),
            water_kgm3                = round(water_kgm3, 2),
            fine_agg_kgm3             = round(fine_agg_kgm3, 2),
            coarse_agg_kgm3           = round(coarse_kgm3, 2),
            plastic_mass_kgm3         = round(plastic_kgm3, 2),
            additive_mass_kgm3        = round(additive_kgm3, 2),
            co2_cement_kgm3           = round(co2_cement, 4),
            co2_water_kgm3            = round(co2_water, 4),
            co2_sand_kgm3             = round(co2_sand, 4),
            co2_coarse_kgm3           = round(co2_coarse, 4),
            co2_plastic_kgm3          = round(co2_plastic, 4),
            co2_additive_kgm3         = round(co2_additive, 4),
            embodied_carbon_kgco2e_m3 = round(total_co2, 4),
            co2_saving_kgco2e_m3      = round(saving, 4),
            co2_saving_pct            = round(saving_pct, 4),
            plastic_diversion_kg_m3   = round(plastic_kgm3, 2),
            pet_bottle_equiv          = pet_equiv,
        )
