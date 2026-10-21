"""Use-class gates follow the lower confidence bound, not a blended pass."""
from modules.shared.use_class_gate import evaluate_classes, status_for_application


def _mean(**kwargs):
    base = {
        "compressive_strength_mpa": 32.0,
        "water_absorption_pct": 4.0,
        "density_kgm3": 2200.0,
    }
    base.update(kwargs)
    return base


def _by_id(gates):
    return {gate["id"]: gate for gate in gates}


def test_interval_crossing_the_paver_line_asks_for_a_verification_batch():
    gates = _by_id(evaluate_classes(
        _mean(),
        {"compressive_strength_mpa": 28.0, "water_absorption_pct": 3.0, "density_kgm3": 2100.0},
        {"compressive_strength_mpa": 36.0, "water_absorption_pct": 5.0, "density_kgm3": 2300.0},
    ))
    assert gates["paver"]["status"] == "verification_batch"
    assert "Cast one verification batch" in gates["paver"]["message"] or "cast one verification batch" in gates["paver"]["message"]
    assert gates["hollow_block"]["status"] == "allowed"
    assert gates["solid_block"]["status"] == "allowed"
    assert gates["structural"]["status"] == "lab_trial"
    assert gates["structural"]["status"] != "allowed"


def test_paver_is_allowed_only_when_the_lower_bound_clears():
    gates = _by_id(evaluate_classes(
        _mean(compressive_strength_mpa=34.0),
        {"compressive_strength_mpa": 31.0, "water_absorption_pct": 3.5, "density_kgm3": 2100.0},
        {"compressive_strength_mpa": 37.0, "water_absorption_pct": 5.5, "density_kgm3": 2300.0},
    ))
    assert gates["paver"]["status"] == "allowed"


def test_mean_below_the_paver_grade_is_refused():
    gates = _by_id(evaluate_classes(
        _mean(compressive_strength_mpa=25.0),
        {"compressive_strength_mpa": 22.0, "water_absorption_pct": 3.0, "density_kgm3": 2100.0},
        {"compressive_strength_mpa": 28.0, "water_absorption_pct": 5.0, "density_kgm3": 2300.0},
    ))
    assert gates["paver"]["status"] == "refused"
    assert gates["structural"]["status"] == "lab_trial"


def test_missing_interval_never_marks_a_product_allowed():
    gates = _by_id(evaluate_classes(_mean()))
    assert gates["paver"]["status"] == "verification_batch"
    assert gates["hollow_block"]["status"] == "verification_batch"
    assert gates["structural"]["status"] == "lab_trial"


def test_absorption_upper_bound_can_block_a_paver():
    gates = _by_id(evaluate_classes(
        _mean(water_absorption_pct=5.0),
        {"compressive_strength_mpa": 31.0, "water_absorption_pct": 4.0, "density_kgm3": 2100.0},
        {"compressive_strength_mpa": 36.0, "water_absorption_pct": 7.5, "density_kgm3": 2300.0},
    ))
    assert gates["paver"]["status"] == "verification_batch"


def test_application_lookup_uses_the_class_gate():
    gates = evaluate_classes(
        _mean(),
        {"compressive_strength_mpa": 28.0, "water_absorption_pct": 3.0, "density_kgm3": 2100.0},
        {"compressive_strength_mpa": 36.0, "water_absorption_pct": 5.0, "density_kgm3": 2300.0},
    )
    status, _message = status_for_application("paving_block_heavy", gates)
    assert status == "verification_batch"
    status, message = status_for_application("thermal_insulation_panel", gates)
    assert status == "refused"
    assert "No use-class standard" in message
