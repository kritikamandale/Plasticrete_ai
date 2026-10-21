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


def test_photo_round_trip(db_path):
    payload = _payload()
    created = store.create_batch(
        payload["mix"], payload["prediction"], payload["score"], payload["recommendation"],
    )
    saved = store.save_photo(created["id"], b"not-a-real-image", ".jpg")
    assert saved["cube_photo_path"]
    assert os.path.exists(saved["cube_photo_path"])
