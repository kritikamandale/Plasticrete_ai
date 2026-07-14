"""
Generate SHAP-guided remediation paths for non-compliant or low-scoring mixes.
Uses rule-based logic derived from known materials science relationships.
These relationships are validated by SHAP global importance from M1:
  - replacement_pct and wc_ratio dominate CS
  - plastic_type dominates thermal_conductivity
  - additive_type moderates the CS drop from plastic inclusion
"""
from dataclasses import dataclass
from typing import Callable, Tuple


@dataclass
class RemediationResult:
    top_negative_factor:  str
    remediation_action_1: str
    remediation_action_2: str
    remediation_action_3: str
    estimated_score_gain: float


# Each rule: (condition_fn, factor, action1, action2, action3, gain)
# condition_fn receives a context dict with cs, wa, den, sts, diversion, co2_saving
_RuleT = Tuple[Callable[[dict], bool], str, str, str, str, float]


class RemediationAdvisor:

    RULES: list[_RuleT] = [
        # BIS 1237 floor tile failures - both CS and WA failing
        (lambda c: c["cs"] < 30 and c["wa"] > 1.0,
         "water_absorption_pct",
         "Reduce wc_ratio from current to 0.40 to cut water absorption",
         "Increase additive to 15% silica_fume to densify matrix",
         "Reduce replacement_pct by 5-10% to boost CS above 30 MPa", 8.0),

        # BIS 1237 floor tile failures - CS only
        (lambda c: c["cs"] < 30 and c["wa"] <= 1.0,
         "compressive_strength_mpa",
         "Reduce replacement_pct by 5% (each 5% drop -> +1.5 MPa CS)",
         "Add 10% silica_fume: pozzolanic reaction adds 2-4 MPa",
         "Reduce wc_ratio to 0.40 (each 0.05 drop -> +2 MPa CS)", 9.0),

        # NBC 2016 structural failures
        (lambda c: c["cs"] < 20 and c["den"] < 1800,
         "density_kgm3",
         "Reduce replacement_pct to increase concrete density above 1800",
         "Switch plastic_type from LDPE/PP to PET (higher density 1380)",
         "Add fly_ash additive: denser matrix without major CS loss", 7.5),

        # Low plastic diversion score
        (lambda c: c["diversion"] < 50,
         "replacement_pct",
         "Increase replacement_pct to 15%: diversion reaches ~83 kg/m3",
         "Switch to Mixed plastic type for higher volume at lower cost",
         "Use larger particle_size to maintain workability at higher pct", 6.0),

        # Low carbon score
        (lambda c: c["co2_saving"] < 10,
         "additive_type",
         "Switch additive from none to fly_ash (EF=0.004 vs cement 0.872)",
         "Increase replacement_pct by 5%: each 5% -> 10-15 kg CO2e saving",
         "Replace 20% cement with GGBS (EF=0.083 vs OPC 0.872)", 10.0),

        # IS 5816 tensile failures
        (lambda c: c["sts"] < 0.10 * c["cs"],
         "split_tensile_mpa",
         "Add fibres additive at 5-10%: fibres add 0.5-1.5 MPa STS",
         "Reduce wc_ratio to 0.40: lower w/c improves tensile strength",
         "Use PET or HDPE fibres specifically: better bond than granular", 5.0),
    ]

    def advise(self, params: dict, props: dict, lca, bis, score) -> RemediationResult:
        context = {
            "cs":        props.get("compressive_strength_mpa", 0),
            "wa":        props.get("water_absorption_pct", 5),
            "den":       props.get("density_kgm3", 2000),
            "sts":       props.get("split_tensile_mpa", 0),
            "diversion": lca.plastic_diversion_kg_m3,
            "co2_saving": lca.co2_saving_pct,
        }

        matched_rule = None
        for cond_fn, factor, a1, a2, a3, gain in self.RULES:
            try:
                if cond_fn(context):
                    matched_rule = (factor, a1, a2, a3, gain)
                    break
            except Exception:
                continue

        if matched_rule is None:
            matched_rule = (
                "sustainability_score",
                f"Increase replacement_pct from {params['replacement_pct']}% to {min(params['replacement_pct']+5, 40)}%",
                "Switch additive_type to silica_fume if not already",
                "Extend curing_days to 28 for maximum strength gain",
                3.0,
            )

        factor, a1, a2, a3, gain = matched_rule
        return RemediationResult(
            top_negative_factor  = factor,
            remediation_action_1 = a1,
            remediation_action_2 = a2,
            remediation_action_3 = a3,
            estimated_score_gain = gain,
        )
