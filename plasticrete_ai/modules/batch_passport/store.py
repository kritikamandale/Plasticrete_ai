"""
SQLite batch passport store.

One plant, a few users. A batch keeps the prediction, the shared mass balance,
and the later cube-test measurements. After three 28-day pairs the store
reports how far this plant sits from the global model.
"""
from __future__ import annotations

import csv
import io
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
_CV_LIMIT = 0.15
_LOCK = threading.Lock()
_EXTRA_COLUMNS = (
    ("lab_name", "TEXT"),
    ("operator", "TEXT"),
    ("cube_size_mm", "REAL"),
    ("n_cubes", "INTEGER"),
    ("cube_values_json", "TEXT"),
    ("cube_std_mpa", "REAL"),
    ("test_standard", "TEXT"),
    ("source", "TEXT"),
    ("due_7d", "TEXT"),
    ("due_28d", "TEXT"),
)


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
            _ensure_columns(conn)
            conn.commit()
        finally:
            conn.close()


def _ensure_columns(conn: sqlite3.Connection) -> None:
    have = {row[1] for row in conn.execute("PRAGMA table_info(batches)")}
    for name, kind in _EXTRA_COLUMNS:
        if name not in have:
            conn.execute(f"ALTER TABLE batches ADD COLUMN {name} {kind}")


