"""Rank mixes the optimiser already returned, by the width of the M1 interval."""
from __future__ import annotations


def suggest_for_mix(mix: dict, tradeoff_points: list[dict]) -> list[dict]:
    """Predict the current mix with M1, then rank the optimiser points by interval width."""
    from modules.m1_prediction import predict

    result = predict(mix)
    data = result.to_dict() if hasattr(result, "to_dict") else result
    low = (data.get("ci_low") or {}).get("compressive_strength_mpa")
    high = (data.get("ci_high") or {}).get("compressive_strength_mpa")
    prediction = {
        "predictions": {
            "compressive_strength_mpa": {
                "mean": data.get("compressive_strength_mpa"),
                "ci_90_low": low,
                "ci_90_high": high,
            }
        }
    }
    return suggest_next(tradeoff_points, prediction)


def suggest_next(tradeoff_points: list[dict], prediction: dict | None = None) -> list[dict]:
    """Widest interval first. Width is high minus low from the point or the prediction."""
    rows: list[dict] = []
    if prediction:
        props = (prediction.get("predictions") or {}).get("compressive_strength_mpa") or {}
        point = {
            "label": "current_mix",
            "predicted_cs_mpa": props.get("mean"),
            "predicted_cs_low": props.get("ci_90_low"),
            "predicted_cs_high": props.get("ci_90_high"),
            "recipe": None,
        }
        rows.extend(_row(point))
    for point in tradeoff_points:
        rows.extend(_row(point))
    rows.sort(key=lambda item: item["interval_width_mpa"], reverse=True)
    return rows


def _row(point: dict) -> list[dict]:
    mean = point.get("predicted_cs_mpa")
    low = point.get("predicted_cs_low")
    high = point.get("predicted_cs_high")
    if mean is None or low is None or high is None:
        return []
    width = float(high) - float(low)
    return [{
        "label": point.get("label"),
        "predicted_cs_mpa": mean,
        "predicted_cs_low": low,
        "predicted_cs_high": high,
        "interval_width_mpa": round(width, 3),
        "recipe": point.get("recipe"),
        "reason": f"90% interval width is {width:.3f} MPa on this returned point.",
    }]
