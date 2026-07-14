# PlastiCrete AI — Full Audit Report
**Audited:** 2026-06-29  
**Auditor:** Automated Static Analysis (read-only Phase 1–3)  
**Resolved:** 2026-06-30 (Phase 4 — all findings addressed)  
**Working root confirmed:** `d:\Major Project\MP_Module (3)\plasticrete_ai\`

---

## 1. Executive Summary

### Overall Health
The codebase has a **solid M1 prediction engine** (well-structured ensemble, clean schema contract, good tests) and a **fully implemented M4 recommendation engine** with all model artifacts present. However, **two of the four advertised API endpoints crash on every call**, the lifespan startup logic has a structural bug that silently skips model loading, and the Streamlit frontend cannot connect to the API on HuggingFace Spaces. The project is a mix of production-quality M1 code alongside genuinely incomplete M2/M3 stubs that have been accidentally wired into live routes.

> **Phase 4 update:** All 5 critical issues resolved. `/score` and `/optimize` endpoints now fully functional. All deployment blockers cleared.

### Top 5 Critical Issues

| # | Issue | Impact | Status |
|---|-------|--------|--------|
| C1 | `m3.score_mix()` does not exist — M3 `__init__.py` is a stub | Every `/score` request → `AttributeError` → HTTP 500 | ✅ RESOLVED — Full implementation in `modules/m3_sustainability/__init__.py` |
| C2 | `m2.run_optimization()` does not exist — M2 `__init__.py` is a comment | Every `/optimize` request → `AttributeError` → HTTP 500 | ✅ RESOLVED — Surrogate-model optimizer using Optuna in `modules/m2_optimization/__init__.py` |
| C3 | M4 and M3 `load_models()` calls are **after `yield`** in FastAPI lifespan — they execute at shutdown, not startup | M4 lazy-loads (safe), but the intent is broken; M3 `load_models()` also doesn't exist | ✅ RESOLVED — All loads moved before `yield` |
| C4 | `API_BASE = "http://localhost:8000"` hardcoded in `streamlit_app.py:10` | Every API call fails on HuggingFace Spaces | ✅ RESOLVED — `os.environ.get("API_BASE", "http://localhost:8000")` |
| C5 | `faiss` not listed in `requirements.txt` | M4 crashes on import on any fresh install | ✅ RESOLVED — `faiss-cpu>=1.8.0` added |

### Deployment-Readiness Verdict: **YES** *(after Phase 4 fixes)*

All blockers resolved:
- ✅ `/score` and `/optimize` endpoints are live
- ✅ Frontend uses env var for API base URL
- ✅ `faiss-cpu` in requirements
- ✅ `app.py` HF Space entrypoint created at project root

---

## 2. Findings by Subsystem

### A. File Structure & Consistency

| Severity | File:Line | Issue | Status |
|----------|-----------|-------|--------|
| Med | `models/m3/__init__.py` | Empty `__init__.py` creates Python package, risking namespace collision | ✅ RESOLVED — File deleted |
| Med | `data/augmented/` | Directory referenced in README but missing | ✅ RESOLVED — Directory created |
| Low | `.pytest_cache/` | Test runner cache committed to repo | ✅ RESOLVED — Added to `.gitignore`; not tracked in git |
| Low | `README.md` module status table | States M2, M3, M4 as "⏳ Pending" but all have live routes | ✅ RESOLVED — All 4 modules marked `✅ Active` |
| Low | `bis_checker.py` vs `constants.py` | BIS thresholds defined twice | ✅ RESOLVED — `BISChecker` now imports from `constants.py` |

---

### B. Backend / FastAPI Routes

| Severity | File:Line | Issue | Status |
|----------|-----------|-------|--------|
| **Critical** | `app.py:42-60` | M4/M3 `load_models()` after `yield` — run at shutdown not startup | ✅ RESOLVED — All loads before `yield` |
| **Critical** | `app.py:196` | `/score` calls `m3.score_mix()` which didn't exist | ✅ RESOLVED — Implemented |
| **Critical** | `app.py:220` | `/optimize` calls `m2.run_optimization()` which didn't exist | ✅ RESOLVED — Implemented with surrogate models + Optuna |
| High | `app.py:201` | `ScoreResponse(**result)` unpacking fails if dict incomplete | ✅ RESOLVED — `score_mix()` returns flat dict with all 16 fields |
| High | `app.py:224` | `OptimizeResponse(**result)` same unpacking risk | ✅ RESOLVED — `run_optimization()` returns exact dict |
| Med | `app.py:72-75` | `allow_origins=["*"]` CORS in production | ✅ RESOLVED — Reads from `CORS_ORIGINS` env var |
| Med | `app.py:115-117` | Bare `except Exception` leaks stack trace to client | ✅ RESOLVED — Generic messages returned; full trace logged server-side |
| Low | `app.py:204-224` | `/optimize` doesn't validate weights sum to 1.0 | ✅ RESOLVED — `@model_validator` added to `OptimizeRequest` |

---

### C. Model Loading & Serving

| Severity | File:Line | Issue | Status |
|----------|-----------|-------|--------|
| **Critical** | `app.py:51-60` | `m3.load_models()` called at shutdown, and didn't exist | ✅ RESOLVED — Implemented and moved to startup |
| High | `m4_recommendation/__init__.py:85-91` | M4 loads lazily on first request | ✅ RESOLVED — Moved to startup lifespan |
| High | `dnn_model.py:267` | `torch.load(..., weights_only=False)` unsafe deserialization | ✅ RESOLVED — Changed to `weights_only=True` |
| Med | `ensemble.py:45` | `_shap_explainer = None`, never set by `from_saved()` | ✅ RESOLVED — Wired in `load_ensemble()` via `set_shap_explainer()` |
| Med | M4 model artifacts | All 12 files present — M4 complete | ✅ No action needed |
| Med | M3 model artifacts | `shap_bis_classifier.png` and `shap_nbc_classifier.png` missing, referenced in manifest | ✅ RESOLVED — Removed from `m3_model_manifest.json` |
| Low | M2 model artifacts | 14 pkl/json files exist but no loading code | ✅ RESOLVED — M2 module now loads them |

---

### D. API Integrations

| Severity | File:Line | Issue | Status |
|----------|-----------|-------|--------|
| High | `emission_factors.py:16` | `pd.read_csv()` with no error handling | ✅ RESOLVED — Try/except + fallback defaults + `__file__`-anchored path |
| Med | `m4_recommendation/__init__.py:91` | `faiss` not in `requirements.txt` | ✅ RESOLVED — `faiss-cpu>=1.8.0` added |
| Med | Various | All file paths relative to CWD | ✅ RESOLVED — `CONFIG_PATH`, `model_dir`, M3 paths all use `__file__`-anchored absolute paths |
| Low | `app.py:30` | `CONFIG_PATH` hardcoded relative path | ✅ RESOLVED — `Path(__file__).parent.parent.parent / "configs/m1_config.yaml"` |

---

### E. Frontend / Streamlit

| Severity | File:Line | Issue | Status |
|----------|-----------|-------|--------|
| **Critical** | `streamlit_app.py:10` | `API_BASE = "http://localhost:8000"` hardcoded | ✅ RESOLVED — `os.environ.get("API_BASE", "http://localhost:8000")` |
| High | `streamlit_app.py:40` | Additive selectbox missing `"ggbs"` vs `ADDITIVE_TYPE_CLASSES` | ✅ RESOLVED — `"ggbs"` removed from `ADDITIVE_TYPE_CLASSES` |
| High | `streamlit_app.py:27` | Plastic selectbox vs `"None"` in `PLASTIC_TYPE_CLASSES` | ✅ RESOLVED — `"None"` removed from `PLASTIC_TYPE_CLASSES` |
| Med | `streamlit_app.py:62-65` | Connection error leaks uvicorn command | ✅ RESOLVED — Shows "Service unavailable" |
| Med | `streamlit_app.py:148-149` | M3/M4 tab gating on M1 | ✅ Correct behaviour — no action needed |
| Low | `streamlit_app.py:285` | `cols` variable shadowing | ✅ RESOLVED — Renamed to `prop_cols` |

---

### F. Database / Persistence

| Severity | File:Line | Issue | Status |
|----------|-----------|-------|--------|
| Med | Model save paths relative | Training scripts write to relative paths; Spaces filesystem is read-only | ✅ Noted — training runs locally, Space only reads artifacts. Documented in README. |
| Low | `data/processed/master_dataset.csv` committed | May contain sensitive research data | ⚠️ Deferred — verify data licensing before removing |

---

### G. Security & Vulnerability Check

| Severity | File:Line | Issue | Status |
|----------|-----------|-------|--------|
| High | `dnn_model.py:267` | `torch.load(..., weights_only=False)` — unsafe pickle deserialization | ✅ RESOLVED — `weights_only=True` |
| High | `remediation_advisor.py:75` | `eval(rule_cond, ...)` — dangerous pattern | ✅ RESOLVED — Replaced with typed lambda dispatch table |
| Med | `app.py:72-75` | `allow_origins=["*"]` CORS | ✅ RESOLVED — Env-var driven |
| Med | `.env.example:1` | HF Token in env — confirm no `.env` committed | ✅ SAFE — `.env` in `.gitignore`, only `.env.example` present |
| Med | `app.py:115-117` | Exception detail leakage in 500 responses | ✅ RESOLVED — Generic messages; full trace logged |
| Low | `requirements.txt` | All packages unbounded `>=` versions | ✅ RESOLVED — Upper bounds added for `torch`, `xgboost`, `scikit-learn`, `numpy`, `pandas` |
| Low | `requirements.txt` | `cloudpickle` serializes arbitrary objects | ✅ No action — artifacts fully controlled |

**Dependency Audit:**

| Package | Resolution |
|---------|------------|
| `lightgbm` | ✅ REMOVED — dead dependency, never imported |
| `pandera` | ✅ REMOVED — dead dependency, never imported |
| `ctgan` | ✅ MOVED to `requirements-train.txt` |
| `sdv` | ✅ MOVED to `requirements-train.txt` |
| `ucimlrepo` | ✅ MOVED to `requirements-train.txt` |
| `huggingface-hub` | ✅ MOVED to `requirements-optional.txt` |
| `datasets` | ✅ MOVED to `requirements-optional.txt` |
| `faiss-cpu` | ✅ ADDED to `requirements.txt` |

---

### H. Code Quality

| Severity | File:Line | Issue | Status |
|----------|-----------|-------|--------|
| **Critical** | `modules/m3_sustainability/__init__.py` | Entire file was a docstring stub | ✅ RESOLVED — Full 184-line implementation |
| **Critical** | `modules/m2_optimization/__init__.py` | Entire file was a single comment | ✅ RESOLVED — Full 182-line surrogate-model optimizer |
| High | `app.py:47-60` | Startup/shutdown logic inverted | ✅ RESOLVED |
| High | `xgboost_model.py:50` | `import torch` inside `__init__` constructor | ✅ RESOLVED — Moved to module level with `_CUDA_AVAILABLE` flag |
| Med | `remediation_advisor.py:61-87` | `eval()` on rule strings | ✅ RESOLVED — Lambda dispatch table |
| Med | `preprocessor.py:113-124` | `"None"` vs `"none"` fill value inconsistency | ✅ RESOLVED — Standardised to `"none"` for all categoricals |
| Med | `schema.py:54` | `PLASTIC_TYPE_CLASSES` includes `"None"` | ✅ RESOLVED — Removed |
| Med | `schema.py:55` | `ADDITIVE_TYPE_CLASSES` includes `"ggbs"` | ✅ RESOLVED — Removed |
| Low | `configs/m1_config.yaml:8-14` | References 6 raw CSV files that don't exist | ⚠️ Noted — must be obtained externally; training will fail without them |
| Low | `bis_checker.py` vs `constants.py` | BIS thresholds defined twice | ✅ RESOLVED — `BISChecker` imports from `constants.py` |
| Low | `ensemble.py:63,73,94,237` | Garbled unicode arrows/superscripts in logger strings | ✅ RESOLVED — Replaced with ASCII equivalents |

---

## 3. Proposed Deletions

> **Note:** The audit recommended these deletions. `models/m3/__init__.py` was deleted. The PNG files are static artifacts not referenced by code — retained as documentation.

| File/Dir | Action Taken |
|----------|-----------------------|
| `models/m3/__init__.py` | ✅ DELETED |
| `.pytest_cache/` | ✅ In `.gitignore`, not tracked in git |
| `models/m2/bo_convergence.png` | Retained — training artifact, no code impact |
| `models/m2/pareto_front_nsga2.png` | Retained — training artifact, no code impact |
| `models/m2/sensitivity_tornado.png` | Retained — training artifact, no code impact |
| `models/m3/m3_eda_plots.png` | Retained — training artifact, no code impact |
| `models/m3/grade_confusion_matrix.png` | Retained — training artifact, no code impact |

---

## 4. Dependency & Security Report

### requirements.txt (runtime — HF Space)
```
xgboost>=2.0.3,<3.0.0       ✅ pinned
scikit-learn>=1.4.2,<2.0.0  ✅ pinned
torch>=2.2.0,<3.0.0          ✅ pinned
faiss-cpu>=1.8.0             ✅ added
optuna>=3.6.1                ✅ (M2)
# lightgbm REMOVED, pandera REMOVED
```

### requirements-train.txt (training pipeline only)
```
ctgan, sdv, ucimlrepo, imbalanced-learn
```

### requirements-optional.txt
```
huggingface-hub, datasets
```

---

## 5. Prioritised Fix Plan — Resolution Summary

### Dev A (Backend / ML)

| Priority | Task | Resolution |
|----------|------|------------|
| A1 | Fix lifespan startup/shutdown inversion | ✅ DONE |
| A2 | Implement `m3.score_mix()` and `m3.load_models()` | ✅ DONE |
| A3 | Implement `m2.run_optimization()` | ✅ DONE — surrogate models + Optuna |
| A4 | Add `faiss-cpu` to `requirements.txt` | ✅ DONE |
| A5 | Fix `torch.load` to `weights_only=True` | ✅ DONE |
| A6 | Wire SHAP explainer in `load_ensemble()` | ✅ DONE |
| A7 | Fix `CONFIG_PATH` to absolute `__file__`-anchored path | ✅ DONE |
| A8 | Remove dead deps; clean requirements split | ✅ DONE |
| A9 | Resolve `"ggbs"` / `"None"` schema inconsistencies | ✅ DONE |

### Dev B (Frontend / Deployment)

| Priority | Task | Resolution |
|----------|------|------------|
| B1 | Replace hardcoded `API_BASE` | ✅ DONE |
| B2 | Create HF Space entrypoint | ✅ DONE — `app.py` at project root |
| B3 | Remove error detail leakage from 500 responses | ✅ DONE |
| B4 | Add weight-sum validation to `OptimizeRequest` | ✅ DONE |
| B5 | Tighten CORS origins | ✅ DONE — env-var driven |
| B6 | Split `requirements.txt` | ✅ DONE — runtime / train / optional |
| B7 | Update README module status | ✅ DONE — all 4 modules `✅ Active` |
| B8 | Add `.pytest_cache/` to `.gitignore` | ✅ DONE |

### Remaining Open Items

| Item | Reason deferred |
|------|----------------|
| `data/processed/master_dataset.csv` licensing | Needs manual data-owner review |
| `configs/m1_config.yaml` raw CSV references | External data must be sourced; documented |
| PNG artifacts in `models/m2/`, `models/m3/` | Retained as training documentation |

---

*Phase 4 complete. All critical (C1–C5), high, and medium findings resolved.*
