"""
FastAPI application serving M1/M2/M3/M4/M5 endpoints for PlastiCrete.ai.
"""
from __future__ import annotations

import io
import os
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from loguru import logger

import modules.m1_prediction as m1
import modules.m2_optimization as m2
import modules.m3_sustainability as m3
import modules.m4_recommendation as m4
import modules.m5_report as m5
import modules.batch_passport as batches


from deployment.api.schemas import (
    HealthResponse, MixInput, PredictionResponse, PropertyResult, SchemaResponse,
    M4MixInput, RecommendationResponse, RAGAnalogueSchema, CostBenefitSchema,
    ScoreRequest, ScoreResponse,
    OptimizeRequest, OptimizeResponse,
    ReportRequest,
    BatchCreateRequest,
    BatchUpdateRequest,
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
    allow_methods=["GET", "POST", "PATCH"],
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
        result = m4.recommend(
            mix_params,
            m1_properties,
            ci_low=payload.ci_90_low,
            ci_high=payload.ci_90_high,
        )
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
        use_class_gates        = result.use_class_gates,
        primary_gate_status    = result.primary_gate_status,
        primary_gate_message   = result.primary_gate_message,
        verification_applications = result.verification_applications,
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
        result = m3.score_mix(
            mix_params,
            m1_properties,
            ci_low=payload.ci_90_low,
            ci_high=payload.ci_90_high,
        )
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
        "plastic_diversion_min_kg_m3": payload.plastic_diversion_min_kg_m3,
        "use_class":                payload.use_class,
    }
    weights = {
        "compressive_strength": payload.weight_compressive,
        "cost_per_m3":          payload.weight_cost,
        "co2_per_m3":           payload.weight_co2,
        "plastic_content_pct":  payload.weight_plastic_content,
    }
    try:
        result = m2.run_optimization(constraints, weights, mode=payload.mode)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.exception(f"M2 optimisation error: {exc}")
        raise HTTPException(status_code=500, detail="Internal optimisation error.")

    result["plastic_kg_available"] = payload.plastic_kg_available
    result["processing_cost_inr_per_kg"] = payload.processing_cost_inr_per_kg
    plastic_kg = (result.get("mass_balance") or {}).get("plastic_kg_m3")
    if payload.plastic_kg_available is not None and plastic_kg:
        result["monthly_m3"] = round(payload.plastic_kg_available / float(plastic_kg), 3)
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
    batch = None
    qr_url = None
    if payload.batch_id:
        batch = batches.get_batch(payload.batch_id)
        if batch is None:
            raise HTTPException(status_code=404, detail="Batch not found.")
        qr_url = batch["qr_url"]
    try:
        pdf_bytes = m5.generate_report(
            mix_params=payload.mix_params,
            prediction=payload.prediction,
            score=payload.score,
            recommendation=payload.recommendation,
            session_id=payload.session_id or (payload.batch_id or "WEB-SESSION"),
            batch=batch,
            qr_url=qr_url,
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


@app.post("/batches")
def create_batch(payload: BatchCreateRequest) -> dict:
    return batches.create_batch(
        mix_params=payload.mix_params,
        prediction=payload.prediction,
        score=payload.score,
        recommendation=payload.recommendation,
        plant_name=payload.plant_name,
        cast_date=payload.cast_date,
    )


@app.get("/batches")
def get_batches(limit: int = 50) -> list:
    return batches.list_batches(limit=limit)


@app.get("/batches/export.csv")
def export_batches() -> StreamingResponse:
    text = batches.export_csv()
    return StreamingResponse(
        io.BytesIO(text.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="batches.csv"'},
    )


@app.post("/batches/import.csv")
async def import_batches(file: UploadFile = File(...)) -> dict:
    text = (await file.read()).decode("utf-8")
    try:
        return batches.import_csv(text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/batches/schedule")
def schedule_verification(payload: BatchCreateRequest) -> dict:
    """Open a passport when a gate already returned verification_batch or lab_trial."""
    from modules.batch_passport.scheduler import open_if_gate_requires_cube

    opened = open_if_gate_requires_cube(
        payload.mix_params,
        payload.prediction,
        payload.score,
        payload.recommendation,
        plant_name=payload.plant_name,
        cast_date=payload.cast_date,
    )
    return {"opened": opened is not None, "batch": opened}


@app.get("/batches/due")
def batches_due(today: str | None = None) -> list:
    from datetime import date
    return batches.due_batches(today or date.today().isoformat())


@app.get("/batches/{batch_id}")
def read_batch(batch_id: str) -> dict:
    record = batches.get_batch(batch_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Batch not found.")
    return record


@app.patch("/batches/{batch_id}")
def patch_batch(batch_id: str, payload: BatchUpdateRequest) -> dict:
    try:
        record = batches.update_measurements(
            batch_id,
            cast_date=payload.cast_date,
            measured_cs_7d=payload.measured_cs_7d,
            measured_cs_28d=payload.measured_cs_28d,
            measured_absorption_pct=payload.measured_absorption_pct,
            notes=payload.notes,
            lab_name=payload.lab_name,
            operator=payload.operator,
            cube_size_mm=payload.cube_size_mm,
            cube_values_mpa=payload.cube_values_mpa,
            test_standard=payload.test_standard,
            source=payload.source,
            confirm_high_cv=payload.confirm_high_cv,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="Batch not found.")
    return record


@app.post("/batches/{batch_id}/photo")
async def upload_batch_photo(batch_id: str, file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=422, detail="Upload a JPEG, PNG, or WebP photo of the cube.")
    data = await file.read()
    if len(data) > 5_000_000:
        raise HTTPException(status_code=422, detail="Photo must be under 5 MB.")
    record = batches.save_photo(batch_id, data, suffix if suffix != ".jpeg" else ".jpg")
    if record is None:
        raise HTTPException(status_code=404, detail="Batch not found.")
    return {"id": record["id"], "cube_photo_path": record["cube_photo_path"]}


@app.get("/batches/{batch_id}/photo")
def read_batch_photo(batch_id: str) -> FileResponse:
    record = batches.get_batch(batch_id)
    if record is None or not record.get("cube_photo_path"):
        raise HTTPException(status_code=404, detail="No cube photo for this batch.")
    path = Path(record["cube_photo_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Cube photo file is missing.")
    return FileResponse(path)


@app.get("/batches/{batch_id}/passport.pdf")
def batch_passport_pdf(batch_id: str) -> StreamingResponse:
    record = batches.get_batch(batch_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Batch not found.")
    try:
        pdf_bytes = m5.generate_report(
            mix_params=record["mix_params"],
            prediction=record["prediction"],
            score=record["score"],
            recommendation=record["recommendation"],
            session_id=record["id"],
            batch=record,
            qr_url=record["qr_url"],
        )
    except Exception as exc:
        logger.exception(f"Batch passport error: {exc}")
        raise HTTPException(status_code=500, detail="Passport generation failed.")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="plasticrete_passport_{batch_id}.pdf"'},
    )