def cube_stats(values: list[float]) -> tuple[float, float, float]:
    """Mean, standard deviation, and coefficient of variation of the cube list."""
    if not values:
        raise ValueError("Cube list is empty.")
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    std = variance ** 0.5
    cv = std / mean if mean else float("inf")
    return mean, std, cv


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
    lab_name: str | None = None,
    operator: str | None = None,
    cube_size_mm: float | None = None,
    cube_values_mpa: list[float] | None = None,
    test_standard: str | None = None,
    source: str | None = None,
    confirm_high_cv: bool = False,
    due_7d: str | None = None,
    due_28d: str | None = None,
) -> dict | None:
    current = get_batch(batch_id)
    if current is None:
        return None
    cube_std = None
    n_cubes = None
    cube_json = None
    if cube_values_mpa:
        mean, cube_std, cv = cube_stats([float(value) for value in cube_values_mpa])
        if cv > _CV_LIMIT and not confirm_high_cv:
            raise ValueError(
                "Coefficient of variation is above 0.15. Send confirm_high_cv to store these cubes."
            )
        measured_cs_28d = round(mean, 3)
        n_cubes = len(cube_values_mpa)
        cube_json = json.dumps([float(value) for value in cube_values_mpa])
        cube_std = round(cube_std, 3)
    wrote_measurement = any(value is not None for value in (
        measured_cs_7d, measured_cs_28d, measured_absorption_pct, cube_values_mpa,
    ))
    if wrote_measurement and source is None:
        source = "lab"
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
                    lab_name = COALESCE(?, lab_name),
                    operator = COALESCE(?, operator),
                    cube_size_mm = COALESCE(?, cube_size_mm),
                    n_cubes = COALESCE(?, n_cubes),
                    cube_values_json = COALESCE(?, cube_values_json),
                    cube_std_mpa = COALESCE(?, cube_std_mpa),
                    test_standard = COALESCE(?, test_standard),
                    source = COALESCE(?, source),
                    due_7d = COALESCE(?, due_7d),
                    due_28d = COALESCE(?, due_28d),
                    error_mpa = ?
                WHERE id = ?
                """,
                (
                    cast_date, measured_cs_7d, measured_cs_28d,
                    measured_absorption_pct, notes, lab_name, operator, cube_size_mm,
                    n_cubes, cube_json, cube_std, test_standard, source,
                    due_7d, due_28d, error, batch_id,
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
                      AND COALESCE(source, 'lab') = 'lab'
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


_CSV_FIELDS = [
    "plant_name", "cast_date", "plastic_type", "replacement_pct", "particle_size_mm",
    "wc_ratio", "additive_type", "additive_pct", "curing_temp_c", "curing_days",
    "predicted_cs_mean", "predicted_cs_low", "predicted_cs_high",
    "measured_cs_7d", "measured_cs_28d", "measured_absorption_pct",
    "cube_values_mpa", "lab_name", "operator", "cube_size_mm", "test_standard",
    "source", "model_version", "notes",
]


def export_csv() -> str:
    """Flat export. Predicted columns are the values stored with each batch."""
    init_db()
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for record in list_batches(limit=1000):
        full = get_batch(record["id"])
        if full is None:
            continue
        mix = full["mix_params"]
        cubes = full.get("cube_values_json")
        writer.writerow({
            "plant_name": full["plant_name"],
            "cast_date": full.get("cast_date") or "",
            "plastic_type": mix.get("plastic_type", ""),
            "replacement_pct": mix.get("replacement_pct", ""),
            "particle_size_mm": mix.get("particle_size_mm", ""),
            "wc_ratio": mix.get("wc_ratio", ""),
            "additive_type": mix.get("additive_type", ""),
            "additive_pct": mix.get("additive_pct", ""),
            "curing_temp_c": mix.get("curing_temp_c", ""),
            "curing_days": mix.get("curing_days", ""),
            "predicted_cs_mean": full.get("predicted_cs_mean") if full.get("predicted_cs_mean") is not None else "",
            "predicted_cs_low": full.get("predicted_cs_low") if full.get("predicted_cs_low") is not None else "",
            "predicted_cs_high": full.get("predicted_cs_high") if full.get("predicted_cs_high") is not None else "",
            "measured_cs_7d": full.get("measured_cs_7d") if full.get("measured_cs_7d") is not None else "",
            "measured_cs_28d": full.get("measured_cs_28d") if full.get("measured_cs_28d") is not None else "",
            "measured_absorption_pct": full.get("measured_absorption_pct") if full.get("measured_absorption_pct") is not None else "",
            "cube_values_mpa": cubes or "",
            "lab_name": full.get("lab_name") or "",
            "operator": full.get("operator") or "",
            "cube_size_mm": full.get("cube_size_mm") if full.get("cube_size_mm") is not None else "",
            "test_standard": full.get("test_standard") or "",
            "source": full.get("source") or "",
            "model_version": full.get("model_version") or "",
            "notes": full.get("notes") or "",
        })
    return buffer.getvalue()


def _blank(value: str | None) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    return float(value)


def import_csv(text: str) -> dict:
    """Load lab rows. Example lines and rows without a stored prediction are skipped."""
    reader = csv.DictReader(io.StringIO(text))
    imported = 0
    skipped = 0
    for row in reader:
        blob = " ".join(str(value) for value in row.values())
        if "EXAMPLE ROW" in blob:
            skipped += 1
            continue
        if str(row.get("source") or "").strip().lower() != "lab":
            skipped += 1
            continue
        predicted = _blank(row.get("predicted_cs_mean"))
        if predicted is None:
            skipped += 1
            continue
        mix = {
            "plastic_type": row.get("plastic_type") or "",
            "replacement_pct": _blank(row.get("replacement_pct")),
            "particle_size_mm": _blank(row.get("particle_size_mm")),
            "wc_ratio": _blank(row.get("wc_ratio")),
            "additive_type": row.get("additive_type") or "",
            "additive_pct": _blank(row.get("additive_pct")),
            "curing_temp_c": _blank(row.get("curing_temp_c")),
            "curing_days": int(float(row["curing_days"])) if str(row.get("curing_days") or "").strip() else None,
        }
        low = _blank(row.get("predicted_cs_low"))
        high = _blank(row.get("predicted_cs_high"))
        prediction = {
            "predictions": {
                "compressive_strength_mpa": {
                    "mean": predicted,
                    "ci_90_low": low,
                    "ci_90_high": high,
                }
            }
        }
        created = create_batch(
            mix, prediction, {}, {},
            plant_name=row.get("plant_name") or "Plant",
            cast_date=row.get("cast_date") or None,
        )
        cubes_raw = str(row.get("cube_values_mpa") or "").strip()
        cubes = None
        if cubes_raw.startswith("["):
            cubes = [float(value) for value in json.loads(cubes_raw)]
        update_measurements(
            created["id"],
            measured_cs_7d=_blank(row.get("measured_cs_7d")),
            measured_cs_28d=_blank(row.get("measured_cs_28d")),
            measured_absorption_pct=_blank(row.get("measured_absorption_pct")),
            lab_name=row.get("lab_name") or None,
            operator=row.get("operator") or None,
            cube_size_mm=_blank(row.get("cube_size_mm")),
            cube_values_mpa=cubes,
            test_standard=row.get("test_standard") or None,
            notes=row.get("notes") or None,
            source="lab",
        )
        imported += 1
    if imported == 0:
        raise ValueError("No source=lab rows to import.")
    return {"imported": imported, "skipped": skipped}


def due_batches(today: str) -> list[dict]:
    """Passports whose 7-day or 28-day measurement is still empty and the due date has arrived."""
    init_db()
    with _LOCK:
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT id FROM batches
                WHERE (due_7d IS NOT NULL AND due_7d <= ? AND measured_cs_7d IS NULL)
                   OR (due_28d IS NOT NULL AND due_28d <= ? AND measured_cs_28d IS NULL)
                ORDER BY created_at
                """,
                (today, today),
            ).fetchall()
        finally:
            conn.close()
    return [item for row in rows if (item := get_batch(row["id"])) is not None]
