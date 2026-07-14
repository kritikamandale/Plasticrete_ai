"""
Composite sustainability score (0-100) with component breakdown.

Component normalisation:
  carbon (30 pts):          clip((co2_saving_pct - (-50)) / 130, 0, 1)
  plastic_diversion (25 pts): clip(plastic_diversion_kg_m3 / 200, 0, 1)
  recycled_content (20 pts):  clip(replacement_pct / 40, 0, 1)
  bis_compliance (15 pts):    n_standards_passed / 7
  green_rating (10 pts):      total_green_credits / 7
"""
import numpy as np
from dataclasses import dataclass


@dataclass
class ScoreResult:
    score_carbon_component:       float
    score_plastic_diversion_comp: float
    score_recycled_content_comp:  float
    score_bis_compliance_comp:    float
    score_green_rating_comp:      float
    sustainability_score:         float
    sustainability_grade:         str


class ScoreAggregator:
    def __init__(self, config: dict):
        w = config["score_weights"]
        self.w_carbon   = w["carbon_component"]
        self.w_div      = w["plastic_diversion_comp"]
        self.w_recycled = w["recycled_content_comp"]
        self.w_bis      = w["bis_compliance_comp"]
        self.w_green    = w["green_rating_comp"]

    def score(self, params, lca, bis, green) -> ScoreResult:
        n_carbon   = np.clip((lca.co2_saving_pct - (-50)) / 130, 0, 1)
        n_div      = np.clip(lca.plastic_diversion_kg_m3 / 200,  0, 1)
        n_recycled = np.clip(params["replacement_pct"] / 40,      0, 1)
        n_bis      = bis.n_standards_passed / 7
        n_green    = green.total_green_credits / 7

        c_carbon   = round(float(n_carbon   * self.w_carbon),   3)
        c_div      = round(float(n_div      * self.w_div),      3)
        c_recycled = round(float(n_recycled * self.w_recycled), 3)
        c_bis      = round(float(n_bis      * self.w_bis),      3)
        c_green    = round(float(n_green    * self.w_green),    3)

        total = round(c_carbon + c_div + c_recycled + c_bis + c_green, 2)

        if   total >= 80: grade = "A"
        elif total >= 60: grade = "B"
        elif total >= 40: grade = "C"
        else:             grade = "D"

        return ScoreResult(
            score_carbon_component       = c_carbon,
            score_plastic_diversion_comp = c_div,
            score_recycled_content_comp  = c_recycled,
            score_bis_compliance_comp    = c_bis,
            score_green_rating_comp      = c_green,
            sustainability_score         = total,
            sustainability_grade         = grade,
        )
