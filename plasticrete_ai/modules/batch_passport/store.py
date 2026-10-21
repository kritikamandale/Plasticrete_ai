"""
SQLite batch passport store.

One plant, a few users. A batch keeps the prediction, the shared mass balance,
and the later cube-test measurements. After three 28-day pairs the store
reports how far this plant sits from the global model.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DB_PATH = Path(os.environ.get("BATCH_DB_PATH", str(_ROOT / "data" / "batches" / "batches.sqlite")))
_PHOTO_DIR = _DB_PATH.parent / "photos"
MODEL_VERSION = "m1-ensemble evaluation_report.json compressive R2 0.9104"
_MIN_PAIRS = 3
_LOCK = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _connect() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _LOCK:
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS batches (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    plant_name TEXT NOT NULL,
                    mix_json TEXT NOT NULL,
                    prediction_json TEXT NOT NULL,
                    score_json TEXT NOT NULL,
                    recommendation_json TEXT NOT NULL,
                    predicted_cs_mean REAL,
                    predicted_cs_low REAL,
                    predicted_cs_high REAL,
                    cast_date TEXT,
                    measured_cs_7d REAL,
                    measured_cs_28d REAL,
                    measured_absorption_pct REAL,
                    cube_photo_path TEXT,
                    error_mpa REAL,
                    model_version TEXT NOT NULL,
                    notes TEXT
                )
                """
            )
            conn.commit()
        finally:
            conn.close()


def public_batch_url(batch_id: str) -> str:
    base = os.environ.get("PUBLIC_APP_URL", "http://localhost:5173").rstrip("/")
    return f"{base}/batch/{batch_id}"


def _prediction_strength(prediction: dict) -> tuple[float | None, float | None, float | None]:
    preds = (prediction or {}).get("predictions") or {}
    cs = preds.get("compressive_strength_mpa") or {}
    return cs.get("mean"), cs.get("ci_90_low"), cs.get("ci_90_high")


def _row_to_dict(row: sqlite3.Row) -> dict:
    item = dict(row)
    item["mix_params"] = json.loads(item.pop("mix_json"))
    item["prediction"] = json.loads(item.pop("prediction_json"))
    item["score"] = json.loads(item.pop("score_json"))
    item["recommendation"] = json.loads(item.pop("recommendation_json"))
    item["qr_url"] = public_batch_url(item["id"])
    item["calibration"] = calibration(item["plant_name"], exclude_id=None, _already_open=True)
    return item


def create_batch(
    mix_params: dict,
    prediction: dict,
    score: dict,
    recommendation: dict,
    plant_name: str = "Plant",
    cast_date: str | None = None,
) -> dict:
    init_db()
    batch_id = "B" + uuid.uuid4().hex[:8].upper()
    mean, low, high = _prediction_strength(prediction)
    with _LOCK:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO batches (
                    id, created_at, plant_name, mix_json, prediction_json, score_json,
                    recommendation_json, predicted_cs_mean, predicted_cs_low, predicted_cs_high,
                    cast_date, model_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id, _now(), plant_name.strip() or "Plant",
                    json.dumps(mix_params), json.dumps(prediction), json.dumps(score),
                    json.dumps(recommendation), mean, low, high, cast_date, MODEL_VERSION,
                ),
            )
            conn.commit()
        finally:
            conn.close()
    return get_batch(batch_id)


def list_batches(limit: int = 50) -> list[dict]:
    init_db()
    with _LOCK:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT * FROM batches ORDER BY created_at DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
        finally:
            conn.close()
    return [_public_summary(row) for row in rows]


def _public_summary(row: sqlite3.Row) -> dict:
    item = dict(row)
    mix = json.loads(item["mix_json"])
    return {
        "id": item["id"],
        "created_at": item["created_at"],
        "plant_name": item["plant_name"],
        "plastic_type": mix.get("plastic_type"),
        "replacement_pct": mix.get("replacement_pct"),
        "predicted_cs_mean": item["predicted_cs_mean"],
        "predicted_cs_low": item["predicted_cs_low"],
        "predicted_cs_high": item["predicted_cs_high"],
        "measured_cs_7d": item["measured_cs_7d"],
        "measured_cs_28d": item["measured_cs_28d"],
        "measured_absorption_pct": item["measured_absorption_pct"],
        "error_mpa": item["error_mpa"],
        "cast_date": item["cast_date"],
        "model_version": item["model_version"],
        "qr_url": public_batch_url(item["id"]),
    }


