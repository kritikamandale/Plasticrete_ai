"""
Model singletons and disk-loading for M4.
All module-level names are None until load() is called.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

import joblib
import faiss

_MODEL_DIR = Path(__file__).parent.parent.parent.parent / "models" / "m4"

# ── Random-forest models ───────────────────────────────────────────────────────
rf_primary:    object = None
rf_multilabel: object = None
rf_score_reg:  object = None

# ── Scalers / encoders ─────────────────────────────────────────────────────────
scaler:     object = None
rag_scaler: object = None
label_enc:  object = None

# ── FAISS + JSON artifacts ─────────────────────────────────────────────────────
faiss_index: object       = None
rag_kb:      List[dict]   = []
config:      dict         = {}
market:      dict         = {}

_loaded = False


def load(model_dir: Path | None = None) -> None:
    """Load all M4 models and knowledge base from disk (idempotent)."""
    global rf_primary, rf_multilabel, rf_score_reg
    global scaler, rag_scaler, label_enc
    global faiss_index, rag_kb, config, market, _loaded

    if _loaded:
        return

    d = Path(model_dir) if model_dir else _MODEL_DIR
    rf_primary    = joblib.load(d / "m4_rf_primary_classifier.pkl")
    rf_multilabel = joblib.load(d / "m4_rf_multilabel_classifier.pkl")
    rf_score_reg  = joblib.load(d / "m4_rf_score_regressor.pkl")
    scaler        = joblib.load(d / "m4_feature_scaler.pkl")
    rag_scaler    = joblib.load(d / "m4_rag_property_scaler.pkl")
    label_enc     = joblib.load(d / "m4_label_encoder.pkl")
    faiss_index   = faiss.read_index(str(d / "m4_faiss_index.bin"))

    with open(d / "m4_rag_knowledge_base.json") as f:
        rag_kb = json.load(f)
    with open(d / "m4_config.json") as f:
        config = json.load(f)
    with open(d / "m4_market_prices.json") as f:
        market = json.load(f)

    _loaded = True


def is_loaded() -> bool:
    return _loaded
