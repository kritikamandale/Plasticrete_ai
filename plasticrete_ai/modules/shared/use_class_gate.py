"""
Allow a product only when its own standard clears on the conservative
side of the 90% interval.

Structural concrete never returns ``allowed``. A mean that clears while the
bound does not returns ``verification_batch`` ("Cast one verification batch").
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_GATE_PATH = Path(__file__).resolve().parents[2] / "data" / "external" / "use_class_gates.json"

_ALLOWED = "allowed"
_VERIFY = "verification_batch"
_LAB = "lab_trial"
_REFUSED = "refused"


@lru_cache(maxsize=1)
def load_gates() -> dict:
    with open(_GATE_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def _num(props: dict | None, key: str):
    if not props:
        return None
    value = props.get(key)
    if value is None:
        return None
    return float(value)


def _class_by_id() -> dict:
    return {row["id"]: row for row in load_gates()["classes"]}


def application_class(application: str) -> str | None:
    for row in load_gates()["classes"]:
        if application in row["applications"]:
            return row["id"]
    return None


def _clears(spec: dict, cs: float | None, wa: float | None, density: float | None, *, bound: bool) -> bool:
    if cs is None:
        return False
    if cs < float(spec["cs_min_mpa"]):
        return False
    wa_max = spec.get("wa_max_pct")
    if wa_max is not None:
        if wa is None:
            return False
        if wa > float(wa_max):
            return False
    dmin = spec.get("density_min_kgm3")
    dmax = spec.get("density_max_kgm3")
    if dmin is not None or dmax is not None:
        if density is None:
            return False
        if dmin is not None and density < float(dmin):
            return False
        if dmax is not None and density > float(dmax):
            return False
    return True


def _status_for_spec(
    spec: dict,
    mean: dict,
    low: dict | None,
    high: dict | None,
) -> tuple[str, str]:
    interval = low is not None and high is not None
    cs_mean = _num(mean, "compressive_strength_mpa")
    wa_mean = _num(mean, "water_absorption_pct")
    den_mean = _num(mean, "density_kgm3")
    clears_mean = _clears(spec, cs_mean, wa_mean, den_mean, bound=False)

    structural = bool(spec.get("structural"))
    label = spec["standard"]

    if not interval:
        if structural and clears_mean:
            return _LAB, (
                f"{label}: the 90% interval was not supplied. "
                "Screen for a lab trial. This is not a certificate."
            )
        if clears_mean:
            return _VERIFY, (
                f"{label}: the 90% interval was not supplied. Cast one verification batch."
            )
        return _REFUSED, f"{label}: the predicted mean does not clear this standard."

    # Conservative side: lower strength, lower density floor, upper absorption and density cap.
    cs_low = _num(low, "compressive_strength_mpa")
    wa_high = _num(high, "water_absorption_pct")
    den_low = _num(low, "density_kgm3")
    den_high = _num(high, "density_kgm3")
    density_for_bound = den_low
    if spec.get("density_max_kgm3") is not None:
        density_for_bound = den_high if den_low is None else den_high
        # A single density figure cannot sit on both sides. Check the two bounds separately.
    clears_bound = _clears(spec, cs_low, wa_high, den_low, bound=True)
    if spec.get("density_max_kgm3") is not None and clears_bound:
        if den_high is None or den_high > float(spec["density_max_kgm3"]):
            clears_bound = False
    if spec.get("density_min_kgm3") is not None and den_low is None:
        clears_bound = False

    if clears_bound and structural:
        return _LAB, (
            f"{label}: the lower confidence bound clears the grade. "
            "Screen for a lab trial. This is not a certificate."
        )
    if clears_bound:
        return _ALLOWED, f"{label}: the lower confidence bound clears this standard."
    if clears_mean:
        return _VERIFY, (
            f"{label}: cast one verification batch. The 90% interval crosses the grade line."
        )
    return _REFUSED, f"{label}: this mix does not clear the standard."


def evaluate_classes(
    mean: dict,
    ci_low: dict | None = None,
    ci_high: dict | None = None,
) -> list[dict]:
    """One gate result per use class, in table order."""
    results = []
    for spec in load_gates()["classes"]:
        status, message = _status_for_spec(spec, mean, ci_low, ci_high)
        results.append({
            "id": spec["id"],
            "label": spec["label"],
            "standard": spec["standard"],
            "status": status,
            "message": message,
            "clause": spec["clause"],
            "cs_min_mpa": spec["cs_min_mpa"],
            "wa_max_pct": spec.get("wa_max_pct"),
            "structural": bool(spec.get("structural")),
            "applications": list(spec["applications"]),
        })
    return results


def status_for_application(application: str, gates: list[dict]) -> tuple[str, str]:
    class_id = application_class(application)
    if class_id is None:
        return _REFUSED, "No use-class standard is configured for this product."
    for gate in gates:
        if gate["id"] == class_id:
            return gate["status"], gate["message"]
    return _REFUSED, "No use-class standard is configured for this product."