def get_batch(batch_id: str) -> dict | None:
    init_db()
    with _LOCK:
        conn = _connect()
        try:
            row = conn.execute("SELECT * FROM batches WHERE id = ?", (batch_id,)).fetchone()
        finally:
            conn.close()
    if row is None:
        return None
    item = dict(row)
    item["mix_params"] = json.loads(item.pop("mix_json"))
    item["prediction"] = json.loads(item.pop("prediction_json"))
    item["score"] = json.loads(item.pop("score_json"))
    item["recommendation"] = json.loads(item.pop("recommendation_json"))
    item["qr_url"] = public_batch_url(item["id"])
    item["calibration"] = calibration(item["plant_name"])
    return item


def update_measurements(
    batch_id: str,
    cast_date: str | None = None,
    measured_cs_7d: float | None = None,
    measured_cs_28d: float | None = None,
    measured_absorption_pct: float | None = None,
    notes: str | None = None,
) -> dict | None:
    current = get_batch(batch_id)
    if current is None:
        return None
    error = current["error_mpa"]
    if measured_cs_28d is not None and current["predicted_cs_mean"] is not None:
        error = round(float(measured_cs_28d) - float(current["predicted_cs_mean"]), 3)
    with _LOCK:
        conn = _connect()
        try:
            conn.execute(
                """
                UPDATE batches SET
                    cast_date = COALESCE(?, cast_date),
                    measured_cs_7d = COALESCE(?, measured_cs_7d),
                    measured_cs_28d = COALESCE(?, measured_cs_28d),
                    measured_absorption_pct = COALESCE(?, measured_absorption_pct),
                    notes = COALESCE(?, notes),
                    error_mpa = ?
                WHERE id = ?
                """,
                (
                    cast_date, measured_cs_7d, measured_cs_28d,
                    measured_absorption_pct, notes, error, batch_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()
    return get_batch(batch_id)


def save_photo(batch_id: str, data: bytes, suffix: str) -> dict | None:
    if get_batch(batch_id) is None:
        return None
    _PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    path = _PHOTO_DIR / f"{batch_id}{suffix}"
    path.write_bytes(data)
    with _LOCK:
        conn = _connect()
        try:
            conn.execute(
                "UPDATE batches SET cube_photo_path = ? WHERE id = ?",
                (str(path), batch_id),
            )
            conn.commit()
        finally:
            conn.close()
    return get_batch(batch_id)


def calibration(plant_name: str, exclude_id: str | None = None, _already_open: bool = False) -> dict:
    """Mean (measured 28-day − predicted mean) once the plant has three pairs."""
    init_db()
    with _LOCK:
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT id, predicted_cs_mean, predicted_cs_low, predicted_cs_high,
                       measured_cs_28d, error_mpa
                FROM batches
                WHERE plant_name = ? AND measured_cs_28d IS NOT NULL
                      AND predicted_cs_mean IS NOT NULL
                """,
                (plant_name,),
            ).fetchall()
        finally:
            conn.close()
    pairs = [dict(row) for row in rows if row["id"] != exclude_id]
    errors = [float(row["error_mpa"] if row["error_mpa"] is not None
                    else float(row["measured_cs_28d"]) - float(row["predicted_cs_mean"]))
              for row in pairs]
    ready = len(errors) >= _MIN_PAIRS
    if not errors:
        mean_error = 0.0
        std = 0.0
    else:
        mean_error = sum(errors) / len(errors)
        variance = sum((err - mean_error) ** 2 for err in errors) / len(errors)
        std = variance ** 0.5
    if mean_error < -0.05:
        direction = f"{abs(mean_error):.1f} MPa under"
    elif mean_error > 0.05:
        direction = f"{mean_error:.1f} MPa over"
    else:
        direction = "in line with"
    message = (
        f"This plant's mixes run {direction} the global model (n={len(errors)})."
        if ready else
        f"Local calibration needs {_MIN_PAIRS} cube pairs. This plant has {len(errors)}."
    )
    return {
        "ready": ready,
        "n_pairs": len(errors),
        "mean_error_mpa": round(mean_error, 2) if errors else None,
        "residual_std_mpa": round(std, 2) if ready else None,
        "message": message,
    }
