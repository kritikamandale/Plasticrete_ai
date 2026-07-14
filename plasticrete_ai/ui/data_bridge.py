"""
Thin adapters between the premium UI and the real backend modules.

Every public function returns a *normalised dict* (never a backend dataclass) and
falls back to `ui.mock_data` on any failure, tagging the result with
`source = "real" | "mock"`. Heavy model loads go through `@st.cache_resource`;
per-mix results through `@st.cache_data`. Pages never import `modules/` directly.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import streamlit as st
import yaml

from ui import mock_data
from ui.theme import TARGET_ORDER

_ROOT = Path(__file__).resolve().parent.parent


# ── config ────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _m1_config() -> dict:
    path = _ROOT / "configs" / "m1_config.yaml"
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError:
        return {}


@st.cache_data(show_spinner=False)
def input_ranges() -> dict:
    """Slider ranges — single source of truth is m1_config augmentation.constraints."""
    cons = ((_m1_config().get("augmentation", {}) or {}).get("constraints", {}) or {})

    def rng(key, default):
        v = cons.get(key)
        return (float(v[0]), float(v[1])) if v else default

    return {
        "replacement_pct":  rng("replacement_pct",  (0.0, 40.0)),
        "particle_size_mm": rng("particle_size_mm", (0.5, 20.0)),
        "wc_ratio":         rng("wc_ratio",         (0.35, 0.65)),
        "additive_pct":     rng("additive_pct",     (0.0, 30.0)),
        "curing_temp_c":    rng("curing_temp_c",    (20.0, 80.0)),
        "curing_days":      rng("curing_days",      (3.0, 90.0)),
    }


# ── lazy, cached model loaders (one cold load per session) ───────────────────
@st.cache_resource(show_spinner=False)
def _load_m1():
    import modules.m1_prediction as m1
    m1.load_ensemble(str(_ROOT / "models" / "m1"), _m1_config())
    return m1


@st.cache_resource(show_spinner=False)
def _load_m2():
    import modules.m2_optimization as m2
    m2.load_models()
    return m2


@st.cache_resource(show_spinner=False)
def _load_m3():
    import modules.m3_sustainability as m3
    m3.load_models()
    return m3


@st.cache_resource(show_spinner=False)
def _load_m4():
    import modules.m4_recommendation as m4
    m4.load_models()
    return m4


# ── normalisers (backend dataclass → plain dict) ─────────────────────────────
def _norm_prediction(res) -> dict:
    return {
        "values":  {t: getattr(res, t, None) for t in TARGET_ORDER},
        "ci_low":  dict(getattr(res, "ci_low", {}) or {}),
        "ci_high": dict(getattr(res, "ci_high", {}) or {}),
        "shap_values": dict(getattr(res, "shap_values", {}) or {}),
        "uncertainty_flag": bool(getattr(res, "uncertainty_flag", False)),
        "low_coverage_targets": list(getattr(res, "low_coverage_targets", []) or []),
        "source": "real",
    }


def props_from_prediction(pred: dict) -> dict:
    """The 7-property dict M3/M4 expect, pulled from a prediction result."""
    vals = pred.get("values", {})
    return {t: (vals.get(t) if vals.get(t) is not None else 0.0) for t in TARGET_ORDER}


# ── public API ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _predict_cached(mix_key: tuple) -> dict:
    mix = dict(mix_key)
    m1 = _load_m1()
    return _norm_prediction(m1.predict(mix))


def predict(mix: dict) -> dict:
    """M1 — 7 properties + CIs + SHAP for a mix recipe."""
    try:
        return _predict_cached(tuple(sorted(mix.items())))
    except Exception as exc:  # noqa: BLE001 — never block the UI on a backend gap
        out = mock_data.prediction()
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out


@st.cache_data(show_spinner=False)
def _score_cached(mix_key: tuple, prop_key: tuple) -> dict:
    m3 = _load_m3()
    res = m3.score_mix(dict(mix_key), dict(prop_key))
    res = dict(res)
    # enrich with fields the mock provides so the page renders identically
    res.setdefault("baseline_co2_kgco2e_m3", 365.71)
    res.setdefault("co2_saved_kgco2e_m3",
                   round(res["baseline_co2_kgco2e_m3"] - res.get("embodied_carbon_kgco2e_m3", 0), 1))
    res["source"] = "real"
    return res


def score(mix: dict, props: dict) -> dict:
    """M3 — sustainability score, embodied carbon, diversion, green credits."""
    try:
        return _score_cached(tuple(sorted(mix.items())), tuple(sorted(props.items())))
    except Exception as exc:  # noqa: BLE001
        out = mock_data.sustainability()
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out


@st.cache_data(show_spinner=False)
def _recommend_cached(mix_key: tuple, prop_key: tuple) -> dict:
    m4 = _load_m4()
    res = m4.recommend(dict(mix_key), dict(prop_key))
    return {
        "primary_application":    res.primary_application,
        "primary_confidence_pct": res.primary_confidence_pct,
        "suitable_applications":  list(res.suitable_applications),
        "suitability_scores":     dict(res.suitability_scores),
        "cost_benefit":           dict(res.cost_benefit.__dict__),
        "rag_analogues":          [dict(a.__dict__) for a in res.rag_analogues],
        "source": "real",
    }


def recommend(mix: dict, props: dict) -> dict:
    """M4 — ranked applications, cost-benefit, RAG analogues."""
    try:
        return _recommend_cached(tuple(sorted(mix.items())), tuple(sorted(props.items())))
    except Exception as exc:  # noqa: BLE001
        out = mock_data.recommendation()
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out


@st.cache_data(show_spinner=False)
def _optimize_cached(constraints_key: tuple, weights_key: tuple, mode: str) -> dict:
    m2 = _load_m2()
    res = m2.run_optimization(dict(constraints_key), dict(weights_key), mode=mode)
    res = dict(res)
    res["source"] = "real"
    return res


def optimize(constraints: dict, weights: dict, mode: str = "constrained") -> dict:
    """M2 — best mix for the given objective weights + constraints."""
    try:
        return _optimize_cached(tuple(sorted(constraints.items())),
                                tuple(sorted(weights.items())), mode)
    except Exception as exc:  # noqa: BLE001
        out = mock_data.optimize()
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out


def bis_checklist(props: dict) -> list[dict]:
    """Per-standard BIS pass/warn/fail rows (real via BISChecker, else mock)."""
    try:
        from modules.m3_sustainability.core.bis_checker import BISChecker
        r = BISChecker().check(props)
        rows = [
            ("is_516",  r.is_516_compliant,  f"Grade {r.is_516_grade} · CS {props.get('compressive_strength_mpa',0):.1f} MPa",
             "CS ≥ 10 MPa", "Increase binder / lower w/c to raise strength."),
            ("is_1237", r.is_1237_compliant, f"CS margin {r.is_1237_cs_margin:+.1f} · WA margin {r.is_1237_wa_margin:+.1f}",
             "CS ≥ 30 MPa & WA ≤ 1%", "Add silica fume and reduce w/c to cut absorption."),
            ("is_2185", r.is_2185_pt1_compliant and r.is_2185_pt2_compliant,
             f"Pt.1 {'✓' if r.is_2185_pt1_compliant else '✗'} · Pt.2 {'✓' if r.is_2185_pt2_compliant else '✗'}",
             "CS ≥ 3.5 MPa · density ≤ 1500 kg/m³", "Raise plastic replacement to lower density."),
            ("is_5816", r.is_5816_compliant, "Split-tensile vs CS ratio checked",
             "STS ≥ 0.10·CS & ≥ 1.5 MPa", "Add fibres to improve tensile behaviour."),
            ("nbc",     r.nbc_structural or r.nbc_nonstructural,
             f"Structural {'✓' if r.nbc_structural else '✗'} · Non-structural {'✓' if r.nbc_nonstructural else '✗'}",
             "CS ≥ 20 MPa (structural)", "Boost strength for structural certification."),
        ]
        out = []
        for key, ok, detail, thr, fix in rows:
            out.append({"key": key, "passed": bool(ok),
                        "status": "pass" if ok else "fail",
                        "detail": detail, "threshold": thr,
                        "fix": "" if ok else fix})
        return out
    except Exception:  # noqa: BLE001
        return mock_data.bis_checklist()


# ── lightweight availability probe (no 33 s M1 load) ─────────────────────────
@st.cache_data(show_spinner=False, ttl=300)
def module_status() -> dict:
    """Best-effort real/mock status for a header indicator (does not warm M1)."""
    status = {}
    # M1: present if artifacts + torch importable
    try:
        import torch  # noqa: F401
        status["M1"] = (_ROOT / "models" / "m1" / "ensemble_config.json").exists()
    except Exception:  # noqa: BLE001
        status["M1"] = False
    for name, loader in (("M2", _load_m2), ("M3", _load_m3), ("M4", _load_m4)):
        try:
            loader()
            status[name] = True
        except Exception:  # noqa: BLE001
            status[name] = False
    return status
