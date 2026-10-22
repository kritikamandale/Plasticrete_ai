"""Saved batches keep a prediction and the later cube measurements."""
from __future__ import annotations

import os

import pytest

from modules.batch_passport import store


@pytest.fixture()
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "batches.sqlite"
    monkeypatch.setenv("BATCH_DB_PATH", str(path))
    monkeypatch.setattr(store, "_DB_PATH", path)
    monkeypatch.setattr(store, "_PHOTO_DIR", tmp_path / "photos")
    return path


def _payload(mean=30.0, low=27.0, high=33.0):
    return {
        "mix": {"plastic_type": "PET", "replacement_pct": 15, "wc_ratio": 0.45,
                "additive_type": "fly_ash", "additive_pct": 10},
        "prediction": {
            "predictions": {
                "compressive_strength_mpa": {"mean": mean, "ci_90_low": low, "ci_90_high": high},
            }
        },
        "score": {"mass_balance": {"plastic_kg_m3": 53.12}, "use_class_gates": []},
        "recommendation": {"primary_application": "hollow_concrete_block"},
    }


def test_batch_records_prediction_and_later_error(db_path):
    payload = _payload()
    created = store.create_batch(
        payload["mix"], payload["prediction"], payload["score"], payload["recommendation"],
        plant_name="Yard A", cast_date="2026-03-01",
    )
    assert created["id"].startswith("B")
    assert created["predicted_cs_mean"] == 30.0
    assert created["qr_url"].endswith("/batch/" + created["id"])
    assert created["model_version"] == store.MODEL_VERSION
    assert created["measured_cs_28d"] is None

    updated = store.update_measurements(created["id"], measured_cs_7d=22.0, measured_cs_28d=27.6)
    assert updated["error_mpa"] == pytest.approx(-2.4)
    assert updated["measured_cs_7d"] == 22.0


def test_calibration_starts_after_three_pairs(db_path):
    ids = []
    for mean, measured in ((30.0, 28.0), (32.0, 29.0), (28.0, 25.6)):
        payload = _payload(mean=mean, low=mean - 2, high=mean + 2)
        created = store.create_batch(
            payload["mix"], payload["prediction"], payload["score"], payload["recommendation"],
            plant_name="Yard A",
        )
        store.update_measurements(created["id"], measured_cs_28d=measured)
        ids.append(created["id"])

    early = store.calibration("Yard A")
    assert early["ready"] is True
    assert early["n_pairs"] == 3
    assert early["mean_error_mpa"] < 0
    assert "under" in early["message"]

    fresh = store.calibration("Yard B")
    assert fresh["ready"] is False
    assert fresh["n_pairs"] == 0


def test_high_cv_needs_confirmation_and_demo_rows_skip_calibration(db_path):
    payload = _payload()
    created = store.create_batch(
        payload["mix"], payload["prediction"], payload["score"], payload["recommendation"],
        plant_name="Yard A",
    )
    with pytest.raises(ValueError):
        store.update_measurements(created["id"], cube_values_mpa=[10.0, 20.0, 30.0])
    stored = store.update_measurements(
        created["id"], cube_values_mpa=[28.0, 28.2, 27.8], lab_name="Site lab",
    )
    assert stored["source"] == "lab"
    assert stored["measured_cs_28d"] == pytest.approx(28.0)
    assert stored["n_cubes"] == 3

    for _ in range(3):
        demo = store.create_batch(
            payload["mix"], payload["prediction"], payload["score"], payload["recommendation"],
            plant_name="Yard Demo",
        )
        store.update_measurements(demo["id"], measured_cs_28d=10.0, source="demo")
    assert store.calibration("Yard Demo")["n_pairs"] == 0


def test_import_skips_example_rows_and_requires_a_lab_row(db_path):
    example = "plant_name,predicted_cs_mean,source,notes\nYard,30,lab,EXAMPLE ROW (not real)\n"
    with pytest.raises(ValueError):
        store.import_csv(example)
    real = (
        "plant_name,predicted_cs_mean,predicted_cs_low,predicted_cs_high,"
        "measured_cs_28d,source,plastic_type\n"
        "Yard A,30,27,33,28.5,lab,PET\n"
    )
    result = store.import_csv(real)
    assert result["imported"] == 1
    assert store.calibration("Yard A")["n_pairs"] == 1


def test_suggest_ranks_by_returned_interval_width():
    from modules.batch_passport.suggest import suggest_next
    rows = suggest_next([
        {"label": "narrow", "predicted_cs_mpa": 30, "predicted_cs_low": 28, "predicted_cs_high": 32},
        {"label": "wide", "predicted_cs_mpa": 20, "predicted_cs_low": 5, "predicted_cs_high": 40},
    ])
    assert rows[0]["label"] == "wide"
    assert "90% interval width" in rows[0]["reason"]


def test_scheduler_opens_only_when_the_gate_asks_for_a_cube(db_path):
    from modules.batch_passport.scheduler import open_if_gate_requires_cube
    payload = _payload()
    refused = open_if_gate_requires_cube(
        payload["mix"], payload["prediction"],
        {"use_class_gates": [{"status": "refused"}]},
        payload["recommendation"], cast_date="2026-03-01",
    )
    assert refused is None
    opened = open_if_gate_requires_cube(
        payload["mix"], payload["prediction"],
        {"use_class_gates": [{"status": "verification_batch"}]},
        payload["recommendation"], plant_name="Yard A", cast_date="2026-03-01",
    )
    assert opened["due_7d"] == "2026-03-08"
    assert opened["due_28d"] == "2026-03-29"
    assert store.due_batches("2026-03-08")[0]["id"] == opened["id"]


def test_photo_round_trip(db_path):
    payload = _payload()
    created = store.create_batch(
        payload["mix"], payload["prediction"], payload["score"], payload["recommendation"],
    )
    saved = store.save_photo(created["id"], b"not-a-real-image", ".jpg")
    assert saved["cube_photo_path"]
    assert os.path.exists(saved["cube_photo_path"])
