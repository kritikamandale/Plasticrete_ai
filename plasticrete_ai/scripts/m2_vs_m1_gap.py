"""Compare frozen M2 surrogate JSON files with a live m1.predict call.

Does not edit the JSON files. The gap is the surrogate-versus-ensemble difference.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import modules.m1_prediction as m1  # noqa: E402


def _mix(payload: dict, key: str) -> dict:
    mix = dict(payload[key])
    mix["curing_days"] = int(mix["curing_days"])
    return mix


def main() -> None:
    bo = json.loads((ROOT / "models" / "m2" / "bo_demo_result.json").read_text(encoding="utf-8"))
    sens = json.loads((ROOT / "models" / "m2" / "sensitivity_analysis.json").read_text(encoding="utf-8"))
    bo_mix = _mix(bo, "best_mix")
    sens_mix = _mix(sens, "base_mix")
    config = yaml.safe_load((ROOT / "configs" / "m1_config.yaml").read_text(encoding="utf-8"))
    m1.load_ensemble(str(ROOT / "models" / "m1"), config)
    bo_live = m1.predict(bo_mix)
    same_mix = bo_mix == sens_mix
    bo_surrogate = float(bo["predicted_properties"]["compressive_strength_mpa"])
    sens_surrogate = float(sens["base_cs_mpa"])
    live = bo_live.compressive_strength_mpa
    report = {
        "same_mix_in_both_files": same_mix,
        "bo_demo_result_cs_mpa": bo_surrogate,
        "sensitivity_analysis_cs_mpa": sens_surrogate,
        "surrogate_file_gap_mpa": abs(bo_surrogate - sens_surrogate),
        "m1_ensemble_cs_mpa": live,
        "m1_ci_90_low": None if live is None else bo_live.ci_low.get("compressive_strength_mpa"),
        "m1_ci_90_high": None if live is None else bo_live.ci_high.get("compressive_strength_mpa"),
        "bo_vs_m1_abs_gap_mpa": None if live is None else abs(bo_surrogate - live),
        "sensitivity_vs_m1_abs_gap_mpa": None if live is None else abs(sens_surrogate - live),
        "label": "surrogate vs ensemble gap",
        "note": "bo_demo_result.json and sensitivity_analysis.json are surrogate-era snapshots. The live optimiser calls M1 and sets prediction_source to m1.",
        "mix": bo_mix,
    }
    out = ROOT / "reports" / "m2_vs_m1_gap.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
