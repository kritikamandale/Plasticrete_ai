"""Open a passport when a gate asks for a cube, and list the ones that are due.

Dates are calendar offsets from the cast date. No hosted model is called.
"""
from __future__ import annotations

from datetime import date, timedelta

from modules.batch_passport import store

_OPEN = ("verification_batch", "lab_trial")


def due_dates(cast_date: str) -> tuple[str, str]:
    day = date.fromisoformat(cast_date)
    return (day + timedelta(days=7)).isoformat(), (day + timedelta(days=28)).isoformat()


def open_if_gate_requires_cube(
    mix_params: dict,
    prediction: dict,
    score: dict,
    recommendation: dict,
    plant_name: str = "Plant",
    cast_date: str | None = None,
) -> dict | None:
    """Create a passport only when a gate status is verification_batch or lab_trial."""
    gates = score.get("use_class_gates") or []
    if not any(gate.get("status") in _OPEN for gate in gates):
        return None
    cast = cast_date or date.today().isoformat()
    day7, day28 = due_dates(cast)
    created = store.create_batch(
        mix_params, prediction, score, recommendation,
        plant_name=plant_name, cast_date=cast,
    )
    return store.update_measurements(created["id"], due_7d=day7, due_28d=day28)
