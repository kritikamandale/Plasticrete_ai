"""Compare the M4 classifier's first choice with the use-class gate.

Properties come from m1.predict. Mixes are a fixed list, not a random draw.
The report is agreement with the rule, not accuracy against a lab.
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
from modules.m4_recommendation import load_models, recommend  # noqa: E402
from modules.m4_recommendation.model import classifiers  # noqa: E402
from modules.m4_recommendation.utils.features import build_feature_vector  # noqa: E402
from modules.shared.use_class_gate import status_for_application, evaluate_classes  # noqa: E402

# Fixed probe mixes inside the input ranges in schema.INPUT_RANGES.
PROBE_MIXES = [
    {"plastic_type": "PET", "replacement_pct": 15.0, "particle_size_mm": 4.0, "wc_ratio": 0.45, "additive_type": "fly_ash", "additive_pct": 10.0, "curing_temp_c": 27.0, "curing_days": 28},
    {"plastic_type": "HDPE", "replacement_pct": 20.0, "particle_size_mm": 6.0, "wc_ratio": 0.50, "additive_type": "silica_fume", "additive_pct": 8.0, "curing_temp_c": 27.0, "curing_days": 28},
    {"plastic_type": "LDPE", "replacement_pct": 30.0, "particle_size_mm": 2.0, "wc_ratio": 0.55, "additive_type": "none", "additive_pct": 0.0, "curing_temp_c": 27.0, "curing_days": 28},
    {"plastic_type": "PP", "replacement_pct": 10.0, "particle_size_mm": 4.0, "wc_ratio": 0.40, "additive_type": "fly_ash", "additive_pct": 15.0, "curing_temp_c": 27.0, "curing_days": 28},
    {"plastic_type": "PVC", "replacement_pct": 5.0, "particle_size_mm": 8.0, "wc_ratio": 0.42, "additive_type": "fibres", "additive_pct": 5.0, "curing_temp_c": 27.0, "curing_days": 28},
    {"plastic_type": "Mixed", "replacement_pct": 25.0, "particle_size_mm": 4.0, "wc_ratio": 0.48, "additive_type": "fly_ash", "additive_pct": 10.0, "curing_temp_c": 27.0, "curing_days": 28},
]


def classifier_primary(mix: dict, props: dict) -> str:
    X = classifiers.scaler.transform(build_feature_vector(mix, props))
    pred = classifiers.rf_primary.predict(X)[0]
    return str(classifiers.label_enc.inverse_transform([pred])[0])


def main() -> None:
    config = yaml.safe_load((ROOT / "configs" / "m1_config.yaml").read_text(encoding="utf-8"))
    m1.load_ensemble(str(ROOT / "models" / "m1"), config)
    load_models(str(ROOT / "models" / "m4"))
    rows = []
    for mix in PROBE_MIXES:
        result = m1.predict(mix)
        props = {name: getattr(result, name) for name in (
            "compressive_strength_mpa", "flexural_strength_mpa", "split_tensile_mpa",
            "density_kgm3", "water_absorption_pct", "thermal_conductivity_wm", "durability_index",
        )}
        props = {k: v for k, v in props.items() if v is not None}
        gates = evaluate_classes(props, result.ci_low, result.ci_high)
        raw = classifier_primary(mix, props)
        raw_status, raw_message = status_for_application(raw, gates)
        advised = recommend(mix, props, ci_low=result.ci_low, ci_high=result.ci_high)
        rows.append({
            "mix": mix,
            "classifier_primary": raw,
            "classifier_gate_status": raw_status,
            "classifier_gate_message": raw_message,
            "authoritative_primary": advised.primary_application,
            "authoritative_gate_status": advised.primary_gate_status,
            "disagreed": raw != advised.primary_application,
            "note": "Disagreement means the gate replaced the classifier. The gate is the verdict.",
        })
    disagreed = sum(1 for row in rows if row["disagreed"])
    report = {
        "n": len(rows),
        "disagreement_count": disagreed,
        "disagreement_rate": disagreed / len(rows) if rows else None,
        "label": "agreement with the use-class rule, not accuracy against ground truth",
        "rows": rows,
    }
    out = ROOT / "reports" / "rules_vs_model.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {out} disagreement {disagreed}/{len(rows)}")


if __name__ == "__main__":
    main()
