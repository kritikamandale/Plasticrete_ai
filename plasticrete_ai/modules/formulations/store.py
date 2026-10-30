"""
SQLite store for PlastiCrete formulations, versioning, and module pipeline results.
Stores formulation parameters alongside M1 prediction, M2 optimization candidates,
M3 sustainability / BIS audit, and M4 commercial RAG results.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_ROOT = Path(__file__).resolve().parents[2]
_DB_PATH = Path(os.environ.get("BATCH_DB_PATH", str(_ROOT / "data" / "batches" / "batches.sqlite")))
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
                CREATE TABLE IF NOT EXISTS formulations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    is_baseline INTEGER NOT NULL DEFAULT 1,
                    parent_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    mix_params_json TEXT NOT NULL,
                    prediction_json TEXT,
                    optimization_json TEXT,
                    score_json TEXT,
                    recommendation_json TEXT,
                    status TEXT NOT NULL DEFAULT 'draft',
                    notes TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_formulations_created_at ON formulations(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_formulations_parent_id ON formulations(parent_id)")
            conn.commit()
        finally:
            conn.close()


def create_formulation(
    name: str,
    mix_params: Dict[str, Any],
    version: int = 1,
    is_baseline: bool = True,
    parent_id: Optional[str] = None,
    prediction: Optional[Dict[str, Any]] = None,
    optimization: Optional[Dict[str, Any]] = None,
    score: Optional[Dict[str, Any]] = None,
    recommendation: Optional[Dict[str, Any]] = None,
    status: str = "active",
    notes: Optional[str] = None,
    formulation_id: Optional[str] = None,
) -> Dict[str, Any]:
    init_db()
    fid = formulation_id or f"FORM-{uuid.uuid4().hex[:8].upper()}"
    timestamp = _now()

    with _LOCK:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO formulations (
                    id, name, version, is_baseline, parent_id,
                    created_at, updated_at, mix_params_json,
                    prediction_json, optimization_json, score_json,
                    recommendation_json, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fid,
                    name,
                    version,
                    1 if is_baseline else 0,
                    parent_id,
                    timestamp,
                    timestamp,
                    json.dumps(mix_params),
                    json.dumps(prediction) if prediction else None,
                    json.dumps(optimization) if optimization else None,
                    json.dumps(score) if score else None,
                    json.dumps(recommendation) if recommendation else None,
                    status,
                    notes,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    return get_formulation(fid)  # type: ignore[return-value]


def update_formulation(
    formulation_id: str,
    name: Optional[str] = None,
    mix_params: Optional[Dict[str, Any]] = None,
    prediction: Optional[Dict[str, Any]] = None,
    optimization: Optional[Dict[str, Any]] = None,
    score: Optional[Dict[str, Any]] = None,
    recommendation: Optional[Dict[str, Any]] = None,
    status: Optional[str] = None,
    notes: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    init_db()
    existing = get_formulation(formulation_id)
    if not existing:
        return None

    timestamp = _now()
    updates = ["updated_at = ?"]
    params: List[Any] = [timestamp]

    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if mix_params is not None:
        updates.append("mix_params_json = ?")
        params.append(json.dumps(mix_params))
    if prediction is not None:
        updates.append("prediction_json = ?")
        params.append(json.dumps(prediction))
    if optimization is not None:
        updates.append("optimization_json = ?")
        params.append(json.dumps(optimization))
    if score is not None:
        updates.append("score_json = ?")
        params.append(json.dumps(score))
    if recommendation is not None:
        updates.append("recommendation_json = ?")
        params.append(json.dumps(recommendation))
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    if notes is not None:
        updates.append("notes = ?")
        params.append(notes)

    params.append(formulation_id)

    with _LOCK:
        conn = _connect()
        try:
            conn.execute(
                f"UPDATE formulations SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()
        finally:
            conn.close()

    return get_formulation(formulation_id)


def get_formulation(formulation_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    with _LOCK:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM formulations WHERE id = ?",
                (formulation_id,),
            ).fetchone()
            if not row:
                return None
            return _row_to_dict(row)
        finally:
            conn.close()


def list_formulations(
    search: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    init_db()
    with _LOCK:
        conn = _connect()
        try:
            if search:
                pattern = f"%{search}%"
                rows = conn.execute(
                    """
                    SELECT * FROM formulations
                    WHERE name LIKE ? OR id LIKE ? OR notes LIKE ?
                    ORDER BY updated_at DESC LIMIT ?
                    """,
                    (pattern, pattern, pattern, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM formulations ORDER BY updated_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [_row_to_dict(r) for r in rows]
        finally:
            conn.close()


def duplicate_formulation(formulation_id: str, new_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    source = get_formulation(formulation_id)
    if not source:
        return None

    new_version = source["version"] + 1
    name = new_name or f"{source['name']} (v{new_version})"
    return create_formulation(
        name=name,
        mix_params=source["mix_params"],
        version=new_version,
        is_baseline=False,
        parent_id=source["id"],
        prediction=source.get("prediction"),
        optimization=source.get("optimization"),
        score=source.get("score"),
        recommendation=source.get("recommendation"),
        notes=f"Cloned from {source['id']}",
    )


def delete_formulation(formulation_id: str) -> bool:
    init_db()
    with _LOCK:
        conn = _connect()
        try:
            cursor = conn.execute("DELETE FROM formulations WHERE id = ?", (formulation_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    d["is_baseline"] = bool(d["is_baseline"])
    d["mix_params"] = json.loads(d["mix_params_json"]) if d["mix_params_json"] else {}
    d["prediction"] = json.loads(d["prediction_json"]) if d.get("prediction_json") else None
    d["optimization"] = json.loads(d["optimization_json"]) if d.get("optimization_json") else None
    d["score"] = json.loads(d["score_json"]) if d.get("score_json") else None
    d["recommendation"] = json.loads(d["recommendation_json"]) if d.get("recommendation_json") else None
    return d

