"""
Rule-based BIS compliance checker.
All thresholds imported from constants.py — single source of truth.
This is NOT an ML model - it is a deterministic rule lookup.
"""
from dataclasses import dataclass

from modules.m3_sustainability.utils.constants import (
    IS_1237_MIN_CS_MPA, IS_1237_MAX_WA_PCT,
    IS_2185_PT1_MIN_CS_MPA, IS_2185_PT2_MAX_DENSITY, IS_2185_PT2_MAX_WA_PCT,
    IS_5816_MIN_STS_CS_RATIO, IS_5816_MIN_STS_MPA,
    NBC_STRUCTURAL_MIN_CS_MPA, NBC_STRUCTURAL_MIN_DENSITY, NBC_STRUCTURAL_MAX_DENSITY,
    NBC_NONSTRUCTURAL_MIN_CS_MPA, NBC_NONSTRUCTURAL_MAX_DENSITY,
)


@dataclass
class BISResult:
    is_516_grade:          str
    is_516_compliant:      bool
    is_1237_compliant:     bool
    is_1237_cs_margin:     float
    is_1237_wa_margin:     float
    is_2185_pt1_compliant: bool
    is_2185_cs_margin:     float
    is_2185_pt2_compliant: bool
    is_5816_compliant:     bool
    nbc_structural:        bool
    nbc_nonstructural:     bool
    bis_overall_pass:      bool
    n_standards_passed:    int


class BISChecker:
    """Check predicted properties against all relevant BIS standards."""

    def check(self, props: dict) -> BISResult:
        cs  = props.get("compressive_strength_mpa", 0.0)
        sts = props.get("split_tensile_mpa", 0.0)
        den = props.get("density_kgm3", 2000.0)
        wa  = props.get("water_absorption_pct", 5.0)

        # IS 516 - grade assignment
        if   cs >= 30.0: grade = "M30"
        elif cs >= 25.0: grade = "M25"
        elif cs >= 20.0: grade = "M20"
        elif cs >= 15.0: grade = "M15"
        elif cs >= 10.0: grade = "M10"
        else:            grade = "Below_M10"

        is516    = cs >= 10.0
        is1237   = (cs >= IS_1237_MIN_CS_MPA) and (wa <= IS_1237_MAX_WA_PCT)
        is2185_p1= cs >= IS_2185_PT1_MIN_CS_MPA
        is2185_p2= (cs >= IS_2185_PT1_MIN_CS_MPA) and (den <= IS_2185_PT2_MAX_DENSITY) and (wa <= IS_2185_PT2_MAX_WA_PCT)
        is5816   = (sts >= IS_5816_MIN_STS_CS_RATIO * cs) and (sts >= IS_5816_MIN_STS_MPA)
        nbc_struct    = (cs >= NBC_STRUCTURAL_MIN_CS_MPA) and (NBC_STRUCTURAL_MIN_DENSITY <= den <= NBC_STRUCTURAL_MAX_DENSITY)
        nbc_nonstruct = (cs >= NBC_NONSTRUCTURAL_MIN_CS_MPA) and (den <= NBC_NONSTRUCTURAL_MAX_DENSITY)

        standards = [is516, is1237, is2185_p1, is2185_p2, is5816, nbc_struct, nbc_nonstruct]
        n_pass    = sum(standards)
        overall   = n_pass >= 3

        return BISResult(
            is_516_grade          = grade,
            is_516_compliant      = is516,
            is_1237_compliant     = is1237,
            is_1237_cs_margin     = round(cs - IS_1237_MIN_CS_MPA, 3),
            is_1237_wa_margin     = round(IS_1237_MAX_WA_PCT - wa, 3),
            is_2185_pt1_compliant = is2185_p1,
            is_2185_cs_margin     = round(cs - IS_2185_PT1_MIN_CS_MPA, 3),
            is_2185_pt2_compliant = is2185_p2,
            is_5816_compliant     = is5816,
            nbc_structural        = nbc_struct,
            nbc_nonstructural     = nbc_nonstruct,
            bis_overall_pass      = overall,
            n_standards_passed    = n_pass,
        )
