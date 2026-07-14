"""IGBC / GRIHA / LEED credit mapper."""
from dataclasses import dataclass


@dataclass
class GreenRatingResult:
    igbc_recycled_content:   int
    igbc_regional_materials: int
    igbc_indoor_air:         int
    igbc_total:              int
    griha_embodied_energy:   int
    griha_waste_management:  int
    griha_total:             int
    leed_bpdo:               int
    leed_construction_waste: int
    leed_total:              int
    total_green_credits:     int


class GreenRater:
    def __init__(self, config: dict):
        gr = config["green_rating"]
        self.igbc_div_min  = gr["igbc_plastic_diversion_min_kg_m3"]
        self.igbc_tc_max   = gr["igbc_tc_threshold_wm"]
        self.griha_co2_min = gr["griha_co2_saving_min_pct"]
        self.griha_div_min = gr["griha_diversion_min_kg_m3"]
        self.leed_pct_min  = gr["leed_replacement_pct_min"]
        self.leed_div_min  = gr["leed_diversion_min_kg_m3"]

    def rate(self, params: dict, props: dict, lca) -> GreenRatingResult:
        div   = lca.plastic_diversion_kg_m3
        co2s  = lca.co2_saving_pct
        tc    = props.get("thermal_conductivity_wm", 1.0)
        pct   = params["replacement_pct"]
        ptype = params["plastic_type"]

        igbc_rc  = int(div  >= self.igbc_div_min)
        igbc_reg = int(ptype in ["PET", "HDPE", "Mixed"])
        igbc_air = int(tc   <= self.igbc_tc_max)
        igbc_tot = igbc_rc + igbc_reg + igbc_air

        griha_e   = int(co2s >= self.griha_co2_min)
        griha_w   = int(div  >= self.griha_div_min)
        griha_tot = griha_e + griha_w

        leed_bpdo = int(pct  >= self.leed_pct_min)
        leed_cw   = int(div  >= self.leed_div_min)
        leed_tot  = leed_bpdo + leed_cw

        total = igbc_tot + griha_tot + leed_tot

        return GreenRatingResult(
            igbc_recycled_content   = igbc_rc,
            igbc_regional_materials = igbc_reg,
            igbc_indoor_air         = igbc_air,
            igbc_total              = igbc_tot,
            griha_embodied_energy   = griha_e,
            griha_waste_management  = griha_w,
            griha_total             = griha_tot,
            leed_bpdo               = leed_bpdo,
            leed_construction_waste = leed_cw,
            leed_total              = leed_tot,
            total_green_credits     = total,
        )
