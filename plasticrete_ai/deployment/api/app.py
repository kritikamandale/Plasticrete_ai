"""
FastAPI application serving M1/M2/M3/M4/M5 endpoints for PlastiCrete.ai.
"""
from __future__ import annotations

import io
import os
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from loguru import logger

import modules.m1_prediction as m1
import modules.m2_optimization as m2
import modules.m3_sustainability as m3
import modules.m4_recommendation as m4
import modules.m5_report as m5


from deployment.api.schemas import (
    HealthResponse, MixInput, PredictionResponse, PropertyResult, SchemaResponse,
    M4MixInput, RecommendationResponse, RAGAnalogueSchema, CostBenefitSchema,
    ScoreRequest, ScoreResponse,
    OptimizeRequest, OptimizeResponse,
    ReportRequest,
)
from modules.m1_prediction.utils.schema import (
    ADDITIVE_TYPE_CLASSES, INPUT_RANGES, PLASTIC_TYPE_CLASSES, TARGET_COLUMNS,
)

_PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH   = _PROJECT_ROOT / "configs" / "m1_config.yaml"
_config: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _config
    logger.info("PlastiCrete AI starting up ...")
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            _config = yaml.safe_load(f)
    model_dir = str(_PROJECT_ROOT / _config.get("model_output", {}).get("save_dir", "models/m1/"))
    try:
        m1.load_ensemble(model_dir, _config)
        logger.info(f"M1 ensemble loaded from {model_dir}")
    except Exception as exc:
        logger.error(f"Failed to load M1 ensemble: {exc}")
    try:
        m2.load_models()
        logger.info("M2 optimisation models loaded")
    except Exception as exc:
        logger.error(f"Failed to load M2 models: {exc}")
    try:
        m3.load_models()
        logger.info("M3 sustainability models loaded")
    except Exception as exc:
        logger.error(f"Failed to load M3 models: {exc}")
    try:
        m4.load_models()
        logger.info("M4 recommendation models loaded")
    except Exception as exc:
        logger.error(f"Failed to load M4 models: {exc}")
    yield
    logger.info("PlastiCrete AI shutting down")


app = FastAPI(
    title="PlastiCrete AI",
    description=(
        "Predict 7 mechanical/physical properties of plastic-waste composite concrete, "
        "run Pareto optimisation, score sustainability (LCA + BIS), recommend applications, "
        "and generate professional PDF Mix Design Reports."
    ),
    version="1.1.0",
    lifespan=lifespan,
)

