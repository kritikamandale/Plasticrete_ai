# PlastiCrete AI — UI Recon Notes

Phase-A read-only reconnaissance. No backend files were modified. This is the
single reference the new `ui/` layer is wired against.

## Runtime environment (verified)
- Python **3.11.4**; `streamlit **1.58.0**` (supports `st.navigation`/`st.Page`),
  `plotly **6.8.0**`, `pandas 2.3.3`, `numpy`, `pyyaml` all present.
- `plasticrete_ai/` is itself a git repo (`.git/` present).
- **M1 cold load ≈ 33 s** (torch + shap) → must go through `@st.cache_resource`.

## Real-module load status (smoke-tested)
| Module | Import | Loads? | Notes |
|---|---|---|---|
| M1 Prediction   | `modules.m1_prediction`   | ✅ real | `predict()` returns real values + SHAP |
| M2 Optimisation | `modules.m2_optimization` | ✅ real | surrogate XGB + Optuna |
| M3 Sustainability | `modules.m3_sustainability` | ✅ real | score_mix works |
| M4 Recommendation | `modules.m4_recommendation` | ❌ **mock fallback** | `ModuleNotFoundError: faiss` — RAG index needs `faiss-cpu`. Install to enable. |

## Public callables (the contract `ui/data_bridge.py` targets)

### M1 — `import modules.m1_prediction as m1`
- `m1.load_ensemble(model_dir: str, config: dict) -> None` — dir `models/m1`, config `configs/m1_config.yaml`.
- `m1.predict(input_dict) -> PredictionResult`
  - **input keys**: `plastic_type, replacement_pct, particle_size_mm, wc_ratio, additive_type, additive_pct, curing_temp_c, curing_days`
  - **PredictionResult** (dataclass): 7 target attrs `compressive_strength_mpa, flexural_strength_mpa, split_tensile_mpa, density_kgm3, water_absorption_pct, thermal_conductivity_wm, durability_index`; plus `ci_low: {target: float}`, `ci_high: {target: float}`, `shap_values: {target: {feature: float}}`, `uncertainty_flag: bool`, `low_coverage_targets: [str]`.
- `m1.predict_batch(X) -> (means, ci_low, ci_high)`, `m1.get_preprocessor()`.

### M2 — `import modules.m2_optimization as m2`
- `m2.load_models() -> None`
- `m2.run_optimization(constraints, weights, mode="constrained"|"scenario") -> dict`
  - **constraints**: `plastic_type(None ok), replacement_pct_max, compressive_strength_min, density_max_kgm3, cost_max_inr_per_m3`
  - **weights**: `compressive_strength, cost_per_m3, co2_per_m3, plastic_content_pct` (must sum ~1.0)
  - **returns**: `best_mix{}, predicted_cs_mpa, predicted_cost_inr_m3, predicted_co2_kgco2e_m3, predicted_plastic_diversion_kg_m3, composite_score, mode`
- **Precomputed artifacts** to read directly for viz (read-only):
  `models/m2/pareto_solutions_nsga2_ranked.csv`, `scenario_results.json`,
  `sensitivity_analysis.json`, `bo_demo_result.json`.

### M3 — `import modules.m3_sustainability as m3`
- `m3.load_models(model_dir="", config=None) -> None`
- `m3.score_mix(mix_params, m1_props) -> dict` with keys:
  `sustainability_score, sustainability_grade, embodied_carbon_kgco2e_m3, co2_saving_pct, plastic_diversion_kg_m3, pet_bottle_equiv, bis_overall_pass, igbc_total_credits, griha_material_criterion_pts, leed_total_points, total_green_credits, top_negative_factor, remediation_action_1..3, estimated_score_gain`.
- Per-standard BIS checklist available via `modules.m3_sustainability.core.bis_checker.BISChecker().check(props) -> BISResult`
  (`is_516_grade`, `is_516/is_1237/is_2185_pt1/is_2185_pt2/is_5816/nbc_structural/nbc_nonstructural` bools + margins). Used read-only for the compliance table.

### M4 — `import modules.m4_recommendation as m4`
- `m4.load_models(model_dir=None) -> None`
- `m4.recommend(mix_params, m1_properties) -> RecommendationResult`
  - `primary_application, primary_confidence_pct, suitable_applications[], suitability_scores{app: 0-100}, cost_benefit(CostBenefit), rag_analogues[RAGAnalogue]`
  - **CostBenefit**: `plastic_mix_cost_inr_m3, conventional_cost_inr_m3, cost_saving_inr_m3, cost_saving_pct, plastic_mix_cost_inr_m2, conventional_cost_inr_m2, cost_saving_inr_m2, product_yield_m2_per_m3, plastic_kg_per_m3, additive_kg_per_m3`
  - **RAGAnalogue**: `rank, id, author, year, journal, doi, primary_application, secondary_application, l2_distance, properties{}`
- **12 real application categories**: `paving_block_light, paving_block_heavy, floor_tile_indoor, floor_tile_outdoor, hollow_concrete_block, lightweight_partition_block, structural_concrete, nonstructural_concrete_fill, plastic_sand_paver, wall_cladding_panel, thermal_insulation_panel, kerb_stone`.

## Config-driven specs (single source of truth — never hard-code)
From `configs/m1_config.yaml` + `modules/m1_prediction/utils/schema.py`:
- **Inputs / ranges**: replacement_pct `0–40`, particle_size_mm `0.5–20`, wc_ratio `0.35–0.65`, additive_pct `0–30`, curing_temp_c `20–80`, curing_days `3–90`.
- **Plastic classes**: `PET, HDPE, LDPE, PVC, PP, Mixed`. **Additive classes**: `fly_ash, silica_fume, fibres, none`.
- **7 targets** + `TARGET_RANGES` for radar normalisation.
- Test standards (design spec): Compressive `IS 516`, Flexural `ASTM C78`, Split Tensile `IS 5816`, Water Absorption `IS 2185`, Durability `0–100 composite`.

From `configs/m2_config.yaml`: default weights `cs .40 / cost .25 / co2 .20 / diversion .15`; normalisation bounds; 3 scenarios. From `configs/m3_config.yaml`: score weights (carbon 30 / diversion 25 / recycled 20 / BIS 15 / green 10), BIS thresholds, green-rating thresholds, baseline CO₂ `365.71 kg/m³`.

## Existing wiring preserved (not touched)
- `app.py` (old) = HF dual-process launcher (uvicorn FastAPI `deployment/api/app:app` on :7861 + old `deployment/frontend/streamlit_app.py` on :7860). Kept in git history; `deployment/` left untouched and still runnable for the API-based deployment.
- New `app.py` becomes the direct-wired `st.navigation` Streamlit shell (no HTTP hop; `ui/data_bridge.py` imports the modules in-process). This is the natural entrypoint for a Streamlit HF Space.

## Gaps → mock fallback
1. **M4** unavailable until `faiss-cpu` is installed → `ui/data_bridge.py` catches and returns `ui/mock_data.py` recommendations. Everything M4-shaped mirrors the real 12 categories & dataclass fields so the swap is transparent once faiss is present.
2. **LIME / PDP / ICE**: not on any public contract and not loaded by default. Explainability SHAP tab uses **real** `PredictionResult.shap_values`; LIME contrastive is derived from SHAP negatives; PDP/ICE curves are illustrative mock (documented in-page).
3. Live per-slider re-prediction with the real ensemble is impractical (33 s cold / ~1–3 s warm). M1 page uses an explicit **Predict** button (cached resource) and seeds session with mock so all downstream pages render instantly before the first real run.