_CORS_ORIGINS_ENV = os.environ.get("CORS_ORIGINS", "")
_CORS_ORIGINS = (
    [o.strip() for o in _CORS_ORIGINS_ENV.split(",") if o.strip()]
    if _CORS_ORIGINS_ENV
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", module="M1")


@app.get("/schema", response_model=SchemaResponse)
def schema() -> SchemaResponse:
    fields = {
        "plastic_type":    {"type": "str",   "classes": PLASTIC_TYPE_CLASSES},
        "replacement_pct": {"type": "float", "range": list(INPUT_RANGES["replacement_pct"])},
        "particle_size_mm":{"type": "float", "range": list(INPUT_RANGES["particle_size_mm"])},
        "wc_ratio":        {"type": "float", "range": list(INPUT_RANGES["wc_ratio"])},
        "additive_type":   {"type": "str",   "classes": ADDITIVE_TYPE_CLASSES},
        "additive_pct":    {"type": "float", "range": list(INPUT_RANGES["additive_pct"])},
        "curing_temp_c":   {"type": "float", "range": list(INPUT_RANGES["curing_temp_c"])},
        "curing_days":     {"type": "int",   "range": list(INPUT_RANGES["curing_days"])},
    }
    return SchemaResponse(
        input_fields=fields,
        output_fields=TARGET_COLUMNS,
        plastic_type_classes=PLASTIC_TYPE_CLASSES,
        additive_type_classes=ADDITIVE_TYPE_CLASSES,
    )


@app.post("/predict", response_model=PredictionResponse)
def predict(mix: MixInput) -> PredictionResponse:
    try:
        mix.validate_categoricals()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    input_dict = mix.model_dump()
    try:
        result = m1.predict(input_dict)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.exception(f"Prediction error: {exc}")
        raise HTTPException(status_code=500, detail="Internal prediction error.")

    predictions = {}
    for target in TARGET_COLUMNS:
        mean_val = getattr(result, target, None)
        predictions[target] = PropertyResult(
            mean=mean_val,
            ci_90_low=result.ci_low.get(target),
            ci_90_high=result.ci_high.get(target),
        )

    return PredictionResponse(
        predictions=predictions,
        shap_values=result.shap_values,
        uncertainty_flag=result.uncertainty_flag,
        low_coverage_targets=result.low_coverage_targets,
    )


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(payload: M4MixInput) -> RecommendationResponse:
    mix_params = {
        "plastic_type":     payload.plastic_type,
        "replacement_pct":  payload.replacement_pct,
        "particle_size_mm": payload.particle_size_mm,
        "wc_ratio":         payload.wc_ratio,
        "additive_type":    payload.additive_type,
        "additive_pct":     payload.additive_pct,
        "curing_temp_c":    payload.curing_temp_c,
        "curing_days":      payload.curing_days,
    }
    m1_properties = {
        "compressive_strength_mpa": payload.compressive_strength_mpa,
        "flexural_strength_mpa":    payload.flexural_strength_mpa,
        "split_tensile_mpa":        payload.split_tensile_mpa,
        "density_kgm3":             payload.density_kgm3,
        "water_absorption_pct":     payload.water_absorption_pct,
        "thermal_conductivity_wm":  payload.thermal_conductivity_wm,
        "durability_index":         payload.durability_index,
    }
    try:
        result = m4.recommend(mix_params, m1_properties)
    except Exception as exc:
        logger.exception(f"M4 recommendation error: {exc}")
        raise HTTPException(status_code=500, detail="Internal recommendation error.")

    return RecommendationResponse(
        primary_application    = result.primary_application,
        primary_confidence_pct = result.primary_confidence_pct,
        suitable_applications  = result.suitable_applications,
        suitability_scores     = result.suitability_scores,
        cost_benefit           = CostBenefitSchema(**result.cost_benefit.__dict__),
        rag_analogues          = [
            RAGAnalogueSchema(**a.__dict__) for a in result.rag_analogues
        ],
    )

@app.post("/score", response_model=ScoreResponse)
def score(payload: ScoreRequest) -> ScoreResponse:
    mix_params = {
        "plastic_type":     payload.plastic_type,
        "replacement_pct":  payload.replacement_pct,
        "particle_size_mm": payload.particle_size_mm,
        "wc_ratio":         payload.wc_ratio,
        "additive_type":    payload.additive_type,
        "additive_pct":     payload.additive_pct,
        "curing_temp_c":    payload.curing_temp_c,
        "curing_days":      payload.curing_days,
    }
    m1_properties = {
        "compressive_strength_mpa": payload.compressive_strength_mpa,
        "flexural_strength_mpa":    payload.flexural_strength_mpa,
        "split_tensile_mpa":        payload.split_tensile_mpa,
        "density_kgm3":             payload.density_kgm3,
        "water_absorption_pct":     payload.water_absorption_pct,
        "thermal_conductivity_wm":  payload.thermal_conductivity_wm,
        "durability_index":         payload.durability_index,
    }
    try:
        result = m3.score_mix(mix_params, m1_properties)
    except Exception as exc:
        logger.exception(f"M3 scoring error: {exc}")
        raise HTTPException(status_code=500, detail="Internal scoring error.")

    return ScoreResponse(**result)


@app.post("/optimize", response_model=OptimizeResponse)
def optimize(payload: OptimizeRequest) -> OptimizeResponse:
    constraints = {
        "plastic_type":             payload.plastic_type,
        "replacement_pct_max":      payload.replacement_pct_max,
        "compressive_strength_min": payload.compressive_strength_min,
        "density_max_kgm3":         payload.density_max_kgm3,
        "cost_max_inr_per_m3":      payload.cost_max_inr_per_m3,
    }
    weights = {
        "compressive_strength": payload.weight_compressive,
        "cost_per_m3":          payload.weight_cost,
        "co2_per_m3":           payload.weight_co2,
        "plastic_content_pct":  payload.weight_plastic_content,
    }
    try:
        result = m2.run_optimization(constraints, weights, mode=payload.mode)
    except Exception as exc:
        logger.exception(f"M2 optimisation error: {exc}")
        raise HTTPException(status_code=500, detail="Internal optimisation error.")

    return OptimizeResponse(**result)


# ── M5: PDF Mix Design Report ──────────────────────────────────────────────────
@app.post(
    "/report/pdf",
    response_class=StreamingResponse,
    summary="Generate a professional PDF Mix Design Report",
    description=(
        "Accepts full mix parameters, M1 prediction, M3 score, and M4 recommendation. "
        "Returns a formatted A4 PDF with recipe table, predicted properties, BIS compliance, "
        "LCA carbon, green credits, SHAP feature influence, and literature analogues."
    ),
)
def report_pdf(payload: "ReportRequest") -> StreamingResponse:
    try:
        pdf_bytes = m5.generate_report(
            mix_params=payload.mix_params,
            prediction=payload.prediction,
            score=payload.score,
            recommendation=payload.recommendation,
            session_id=payload.session_id or "WEB-SESSION",
        )
    except Exception as exc:
        logger.exception(f"M5 report generation error: {exc}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    session_slug = (payload.session_id or "report").replace(" ", "_")[:24]
    filename = f"plasticrete_report_{session_slug}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )