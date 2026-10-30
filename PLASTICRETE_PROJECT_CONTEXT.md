# PlastiCrete.ai — project context for another model

This file is the project context for PlastiCrete.ai. It describes the built system, the runtime workflow, the numbers the code uses, and the numbers reported in the IEEE-style paper (`paper/main.tex` and `Research_Paper (2).pdf`).

**How to use this file**

- When the paper and the running code disagree, the running code is the system. Paper numbers are kept in their own section and are labelled as paper results or saved snapshots.
- A prediction, a gate status, a PDF, and a retrieved paper are a screen. They are not an IS cube test, a structural certificate, or a plant acceptance.
- Do not invent mix results. If a number is not in this file, it is not a stored project result.
- Design-chat and paper-drafting chat are omitted. Only the product, its data, its models, and its workflow are here.

Authors on the paper: Kritika Mandale, DSV Siddharth, Meet Tagalpallewa, Joe Francis, Praveen Sen, Stanly Wilson. Institution: St. Vincent Pallotti College of Engineering & Technology, Nagpur, Maharashtra, India. Repository named in the README: `https://github.com/kritikamandale/Plasticrete_ai`. Project lead named in the README: Kritika Mandale. API version in FastAPI: `1.1.0`.

---

## 1. What the system is

PlastiCrete.ai screens plastic-aggregate concrete mixes before a cube is cast. A user supplies eight mix variables. The system then:

1. Predicts seven mechanical and physical properties and a 90% interval (M1).
2. Searches recipes under constraints, using that same ensemble for strength and one shared mass-balance table for cost, CO₂, and plastic mass (M2).
3. Scores cradle-to-gate carbon and allows a product only when the conservative side of the interval clears that product’s own standard (M3). Structural concrete is never marked allowed.
4. Classifies one of twelve applications, drops any application the gate does not pass, and retrieves three published mixes by property distance (M4).
5. Writes an A4 PDF of the recipe, the interval, the gates, the mass balance, SHAP, and the analogues (M5).
6. Opens a local batch passport, with cube dates at day 7 and day 28, only when a gate status is `verification_batch` or `lab_trial`.

The problem the paper states: plastic-waste concrete properties vary with at least eight interacting variables, a 28-day cube cycle is too slow for routine screening, and prior models stop at a property (sometimes plus one cost objective). They do not name the Indian product, refuse the products the interval cannot support, or schedule the cube an uncertain prediction still requires. The README states a laboratory trial batch costs about ₹5,000 to ₹25,000 and needs a 28-day cure. That cost range is a project claim in the README, not a measured result in the repository.

---

## 2. Runtime sequence

This is the order the live studio and API actually run. Later modules consume earlier outputs. They do not re-predict strength on their own.

```
User edits 8 mix variables
        │
        ▼
POST /predict                         M1 ensemble
        │  7 means, 90% low/high, SHAP, uncertainty_flag
        ▼
POST /score          and          POST /recommend     (parallel after /predict)
        │                              │
        │  mass balance                │  RF primary + multilabel + scores
        │  4 use-class gates           │  then the same 4 gates drop or keep apps
        │  sustainability index        │  FAISS top-3 analogues
        │  green-credit counts         │  cost vs conventional M20
        │  remediation text            │
        ▼                              ▼
Studio shows overview, predictor, sustainability, recommender, explainability
        │
        ▼
POST /optimize                        optional, separate search
        │  Optuna TPE, 80 trials
        │  each trial: M1 predict_batch + shared mass balance + optional gate
        │  returns best recipe + up to 3 trade-off points
        ▼
POST /batches                         user saves a passport, or
POST /batches/schedule                opens one only if a gate asks for a cube
        │  due_7d = cast_date + 7, due_28d = cast_date + 28
        ▼
PATCH /batches/{id}                   lab writes cube values
        │  error_mpa = measured_28d − predicted mean
        │  plant offset is reported after 3 lab pairs
        ▼
POST /report/pdf  or  GET /batches/{id}/passport.pdf
```

Frontend call order in `MixContext.refreshAll`:

1. `POST /predict` with the eight inputs.
2. In parallel, `POST /score` and `POST /recommend`, each carrying the eight inputs, the seven means, and `ci_90_low` / `ci_90_high`.
3. Optimisation is a separate call from the optimiser tab. It does not reuse the displayed prediction; each candidate is scored inside the search.
4. Saving a batch stores mix, prediction, score, and recommendation together.
5. Scheduling (`POST /batches/schedule`) reads `score.use_class_gates`. If none of the statuses is `verification_batch` or `lab_trial`, it creates nothing.

The Vite app proxies `/api` to `http://localhost:8000` and strips the `/api` prefix. Default frontend port is 5173. Default API port is 8000. `VITE_API_URL` overrides the API base. `PUBLIC_APP_URL` (default `http://localhost:5173`) is the prefix of a batch QR URL: `{PUBLIC_APP_URL}/batch/{id}`.

---

## 3. Stack and layout

| Layer | What runs |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4. Routes are the History API, not React Router. |
| API | FastAPI, Pydantic v2, CORS from `CORS_ORIGINS` or `*`. Methods: GET, POST, PATCH. |
| M1 | XGBoost, Random Forest, PyTorch DNN, SHAP, LIME (configured), partial dependence (configured). |
| M2 live search | Optuna TPE, 80 trials, seed 42. Strength from M1. Cost, CO₂, plastic kilograms from the shared mass balance. |
| M2 on disk | Older Gaussian-process, XGBoost surrogate, NSGA-II, and MOPSO artefacts. The live `/optimize` path does not use them for the number it returns. |
| M3 live score | Deterministic mass balance, use-class gate, BIS rule checker (overwritten by the gate), green-credit mapper, weighted index. |
| M4 | Three Random Forests, FAISS FlatL2, 7-dimensional property space, 18 reference mixes. |
| M5 | ReportLab A4 PDF. |
| Passport | SQLite at `plasticrete_ai/data/batches/batches.sqlite` (gitignored). Photos beside it. No external language model. |

Python packages pinned in `plasticrete_ai/requirements.txt`: XGBoost `>=2.0.3,<3`, scikit-learn `>=1.4.2,<2`, PyTorch `>=2.2,<3`, Optuna `>=3.6.1`, NumPy, pandas, SciPy, SHAP, LIME, FAISS-cpu `>=1.8`, FastAPI `>=0.111`, Uvicorn, Pydantic `>=2.7`, ReportLab `>=4`, PyYAML, Loguru, pytest. CI (`.github/workflows/test.yml`) uses Python 3.11, runs `pytest modules -q` inside `plasticrete_ai`, then `python scripts/validate_kb.py`.

```
Plasticrete_ai/
├── README.md
├── paper/main.tex                     # paper source
├── plasticrete_ai/                    # backend
│   ├── configs/                       # m1–m4 YAML, standards.yaml
│   ├── data/raw/                      # uci_yeh_concrete.csv, PlastiCreteAI_M1_Final_2000.csv
│   ├── data/processed/                # master_dataset.csv, m2/m3/m4 training sets
│   ├── data/external/                 # mass balance, gates, ICE factors, costs
│   ├── data/batches/                  # SQLite + cube photos (not in git)
│   ├── deployment/api/app.py
│   ├── deployment/api/schemas.py
│   ├── models/m1|m2|m3|m4/
│   ├── modules/shared/                # mass_balance.py, use_class_gate.py
│   ├── modules/m1_prediction/
│   ├── modules/m2_optimization/
│   ├── modules/m3_sustainability/
│   ├── modules/m4_recommendation/
│   ├── modules/m5_report/
│   ├── modules/batch_passport/
│   ├── pipeline/                      # data + training scripts
│   ├── scripts/                       # audit, gap, KB validation
│   └── reports/                       # dataset card, gaps, label provenance
└── plasticrete_web/src/
    ├── api/client.ts
    ├── context/MixContext.tsx
    ├── routing.ts
    ├── pages/                         # Landing, Studio, Dashboard, Predictor,
    │                                  # Optimizer, Sustainability, Recommender,
    │                                  # Explainability, Standards, Tech, Batch
    ├── data/                          # copies of the two JSON tables
    └── lib/                           # TypeScript ports of mass balance and gate
```

Startup (`lifespan` in `app.py`) loads, in order: M1 ensemble from `models/m1/`, M2 surrogate files (load can fail without killing the API), M3 scorers, M4 classifiers and the FAISS index. A failed M1 load makes `/predict` return 503.

---

## 4. Inputs and outputs

Source of truth for names, classes, and ranges: `plasticrete_ai/modules/m1_prediction/utils/schema.py` and the Pydantic bounds in `schemas.py`. The root README still lists older bounds (replacement 0–50%, w/c 0.30–0.65, particle size 0.1–20 mm, curing 10–50 °C, curing 1–90 days, and extra plastic names PS, PVC crumb rubber, and SCM names GGBS and metakaolin). Those README bounds are not what the API accepts.

### 4.1 Eight inputs

| Field | Type | Accepted values |
|---|---|---|
| `plastic_type` | categorical | `PET`, `HDPE`, `LDPE`, `PVC`, `PP`, `Mixed` |
| `replacement_pct` | float | 0.0–40.0, percent by volume of fine aggregate |
| `particle_size_mm` | float | 0.5–20.0 |
| `wc_ratio` | float | 0.35–0.65, water / design binder |
| `additive_type` | categorical | `fly_ash`, `silica_fume`, `fibres`, `none` |
| `additive_pct` | float | 0.0–30.0, percent by mass of the 383 kg binder |
| `curing_temp_c` | float | 20.0–80.0 |
| `curing_days` | int | 3–90. The optimiser only tries 3, 7, 14, 28, 56, 90 |

`configs/m1_config.yaml` also lists plastic class `None`. The API validator uses `schema.py`, which does not include `None`. An unknown category is HTTP 422.

Default studio mix (`DEFAULT_MIX`):

| plastic | replacement % | size mm | w/c | additive | additive % | temp °C | days |
|---|---:|---:|---:|---|---:|---:|---:|
| PET | 15 | 4 | 0.45 | fly_ash | 10 | 27 | 28 |

The same eight values are written into the URL query: `plastic`, `rep`, `size`, `wc`, `additive`, `add`, `temp`, `days`.

### 4.2 Seven outputs

Column order is fixed. M2 `predict_batch` uses this index order.

| Index | Field | Unit | Physical range used for CTGAN rejection |
|---:|---|---|---|
| 0 | `compressive_strength_mpa` | MPa | 0–90 |
| 1 | `flexural_strength_mpa` | MPa | 0–15 |
| 2 | `split_tensile_mpa` | MPa | 0–10 |
| 3 | `density_kgm3` | kg/m³ | 1200–2600 |
| 4 | `water_absorption_pct` | % | 0–25 |
| 5 | `thermal_conductivity_wm` | W/m·K | 0.10–2.50 |
| 6 | `durability_index` | 0–100 composite | 0–100 |

`PredictionResult` also returns `ci_low`, `ci_high`, `shap_values` (per target, per feature), `uncertainty_flag`, and `low_coverage_targets`.

### 4.3 Derived features inside M1

After categorical encoding, and before scaling:

- `log_particle_size_mm` = log1p(particle size)
- `log_curing_days` = log1p(curing days)
- `is_plain_concrete` = 1 when plastic type is the string `None` or encoded class index 6
- `replacement_pct_x_wc_ratio`
- `replacement_pct_x_additive_pct`

Continuous inputs use `RobustScaler`. Targets use `StandardScaler`. Missing inputs use `KNNImputer` with 5 neighbours. Missing targets are dropped property by property. No imputed label enters a loss.

### 4.4 Twelve applications

| id | Display name | Use class |
|---|---|---|
| `paving_block_light` | Light paving blocks | paver |
| `paving_block_heavy` | Heavy duty pavers | paver |
| `plastic_sand_paver` | Plastic-sand composite paver | paver |
| `floor_tile_outdoor` | Outdoor patio tiles | paver |
| `kerb_stone` | Kerb and gutter stones | paver |
| `hollow_concrete_block` | Hollow masonry blocks | hollow_block |
| `lightweight_partition_block` | Lightweight partition blocks | hollow_block |
| `floor_tile_indoor` | Indoor floor tiles | solid_block |
| `wall_cladding_panel` | Wall cladding panels | solid_block |
| `nonstructural_concrete_fill` | Non-structural fill | solid_block |
| `structural_concrete` | Beams and columns | structural |
| `thermal_insulation_panel` | Thermal and acoustic panels | none configured |

`thermal_insulation_panel` has no row in `use_class_gates.json`. `status_for_application` therefore returns `refused` with the message that no use-class standard is configured. Suitability threshold in `m4_config.yaml` is 55. The live recommender does not filter on 55; it filters on the gate.

---

## 5. M1 — property predictor

### 5.1 Model

For each of the seven properties, three learners are trained separately and combined as

`y_hat = w_xgb * f_xgb + w_rf * f_rf + w_dnn * f_dnn`

with weights ≥ 0 and summing to 1. The weight of a learner is its cross-validated R² on that property, renormalised. Fallback weights if CV scores are missing: XGBoost 0.40, Random Forest 0.35, DNN 0.25.

| Learner | Settings on disk |
|---|---|
| XGBoost | up to 1000 rounds, max depth 6, learning rate 0.05, subsample 0.8, colsample 0.8, min child weight 3, gamma 0.1, reg alpha 0.1, reg lambda 1.0, early stopping 50 rounds, `tree_method=hist`. Optuna budget if tuning is turned on: 100 trials, 3600 s. |
| Random Forest | 500 trees, OOB scoring, `max_features=sqrt`, min samples split 4, min samples leaf 2. |
| DNN | Hidden widths 256 / 128 / 64 / 32, ReLU, batch norm, dropout 0.25. Adam, up to 300 epochs, batch 32, learning rate 0.001, weight decay 1e-4, early stopping patience 30, gradient clip 1.0. |
| Transfer | Pretrain 100 epochs at lr 0.001, fine-tune 200 epochs at lr 0.0003, freeze layers until index 2. Pretrain sources named in config: UCI Yeh and a Mendeley rubberized-concrete file. The master CSV that was actually evaluated contains UCI Yeh plus `PlastiCreteAI_M1_Final_2000` only. |
| CTGAN | Config asks for 500 synthetic rows, 300 epochs, kept only inside the physical ranges. The evaluated master CSV has 0 rows tagged synthetic in val or test. |

A target with fewer than 50 labelled rows is skipped (`min_coverage_rows`).

### 5.2 The 90% interval

Single prediction (`Ensemble.predict`):

- XGBoost point, Random Forest mean and tree standard deviation, DNN mean and standard deviation from Monte Carlo dropout with T = 50 forward passes.
- Combined standard deviation is the maximum of the forest standard deviation, the dropout standard deviation, and the standard deviation of the three point predictions.
- Interval is `mean ± 1.645 * std` after inverse-transforming to original units. 1.645 is the normal z for a central 90% interval. Config also stores percentile keys 5 and 95; the code path that serves `/predict` uses z = 1.645.
- `uncertainty_flag` is true when, for any target with a non-zero mean, `(high − low) / |mean|` exceeds that target’s threshold.

Relative-width thresholds:

| Target | Threshold |
|---|---:|
| compressive_strength_mpa | 1.50 |
| flexural_strength_mpa | 1.00 |
| split_tensile_mpa | 1.80 |
| density_kgm3 | 0.10 |
| water_absorption_pct | 1.00 |
| thermal_conductivity_wm | 0.50 |
| durability_index | 1.00 |

Batch prediction used inside M2 (`predict_batch`) skips SHAP and skips Monte Carlo dropout. Its interval uses the forest standard deviation only, still with z = 1.645. SHAP on the single-prediction path is TreeSHAP through the saved explainer, background sample size 100 in config. LIME is configured for 1000 samples and PDP for grid resolution 50. The paper states that native LIME and PDP figures are not what the live interface shows.

### 5.3 Weights on disk

Order is XGBoost, Random Forest, DNN. Rounded values match the paper table.

| Property | XGBoost | RF | DNN |
|---|---:|---:|---:|
| compressive_strength_mpa | 0.3955 | 0.3845 | 0.2201 |
| flexural_strength_mpa | 0.3466 | 0.3430 | 0.3103 |
| split_tensile_mpa | 0.3487 | 0.3426 | 0.3086 |
| density_kgm3 | 0.3430 | 0.3417 | 0.3154 |
| water_absorption_pct | 0.3511 | 0.3383 | 0.3106 |
| thermal_conductivity_wm | 0.3555 | 0.3467 | 0.2978 |
| durability_index | 0.3471 | 0.3362 | 0.3167 |

### 5.4 Test metrics of the weights on disk

From `models/m1/evaluation_report.json`. These are the metrics of the saved run. They were not recomputed by the audit scripts. The report’s own `status` field is `[PASS]` for every row, including properties whose R² sits outside the “expected range” column. Treat the expected range as the planning band in the YAML, and the R² column as the measured test score.

| Property | Test R² | RMSE | MAE | MAPE % | n_test | Planning band in YAML |
|---|---:|---:|---:|---:|---:|---|
| compressive_strength_mpa | 0.9104 | 5.6011 MPa | 3.6123 MPa | 13.69 | 455 | 0.88–0.94 |
| flexural_strength_mpa | 0.9435 | 0.319 MPa | 0.2205 MPa | 8.05 | 282 | 0.82–0.90 |
| split_tensile_mpa | 0.9393 | 0.3731 MPa | 0.2501 MPa | 15.08 | 282 | 0.80–0.88 |
| density_kgm3 | 0.8874 | 30.2412 kg/m³ | 23.7415 | 1.06 | 282 | 0.90–0.96 |
| water_absorption_pct | 0.8928 | 0.2961 | 0.233 | 7.84 | 282 | 0.75–0.85 |
| thermal_conductivity_wm | 0.9290 | 0.0578 | 0.045 | 4.69 | 282 | 0.65–0.78 |
| durability_index | 0.9192 | 4.2642 | 3.393 | 9.46 | 282 | 0.70–0.82 |

Compressive strength is the only target present on the UCI pretraining rows, which is why its test count is 455 and the other six are 282. Density and water absorption are the weakest of the seven. Both appear in product gates, so those two outputs are meant to be read with the interval.

The paper compares compressive R² 0.9104 with Asif et al. multi-expression programming 0.88 and gene-expression programming 0.87, and says the datasets differ so the margin is only indicative.

Model-card string stored on every passport: `m1-ensemble evaluation_report.json compressive R2 0.9104`.

Retraining policy in the model card: do not overwrite `models/m1` until a grouped split can be built from paper identifiers that are actually columns in the table. They are not.

---

## 6. Shared mass balance

`modules/shared/mass_balance.py` is the only bill of materials. M2, M3, M4 cost, M5, and the sustainability page all call `compute`. Quantities are integer hundredths of a kilogram so a spreadsheet of the displayed rows matches the totals. Factors live in `data/external/mass_balance_factors.json` (`table_id`: `plasticrete-mass-balance-v1`, factor date 2026-03-01). The web app carries a copy of the same JSON.

Basis string in the file: IS 10262:2019 M20 reference per cubic metre. Plastic replaces fine aggregate by volume at sand SSD density 2650 kg/m³. An SCM replaces cement by mass. Water is the water/binder ratio times the 383 kg design binder, so water does not change when SCM replaces cement. Factors are cradle-to-gate materials only. Haul is not included.

### 6.1 Reference quantities

| Item | Value |
|---|---:|
| Design binder (cement before SCM split) | 383 kg/m³ |
| Fine aggregate before replacement | 680 kg/m³ |
| Coarse aggregate | 1210 kg/m³ |
| Aggregate SSD density | 2650 kg/m³ |
| Baseline embodied carbon | 365.71 kg CO₂e/m³ |
| Baseline source | Goh et al. 2022 conventional M20 |
| PET bottle mass used for the bottle count | 0.025 kg (25 g) |
| Batching overhead | 1.00 unit × ₹50 per m³, 0 kg CO₂e |

Arithmetic:

- `additive_kg = binder * additive_pct / 100`, and 0 if additive type is `none`.
- `cement_kg = 383 − additive_kg`.
- `water_kg = wc_ratio * 383`. At w/c 0.50 this is 191.5 kg. It does not depend on the SCM split.
- `sand_removed = replacement_pct/100 * 680`. Remaining sand is 680 minus that.
- `plastic_kg = (replacement_pct/100) * 680 * plastic_density / 2650`.
- Bottle equivalents: whole bottles from plastic mass / 0.025 kg, integer arithmetic in the code.
- CO₂ saving percent = `(365.71 − mix_co2) / 365.71 * 100`.
- `conventional_mix()` is plastic replacement 0, additive `none`, w/c 0.50. That is the M20 bill M4 compares against. It is not the 723 kg sand / 1102 kg coarse bill stored in the old M4 market JSON.

Particle size and curing do not change the mass balance.

### 6.2 Densities, emission factors, prices

Emission factors are kg CO₂e per kg. Plastic factors are negative avoided-burden credits. Overhead emits nothing.

| Key | Density kg/m³ | kg CO₂e/kg | ₹/kg |
|---|---:|---:|---:|
| cement_opc | — | 0.872 | 7.00 |
| sand_river | — | 0.0048 | 1.50 |
| coarse_aggregate | — | 0.0048 | 1.20 |
| water | — | 0.0003 | 0.10 |
| fly_ash | — | 0.004 | 1.20 |
| silica_fume | — | 0.014 | 25.00 |
| fibres | — | 0 | 8.00 |
| none | — | 0 | 0 |
| PET | 1380 | −1.32 | 45 |
| HDPE | 960 | −1.20 | 38 |
| LDPE | 920 | −1.25 | 35 |
| PVC | 1400 | −0.95 | 30 |
| PP | 905 | −1.18 | 42 |
| Mixed | 1100 | −1.10 | 25 |
| overhead | — | 0 | 50 per m³ |

Sources named inside the JSON: ICE v4.1 A1–A3 via `ice_emission_factors_extended.csv` for emissions; `material_costs_inr.json` for cement, sand, aggregate, water, SCM; `plastic_props_m2.json` for plastic ₹/kg; `plastic_density_lookup.json` for densities. A user-entered ₹/kg is not a field the mass balance reads. The table is the price.

`models/m4/m4_market_prices.json` still holds a different price list (cement ₹9/kg, sand ₹1.8, PET ₹3.5, and so on) and a different conventional M20 (383 kg cement, 723 kg sand, 1102 kg coarse, 191.5 kg water). Live cost-benefit does not use those rupee rates. It uses the mass-balance table. It does use `product_area_yield` from that market file:

| Application | m² per m³ |
|---|---:|
| paving_block_light | 6 |
| paving_block_heavy | 5 |
| floor_tile_indoor | 10 |
| floor_tile_outdoor | 10 |
| hollow_concrete_block | 8 |
| lightweight_partition_block | 10 |
| structural_concrete | 1 |
| nonstructural_concrete_fill | 1 |
| plastic_sand_paver | 7 |
| wall_cladding_panel | 8 |
| thermal_insulation_panel | 12 |
| kerb_stone | 4 |

Per square metre cost = per cubic metre cost / that yield. Saving = conventional cost − plastic-mix cost. Percent saving = saving / conventional cost × 100.

---

## 7. M2 — mix search

### 7.1 What `/optimize` does now

`modules/m2_optimization/model/optimizer.py` runs Optuna TPE (`TPESampler`, seed 42) for 80 trials, direction minimize. Each trial:

1. Samples plastic type (fixed if the request set one, otherwise all six), additive type, replacement from 0 to `replacement_pct_max`, particle size 0.5–20, w/c 0.35–0.65, additive percent 0–30, curing temperature 20–80, curing days in {3, 7, 14, 28, 56, 90}.
2. Builds the mass balance.
3. Calls M1 `predict_batch` for the seven means and the 90% bounds.
4. Rejects the trial (objective `1e9`) when any constraint fails.
5. Otherwise scores a weighted sum and returns the negative of that score.

Constraints:

- predicted compressive mean ≥ `compressive_strength_min` (API default 20 MPa; the optimizer function default if the key is missing is 10)
- optional maximum cost ₹/m³
- optional maximum density kg/m³
- optional minimum plastic kg/m³
- optional `use_class` in `paver`, `hollow_block`, `solid_block`, `structural`. The trial passes only when that class status is `allowed` or `lab_trial`. `verification_batch` and `refused` fail the constraint. Structural can pass the search only as `lab_trial`, because the gate never returns `allowed` for it.

Weights must sum to 1 within 0.01. API defaults:

| Weight | Default |
|---|---:|
| `weight_compressive` | 0.40 |
| `weight_cost` | 0.30 |
| `weight_co2` | 0.20 |
| `weight_plastic_content` | 0.10 |

Normalised composite, higher is better, then negated for Optuna:

```
n_cs   = cs / 60
n_cost = 1 − min(cost / 5500, 1)
n_co2  = 1 − min(max(co2, 0) / 380, 1)
n_div  = min(plastic_kg / 180, 1)
score  = 0.40*n_cs + 0.30*n_cost + 0.20*n_co2 + 0.10*n_div
```

The denominators are `CS_NORM_MAX=60`, `COST_NORM_MAX=5500`, `CO2_NORM_MAX=380`, `DIV_NORM_MAX=180`.

Response fields: `best_mix` (eight inputs plus cement, sand, coarse, plastic, water, additive kilograms), `predicted_cs_mpa`, `predicted_cs_low`, `predicted_cs_high`, cost, CO₂, plastic kg, `composite_score`, `feasible`, `prediction_source="m1"`, the full `mass_balance`, and up to three `tradeoff_points`.

Trade-off labels, taken from the feasible pool of that same search, duplicates removed:

- `balanced` — the chosen weighted point
- `max_strength`
- `max_diversion`
- `min_cost`

The API also accepts `plastic_kg_available` and `processing_cost_inr_per_kg`. If available kilograms and plastic kg/m³ are both present, `monthly_m3 = plastic_kg_available / plastic_kg_m3`. The processing cost is echoed. It is not substituted into the factor table.

`mode` must be `constrained` or `scenario`. The live objective does not branch on that string beyond storing it on the response.

`modules/batch_passport/suggest.py` ranks an optimiser’s trade-off points by compressive interval width `(high − low)`. The widest interval is the next cube the validation note says to cast. Five mixes are described there as a pilot, not a validation of the model.

### 7.2 Saved surrogate snapshot (not the live search)

`models/m2/m2_model_manifest.json` records an earlier training run dated 2026-06-27, 2125 dataset rows, 67 columns, seed 42. Those surrogates are still loaded at startup. The live objective does not call them.

| Surrogate | Validation R² | Error |
|---|---:|---|
| Gaussian process, Matérn-5/2 + ARD, composite score, trained on 800 points | 0.9843 | RMSE 0.00888 |
| XGBoost cost | 0.9864 | RMSE ₹73.72/m³ |
| XGBoost CO₂ | 0.9927 | RMSE 5.5 kg CO₂e/m³ |
| XGBoost compressive strength | 0.9864 | RMSE 2.014 MPa, MAE 1.396 MPa |
| XGBoost plastic diversion | 0.9993 | RMSE 0.413 kg/m³ |

Five-fold means on that same snapshot: CS R² 0.9849 (std 0.001), cost 0.9821, CO₂ 0.9907, diversion 0.9993.

NSGA-II on that run: 80 non-dominated solutions, hypervolume 85576553.44. Bayesian optimisation best composite score 0.7307.

Bayesian demo mix (LDPE, silica fume, replacement 8.474%, particle size 0.5 mm, w/c 0.35, additive 30%, cure 20 °C, 90 days):

| Source of the compressive number | MPa |
|---|---:|
| `bo_demo_result.json` | 44.408 |
| `sensitivity_analysis.json` base, same mix | 55.689 |
| Gap between those two surrogate files | 11.281 |
| M1 ensemble on the same mix | 45.463 |
| M1 90% interval on that mix | 21.366 to 69.560 |
| Absolute gap, BO file vs M1 | 1.055 |
| Absolute gap, sensitivity file vs M1 | 10.226 |

`reports/m2_vs_m1_gap.json` labels this a surrogate-versus-ensemble gap. The live optimiser sets `prediction_source` to `m1`.

Sensitivity on that same mix, ±10% of each continuous input, from the surrogate file. Largest move is water/cement, about 3 MPa. Particle size does not move the surrogate.

| Input | +10% Δ CS MPa | −10% Δ CS MPa | max \|Δ\| |
|---|---:|---:|---:|
| replacement_pct | −0.864 | +0.303 | 0.864 |
| particle_size_mm | 0 | 0 | 0 |
| wc_ratio | −3.039 | 0 | 3.039 |
| additive_pct | 0 | +0.679 | 0.679 |
| curing_temp_c | +0.702 | 0 | 0.702 |
| curing_days | 0 | −0.295 | 0.295 |

### 7.3 Three scenario mixes stored from the paper’s optimisation run

From `models/m2/scenario_results.json`. These are the three points in the paper’s trade-off figure. They are a saved scenario file, not a response from the current 80-trial TPE search.

| Optimised for | Plastic | Additive | Repl. % | Size mm | w/c | Add. % | Temp °C | Days | CS MPa | Cost ₹/m³ | CO₂ kg/m³ | Plastic kg/m³ |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Strength | LDPE | none | 6.2 | 0.5 | 0.357 | 30.0 | 20 | 90 | 56.45 | 6686 | 303.9 | 8.4 |
| Cost | LDPE | silica_fume | 19.1 | 2.0 | 0.35 | 0.0 | 72.4 | 86 | 34.52 | 4758 | 248.8 | 22.5 |
| Sustainability | Mixed | silica_fume | 40.0 | 3.6 | 0.35 | 0.0 | 80 | 90 | 17.35 | 5487 | 169.2 | 61.5 |

The paper’s reading of that table: diversion rises only as strength falls. The sustainability mix diverts 61.5 kg/m³ at 17.35 MPa. The strength mix reaches 56.45 MPa and diverts 8.4 kg/m³. The cost mix is the cheapest. The paper’s scalarised weights were (0.40, 0.25, 0.20, 0.15) for strength, cost, CO₂, diversion. The live API defaults are (0.40, 0.30, 0.20, 0.10).

Paper cost example on the cost mix: saving ₹1,644/m³ (25.7%) against its conventional M20 bill, 22.5 kg plastic diverted, and at a paving yield of 6 m²/m³ a material cost of about ₹793/m². That 25.7% uses the paper’s conventional bill (383 kg cement, 723 kg sand, 1102 kg coarse, 191.5 kg water), not the live 680 kg sand bill. Recompute savings from `conventional_mix()` if the number has to match the API.

The paper also describes a 50-iteration Bayesian point: LDPE with silica fume, low w/c, long cure, about 44 MPa, about ₹5,000/m³, about 10 kg plastic per m³. That is the BO demo family (the file’s CS is 44.41 MPa on the mix in section 7.2). Plastic mass in the sentence (“about 10 kg”) is the paper’s rounding of that demo, not the 8.4 kg strength scenario.

---

## 8. M3 — sustainability and the use-class gate

`score_mix` does five things and then overwrites the compliance flag.

1. `LCACalculator.compute` calls the shared mass balance and copies cement, water, sand, coarse, plastic, additive, component CO₂, total CO₂, saving, and bottle count.
2. `evaluate_classes` runs the four gates on the seven means and the 90% interval.
3. `BISChecker.check` runs a separate seven-clause rule set on the means only.
4. The pass flag the caller sees is then replaced: `bis_overall_pass` is true only when some non-structural gate status is `allowed`. `n_standards_passed` is the count of gates whose status is `allowed` or `lab_trial`.
5. The sustainability index uses that gate fraction. Green-rating points are still computed and returned as IGBC, GRIHA, and LEED counts. They are not added into the index (`n_green` is forced to 0).
6. Remediation text names the failing or crossing gate. `estimated_score_gain` is always 0. The advisor does not invent a megapascal or carbon delta.

### 8.1 Index

Weights in `configs/m3_config.yaml` (they sum to 100):

| Component | Points | Normalisation |
|---|---:|---|
| Carbon | 30 | clip((co2_saving_pct − (−50)) / 130, 0, 1) |
| Plastic diversion | 25 | clip(plastic_kg_m3 / 200, 0, 1) |
| Recycled content | 20 | clip(replacement_pct / 40, 0, 1) |
| Gate fraction | 15 | (number of gates in {allowed, lab_trial}) / (number of gates) |
| Green rating | 10 | 0 in the live aggregator |

Grades: A ≥ 80, B ≥ 60, C ≥ 40, otherwise D.

The paper’s equation still adds `0.10 * C_green`. The running index does not.

### 8.2 Use-class gate (this is the compliance verdict)

Table `plasticrete-use-class-gates-v1`, factor date 2026-03-01. `configs/standards.yaml` repeats the thresholds and sets `verified: false` because the repository does not contain the official BIS text.

| id | Standard | CS minimum | Water absorption | Density | Structural flag |
|---|---|---:|---|---|---|
| paver | IS 15658 | 30 MPa | ≤ 6% by mass | none | no |
| hollow_block | IS 2185 (Part 1) | 3.5 MPa | none | none | no |
| solid_block | IS 2185 (Part 1) | 5.0 MPa | none | none | no |
| structural | IS 456 M20 | 20 MPa | none | 1800–2500 kg/m³ | yes |

Status rules, in order:

1. If the interval is missing and the mean clears: structural → `lab_trial`; any other class → `verification_batch`; mean fails → `refused`.
2. Conservative side of a present interval: lower compressive strength, upper water absorption, lower density against a floor, upper density against a cap.
3. If that conservative side clears and the class is structural → `lab_trial`. Message: the lower bound clears the grade; screen for a lab trial; this is not a certificate.
4. If that side clears and the class is not structural → `allowed`.
5. If only the mean clears → `verification_batch`. Message: cast one verification batch; the 90% interval crosses the grade line.
6. Otherwise → `refused`.

A missing interval never produces `allowed`.

The paper’s Table of representative thresholds is a different, earlier sketch: paving CS ≥ 20 MPa and absorption ≤ 5% and density ≥ 1800; structural also requiring durability ≥ 65; a thermal class with k ≤ 0.6, density ≤ 1200, CS ≥ 2. The live gate table above is what the API evaluates. There is no thermal-class gate.

### 8.3 BIS checker that runs and is then overwritten

`BISChecker` still grades the mean. It is not the flag returned as `bis_overall_pass`.

| Check | Rule on the mean |
|---|---|
| IS 516 grade | M30 ≥ 30, M25 ≥ 25, M20 ≥ 20, M15 ≥ 15, M10 ≥ 10, else Below_M10. “Compliant” if CS ≥ 10. |
| IS 1237 | CS ≥ 30 MPa and water absorption ≤ 1%. |
| IS 2185 Part 1 | CS ≥ 3.5 MPa. |
| IS 2185 Part 2 | CS ≥ 3.5, density ≤ 1500 kg/m³, absorption ≤ 10%. |
| IS 5816 | split tensile ≥ max(1.5 MPa, 0.10 × compressive). |
| NBC structural | CS ≥ 20 and density in 1800–2500. |
| NBC non-structural | CS ≥ 5 and density ≤ 1800. |

Its own overall pass would be “at least 3 of these 7”. `score_mix` replaces that with the gate result before the response is built. Calling the historical M3 classifier accuracy a hit rate on built products is rejected by `reports/label_provenance.md`. Those labels were produced by rules of this kind.

### 8.4 Green credits (returned, not added to the index)

| Credit | Awarded when |
|---|---|
| IGBC recycled content | plastic kg/m³ ≥ 50 |
| IGBC regional materials | plastic type is PET, HDPE, or Mixed |
| IGBC indoor air | thermal conductivity ≤ 0.60 W/m·K |
| GRIHA embodied energy | CO₂ saving ≥ 10% |
| GRIHA waste | plastic kg/m³ ≥ 100 |
| LEED BPDO-style | replacement ≥ 10% |
| LEED construction waste | plastic kg/m³ ≥ 75 |

`igbc_total_credits`, `griha_material_criterion_pts`, `leed_total_points`, and `total_green_credits` are the sums of those 0/1 flags. Maximum total is 7.

### 8.5 M3 model-file metrics (rule-label agreement)

From `models/m3/m3_evaluation_report.json`. Dataset 2200 rows, 15 features (8 mix variables encoded plus 7 properties), split 1540 / 330 / 330, seed 42. The live `/score` path is the rule engine in section 8, not these regressors.

| Model | Score |
|---|---|
| Carbon regressor | R² 0.9978, RMSE 7.1947, MAE 5.2478, MAPE 17.39% |
| Score regressor | R² 0.9951, RMSE 1.3605, MAE 1.0186, MAPE 1.77% |
| CO₂-saving regressor | R² 0.9977, RMSE 2.0256, MAE 1.5139, MAPE 2.24% |
| Diversion regressor | R² 0.9971, RMSE 7.0105, MAE 4.4662 |
| BIS classifier | accuracy 0.9939, weighted F1 0.9945, ROC AUC 0.9992 |
| IS 1237 classifier | accuracy 1.0, weighted F1 1.0 |
| NBC structural classifier | accuracy 0.9909, weighted F1 0.9901, ROC AUC 0.9984 |
| Green-rating scorer | R² 0.9951, RMSE 0.1101, MAE 0.0121 |
| Grade classifier | accuracy 0.9152, weighted F1 0.9157 |
| Remediation classifier | accuracy 0.9364, weighted F1 0.9341 |

The paper rounds the BIS screen to 99.4%, the grade classifier to 91.5%, and remediation to 93.6%. The paper says the grade classifier is weaker because mixes near a grade boundary fall on opposite sides of a hard cut. It also says these labels are easier than a plant cube.

M3 dataset generation config: 2200 rows = 1400 from M1 predictions + 600 from physics formulas + 200 augmented, seed 42.

---

## 9. M4 — application recommender

### 9.1 Live `recommend` order

Feature vector: the eight mix variables (plastic and additive label-encoded) plus the seven properties, then the saved scaler.

Encodings:

| plastic_type | code | additive_type | code |
|---|---:|---|---:|
| PET | 0 | none | 0 |
| HDPE | 1 | fly_ash | 1 |
| LDPE | 2 | silica_fume | 2 |
| PVC | 3 | fibres | 3 |
| PP | 4 | | |
| Mixed | 5 | | |

Then:

1. Primary Random Forest: class id and confidence = max class probability × 100, one decimal.
2. Multilabel Random Forest: the applications predicted as 1.
3. Score regressor: a 0–100 suitability per application, sorted high to low.
4. The same four use-class gates as M3, using the means and the interval.
5. `suitable_applications` keeps only multilabel hits whose gate is `allowed` or `lab_trial`.
6. If the classifier’s primary is not in that passing set, and some application does pass, the primary moves to the passing application with the highest suitability score. Confidence stays the classifier’s original max probability. The gate message is what the studio shows.
7. `verification_applications` lists applications whose gate is `verification_batch`.
8. Cost-benefit uses the shared mass balance and `conventional_mix()`, divided by the yield of the (possibly replaced) primary application.
9. FAISS FlatL2 returns the top 3 knowledge-base rows in the scaled 7-property space. A neighbour is a precedent. It does not override the gate. `verified` on the analogue dataclass defaults to true in the schema; that flag is not a laboratory certificate.

### 9.2 Classifier metrics on disk

From `models/m4/m4_evaluation_report.json`. The paper’s macro-F1 0.84 is the cross-validated figure 0.8395, not the test macro-F1.

| Primary classifier | Value |
|---|---:|
| Accuracy | 0.9947 |
| Macro-F1, test | 0.7487 |
| Weighted F1 | 0.9933 |
| 5-fold macro-F1 mean | 0.8395 |
| 5-fold macro-F1 std | 0.0862 |

The paper’s reading: headline accuracy follows the common classes and should not be quoted alone. Eleven of twelve multilabel F1 scores are above 0.92. Outdoor floor tile is the weak class.

| Application | Multilabel F1 | Multilabel accuracy | Score regressor R² | Score MAE |
|---|---:|---:|---:|---:|
| paving_block_light | 0.9945 | 0.992 | 0.9968 | 0.62 |
| paving_block_heavy | 0.9263 | 0.9813 | 0.9965 | 0.47 |
| floor_tile_indoor | 0.9231 | 0.992 | 0.9975 | 0.43 |
| floor_tile_outdoor | 0.7500 | 0.9947 | 0.9973 | 0.34 |
| hollow_concrete_block | 1.0000 | 1.000 | 0.9819 | 0.07 |
| lightweight_partition_block | 1.0000 | 1.000 | 0.9950 | 0.10 |
| structural_concrete | 0.9639 | 0.952 | 0.9962 | 0.88 |
| nonstructural_concrete_fill | 0.9987 | 0.9973 | 0.9938 | 0.09 |
| plastic_sand_paver | 0.9971 | 0.9973 | 0.9988 | 0.20 |
| wall_cladding_panel | 1.0000 | 1.000 | 0.9929 | 0.28 |
| thermal_insulation_panel | 1.0000 | 1.000 | 0.9997 | 0.11 |
| kerb_stone | 0.9845 | 0.984 | 0.9975 | 0.58 |

RAG index: FAISS FlatL2, 18 mixes, 7 embedding dimensions. Five rows were removed because stored `wc_ratio` was 0 and the source table is not in the repo (`reports/kb_dropped.md`): `IFT_2023_01`, `IFT_2023_02`, `IFT_2023_03` (DOI 10.1016/j.heliyon.2023.e17107) and `STR_2024_01`, `STR_2024_02` (DOI S2352012424004375). The index was rebuilt from the remaining rows with the existing property scaler.

`reports/rules_vs_model.json` checks six hand mixes. On all six the classifier’s primary was `hollow_concrete_block` and the gate agreed, so disagreement count is 0 of 6. The file’s own label: agreement with the use-class rule, not accuracy against ground truth. One of the six is a verification batch (the default PET / 15% / fly ash mix). The other five are `allowed` on the hollow-block gate.

| Mix | Gate on the classifier’s primary |
|---|---|
| PET, 15%, 4 mm, w/c 0.45, fly ash 10%, 27 °C, 28 d | verification_batch, IS 2185 Part 1, interval crosses the line |
| HDPE, 20%, 6 mm, w/c 0.50, silica fume 8%, 27 °C, 28 d | allowed |
| LDPE, 30%, 2 mm, w/c 0.55, no SCM, 27 °C, 28 d | allowed |
| PP, 10%, 4 mm, w/c 0.40, fly ash 15%, 27 °C, 28 d | allowed |
| PVC, 5%, 8 mm, w/c 0.42, fibres 5%, 27 °C, 28 d | allowed |
| Mixed, 25%, 4 mm, w/c 0.48, fly ash 10%, 27 °C, 28 d | allowed |

---

## 10. Batch passport and the scheduler

SQLite, one plant, a few users. The scheduler calls no language model. It is deterministic.

`POST /batches/schedule` (`open_if_gate_requires_cube`):

- Read `score.use_class_gates`.
- If any status is `verification_batch` or `lab_trial`, create a passport from the prediction already computed and set `due_7d` and `due_28d` to the cast date plus 7 and 28 calendar days.
- If every status is `allowed` or `refused`, create nothing and return `{opened: false, batch: null}`.
- Structural concrete produces a laboratory-trial passport even when the lower bound clears the grade, because its status is `lab_trial`, which is in the open set.
- A class the bound clearly allows produces no cube schedule by itself. Another class on the same mix can still open one.

`POST /batches` always creates a passport, whether or not a gate asked for a cube. That is the manual save. The schedule route is the automatic one.

Batch id format: `B` plus 8 uppercase hex characters.

Columns kept: plant name, cast date, the four JSON blobs (mix, prediction, score, recommendation), predicted CS mean and 90% bounds, measured CS at 7 and 28 days, measured absorption, error in MPa, model version, notes, lab name, operator, cube size, cube count, individual cube values, cube standard deviation, test standard, source, due dates, photo path.

Measurement rules:

- If individual cube values are sent, the store computes the mean and the coefficient of variation (standard deviation / mean) and writes the mean as `measured_cs_28d`.
- If CV > 0.15, the API returns 422 unless `confirm_high_cv` is true.
- A written measurement with no `source` is stored as `lab`.
- `error_mpa = measured_cs_28d − predicted_cs_mean`, rounded to 3 decimals.
- Photos: JPEG, PNG, or WebP, at most 5 MB.
- CSV import and export exist. Predicted columns on export are the values stored with the batch, not a fresh inference.

Plant calibration (`calibration`):

- Uses rows for that `plant_name` where both measured 28-day strength and predicted mean exist, and `source` is `lab` (null source counts as lab).
- Ready when the plant has at least 3 such pairs.
- Reports mean error and, once ready, the residual standard deviation of those errors.
- Direction text: under the model if mean error < −0.05 MPa, over if > 0.05, otherwise “in line”.
- The paper states this offset is defined and is not a field result, because the repository has no plant cube campaign. `docs/LIMITATIONS.md` says the same: a passport stays unvalidated until a lab writes measurements with `source=lab`.

Lab recording template (`docs/lab_protocol_IS516.md`), which is a template and contains no measured results:

1. Cast three 150 mm cubes.
2. Cure them with the cast date on the passport.
3. Test one set at 7 days and the remaining cubes at 28 days.
4. Enter each cube, not a remembered average.
5. CV above 0.15 needs an explicit confirm.
6. Photograph the cube onto the same passport.

`docs/validation_plan.md`: call `/optimize`, rank `tradeoff_points` by interval width, cast the widest first. It deliberately does not list megapascal targets.

`GET /batches/due?today=YYYY-MM-DD` lists passports whose due date is that day or earlier and whose measurement is still empty.

---

## 11. M5 — PDF

`POST /report/pdf` takes mix, prediction, score, recommendation, optional session id, optional batch id. If a batch id is set and missing, the API returns 404. The file name is `plasticrete_report_{session}.pdf`.

`GET /batches/{id}/passport.pdf` rebuilds the same report from the stored blobs and the batch QR.

Sections, in generator order:

1. Header and footer with mix and session id.
2. Mix recipe.
3. Mass balance per m³, from the shared table when the score carries it.
4. Predicted properties with the 90% interval and the uncertainty flag.
5. Use-class gate (standard, status, message).
6. LCA and sustainability score, then the green-credit counts, with the note that those counts are not added into the index.
7. SHAP for compressive strength.
8. Remediation text.
9. Top 3 literature analogues.
10. Recommended application and cost-benefit.
11. Batch passport block and QR when a batch is attached.

The PDF does not replace a cube test.

---

## 12. HTTP API

| Method | Path | Role |
|---|---|---|
| GET | `/health` | `{status: ok, module: M1}` |
| GET | `/schema` | Classes and numeric ranges |
| POST | `/predict` | Seven properties, 90% bounds, SHAP, uncertainty flag |
| POST | `/score` | Index, grade, carbon, gates, mass balance, green counts, remediation |
| POST | `/recommend` | Primary application after the gate, scores, cost, 3 analogues |
| POST | `/optimize` | 80-trial search |
| POST | `/report/pdf` | A4 PDF stream |
| POST | `/batches` | Create a passport |
| GET | `/batches?limit=50` | Summaries |
| GET | `/batches/export.csv` | Flat CSV |
| POST | `/batches/import.csv` | CSV upload |
| POST | `/batches/schedule` | Open a passport only if a gate asks for a cube |
| GET | `/batches/due` | Unmeasured passports that are due |
| GET | `/batches/{id}` | Full record plus calibration |
| PATCH | `/batches/{id}` | Lab measurements |
| POST | `/batches/{id}/photo` | Cube photo |
| GET | `/batches/{id}/photo` | Photo file |
| GET | `/batches/{id}/passport.pdf` | Passport PDF |
| GET | `/docs` | OpenAPI |

Interactive docs: `http://localhost:8000/docs`.

Example predict body:

```json
{
  "plastic_type": "PET",
  "replacement_pct": 15.0,
  "particle_size_mm": 4.0,
  "wc_ratio": 0.45,
  "additive_type": "fly_ash",
  "additive_pct": 10.0,
  "curing_temp_c": 27.0,
  "curing_days": 28
}
```

---

## 13. Frontend routes

| Path | Page |
|---|---|
| `/` | Landing |
| `/studio` | Studio shell, overview tab: seven means and the four gates |
| `/studio/predictor` | Means and 90% intervals |
| `/studio/optimizer` | Constraint search and trade-off points |
| `/studio/sustainability` | Mass-balance rows and gates |
| `/studio/recommender` | Application, cost, analogues |
| `/studio/explainability` | SHAP attributions |
| `/standards` | Standards handbook page |
| `/technology` | Architecture and metrics page |
| `/batch/{id}` | Passport: lab entry, photo, PDF, calibration message |

The studio can save a batch, schedule a verification passport, list due cubes, and download the PDF. Mix state is global and mirrored into the query string so a recipe survives navigation.

---

## 14. Data the models were built from

### 14.1 Master table that M1 was evaluated on

`reports/dataset_card.md`, read from `data/processed/master_dataset.csv`, split by `Preprocessor.split` with `test_size=0.15`, `validation_size=0.15`, `random_seed=42`. Rows whose study type or DOI contains “synthetic” or “ctgan” are forced into train. There are no such rows left in val or test.

| Fact | Value |
|---|---|
| Rows | 3030 |
| Train / val / test | 2120 / 455 / 455 |
| experimental (`PlastiCreteAI_M1_Final_2000`) | 2000 |
| pretraining (UCI Yeh) | 1030 |
| DOI groups | 2 |
| DOIs in both train and test | both of them |
| DOIs in both train and val | both of them |
| DOIs in both val and test | both of them |

DOIs:

- `10.1061/(ASCE)0899-1561(1998)10:1(52)` — 1030 rows, I-Cheng Yeh concrete data.
- `PlastiCreteAI_M1_Final_2000` — 2000 rows. This is a source id, not a publisher DOI.

Missing targets: compressive strength is complete on all 3030 rows. Each of the other six targets is missing on the 1030 pretraining rows and present on the 2000 plastic rows.

The split stays row-wise. A grouped holdout needs at least three DOI groups. With two groups, holding one out would put every plastic row in test. Individual papers cannot be held out: those paper ids are not columns. Train and test both contain the plastic source id. The limitations note says the weights were not retrained during the audit that recorded this overlap.

`docs/DATA_LICENSES.md`: no licence is recorded on the CSVs. The file is not permission to redistribute them. Confirm the upstream licence before publishing `master_dataset.csv`.

### 14.2 Files the training config still names

`configs/m1_config.yaml` lists more raw files than the master CSV’s two source ids:

| Config path | Note in the older README checklist |
|---|---|
| `data/raw/uci_yeh_concrete.csv` | UCI, 1030 rows, present |
| `data/raw/mendeley_rubberized.csv` | named as pretraining, about 1200 rows |
| `data/raw/nayir_yilmaz_2024.csv` | named fine-tune source |
| `data/raw/nafees_2022.csv` | DOI 10.3390/ma15010221 in the checklist, about 640 rows |
| `data/raw/chong_shi_2023.csv` | about 103 rows |
| `data/raw/alkharisi_dahish_2025.csv` | about 296 rows |
| `data/raw/manual_extraction.csv` | team-extracted, size not fixed |
| `data/raw/PlastiCreteAI_M1_Final_2000.csv` | the 2000-row plastic table actually joined into the master file |

The evaluated master file collapsed the plastic rows onto one source id. Do not describe the test R² as a per-paper holdout.

### 14.3 Other processed sets

| File | Role |
|---|---|
| `data/processed/m2_training_dataset.csv` | generated by `pipeline/generate_m2_dataset.py`, labelled synthetic |
| `data/processed/m3_training_dataset.csv` | 2200 rows for the M3 model files |
| `data/processed/m4_training_dataset.csv` | M4 classifier labels; those labels follow the rule family, not plant certificates |

---

## 15. Training and data pipeline sequence

Offline order, when retraining rather than serving the saved weights:

1. Place raw CSVs under `plasticrete_ai/data/raw/` as named in `docs/DATA_EXTRACTION_GUIDE.md` and `m1_config.yaml`.
2. `pipeline/run_data_pipeline.py` builds the processed master table: encode categories, impute inputs, engineer the five derived features, drop missing targets per property, split 15% val and 15% test with seed 42, keep synthetic rows in train.
3. Optional CTGAN augmentation (`--no-ctgan` skips it): up to 500 rows inside the physical ranges.
4. `pipeline/run_m1_training.py` trains XGBoost, Random Forest, and the DNN. `--tune-xgb` runs Optuna (on the order of two hours in the README). `--no-transfer` skips UCI/Mendeley pretraining of the network. Weights are CV-R². Artefacts go to `models/m1/`.
5. Explainers (SHAP, and the configured LIME and PDP utilities) attach to the saved ensemble.
6. `pipeline/generate_m2_dataset.py` and `pipeline/generate_m3_dataset.py` build the downstream tables. M3’s generator targets 2200 rows.
7. `pipeline/run_m4_data_pipeline.py` fits the three forests, the scalers, and the FAISS index from the knowledge base.
8. Do not replace `models/m1` until paper-level ids exist for a grouped split. That is the written retraining policy.

Notebook: `plasticrete_ai/notebooks/PlastiCrete_M1_Training.ipynb`.

Serving order is section 2. Training artefacts are loaded once at process start.

---

## 16. Paper claims, kept separate from the live path

The paper title is “Explainable Machine Learning Platform for Plastic Waste Composite Material Property Prediction, Mix Optimisation & Sustainable Construction Intelligence”.

Abstract claims, which match the files in sections 5 and 9 except where section 18 says otherwise:

- Ensemble test R² 0.91 compressive and 0.94 flexural (exact file values 0.9104 and 0.9435).
- Compliance screening 99.4% (file 0.9939 on the BIS classifier).
- Application recommendation cross-validated macro-F1 0.84 (file 0.8395).

Positioning table in the paper:

| Capability | Single-stage ML | BIM checkers | PlastiCrete |
|---|---|---|---|
| Property prediction | Partial | No | Yes |
| Explainability | Partial | No | Yes |
| Multi-objective optimisation | Rare | No | Yes |
| BIS/NBC use-class gate | No | Partial | Yes |
| Literature-backed recommendation | No | No | Yes |
| Scheduled verification cube | No | No | Yes |

Paper pipeline figure order: 8 inputs → M1 (XGBoost + RF + DNN) → M2 (GP-BO + NSGA-II + MOPSO) → M3 gate and score → M4 recommender, with the scheduler branching off M3. Side outputs: SHAP/LIME/PDP and the 90% interval; Pareto mixes; status in {allowed, verify, lab trial, refused}; ranked uses and evidence; cubes due on day 7 and day 28.

Paper search description, which is the snapshot in section 7.2 and not the live TPE loop: a Matérn-5/2 Gaussian process with ARD on one composite score, expected improvement, NSGA-II and MOPSO in parallel, non-dominated sets merged. Scalarised objective in the paper:

`J = 0.40*CS − 0.25*Cost − 0.20*CO2 + 0.15*Diversion`

Dominance is the standard Pareto relation. The paper proves it is a strict partial order on a finite set and that the non-dominated front is an antichain. Evolutionary cost is stated as O(G·N) surrogate evaluations.

Paper assumptions: records aggregated across studies are treated as approximately i.i.d. within each property; noise is additive and inside the variable ranges; the mix–property map is treated as stationary as rows are added; inputs outside the training ranges are extrapolation, which M1 flags.

Paper combinatorial remark: discretising the six continuous inputs on practitioner grids, with six plastic types and four additive types, yields about 8.9 million candidate formulations. That sentence is the justification for a surrogate. It is not a count of rows in the CSV.

Related-work anchors named in the paper, for context only: Han et al. (random forest plus cost optimisation on recycled plastic aggregate concrete), Yilmaz and Nayir (six models including XGBoost, SHAP, compressive and flexural), Nafees et al. (trees, MLP, SVM, random forest), Asif et al. (MEP/GEP, compressive R² 0.88 and 0.87), Fan et al. (NSGA-II on recycled aggregate concrete for cost, carbon, and strength), Eastman et al. (BIM rule checking), FAISS for neighbour search. The paper’s claim of novelty is the closed chain, not a new base learner.

---

## 17. Standards named in the project

Live gate standards: IS 15658 (pavers), IS 2185 Part 1 (hollow and solid blocks), IS 456 (structural M20, lab trial only).

Also implemented or named, but not the gate verdict:

- IS 10262:2019 — the M20 reference bill (383 / 680 / 1210).
- IS 516 — grade label from the compressive mean (M10 through M30).
- IS 1237 — checker threshold CS ≥ 30 and absorption ≤ 1% (stricter absorption than the paver gate’s 6%).
- IS 2185 Part 2 — lightweight checker: CS ≥ 3.5, density ≤ 1500, absorption ≤ 10%.
- IS 5816 — split-tensile checker.
- NBC 2016 — structural and non-structural density/strength checks inside `BISChecker`.
- IS 383 is named in the README as the aggregate specification. It is not a numeric gate in `use_class_gates.json`.

Green systems named: IGBC, GRIHA, LEED v4-style recycled-content and waste flags. They are threshold counts, not a submitted rating.

---

## 18. Where the paper and the running code differ

Use this table before quoting a number.

| Topic | Paper or old snapshot | Running code |
|---|---|---|
| Optimiser at request time | GP-BO + NSGA-II + MOPSO, 50 BO iterations, 80-point NSGA-II front | Optuna TPE, 80 trials, M1 `predict_batch`, shared mass balance |
| Objective weights | 0.40, 0.25, 0.20, 0.15 | API default 0.40, 0.30, 0.20, 0.10 |
| Scenario CS / cost / CO₂ / kg | The three rows in section 7.3 | Not recomputed by `/optimize` unless a new search happens to land there |
| Paver gate | Sketch: CS ≥ 20, WA ≤ 5%, density ≥ 1800 | IS 15658: CS ≥ 30 on the low bound, WA ≤ 6% on the high bound |
| Thermal product | Its own gate in the paper table | No gate; recommendation is refused |
| Sustainability index | Includes a 10-point green term | Green term is 0; credit counts are still returned |
| Conventional sand mass in the paper’s ₹1,644 example | 723 kg | Live comparison uses 680 kg |
| M4 market JSON prices | Still on disk | Live rupees come from `mass_balance_factors.json` |
| Classifier accuracy | Safe to quote only beside macro-F1, and only as agreement with rule labels | Same files; `label_provenance.md` forbids calling it a plant hit rate |
| LIME and PDP | Configured | Not the figures in the live interface |
| Input bounds in the root README | 0–50% replacement, w/c from 0.30, extra polymer names | Schema and Pydantic bounds in section 4 |

---

## 19. What the system must not be treated as

From `docs/LIMITATIONS.md`, the model card, and the paper’s conclusion:

- The output is a 90% interval from the saved ensemble. It is not a structural design.
- `bis_overall_pass` is “some non-structural gate is allowed”. It is not a laboratory pass.
- M4’s score is agreement with the rule that trained it. The gate is the verdict when they differ.
- `bo_demo_result.json` and `sensitivity_analysis.json` disagree with each other by 11.3 MPa on one mix. Do not quote either as the live strength of that mix. M1 on that mix is 45.46 MPa with interval 21.37–69.56.
- Prices and emission factors are the rows in the mass-balance JSON.
- No cube results ship with the repository. Plant calibration starts after three lab pairs and is not a reported field result.
- Predictions outside section 4 ranges are extrapolation.
- The PDF, the QR, and a retrieved DOI do not replace an IS cube test or a structural engineer’s sign-off.
- Future work stated in the paper: write 7-day and 28-day cubes back onto the passport, compute the plant offset once three pairs exist, enlarge the evidence index, and study whether SHAP and the retrieved precedents change a mix decision.

---

## 20. How to run

Backend, from `plasticrete_ai`:

```
python -m venv venv
# Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn deployment.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Frontend, from `plasticrete_web`:

```
npm install
npm run dev
```

Open `http://localhost:5173`. API docs at `http://localhost:8000/docs`.

Tests: `python -m pytest modules -q` inside `plasticrete_ai`, then `python scripts/validate_kb.py`. Other audit scripts: `scripts/audit_split.py`, `scripts/eval_rules_vs_model.py`, `scripts/m2_vs_m1_gap.py`, `scripts/drop_zero_wc.py`.

Environment:

| Variable | Effect |
|---|---|
| `CORS_ORIGINS` | Comma-separated origins; empty means `*` |
| `VITE_API_URL` | Frontend API base; default `/api` |
| `PUBLIC_APP_URL` | QR link prefix; default `http://localhost:5173` |
| `BATCH_DB_PATH` | SQLite path; default `data/batches/batches.sqlite` |

---

## 21. One-screen workflow for a mix

1. Fix the eight inputs inside the ranges in section 4. Start from the default PET / 15% / 4 mm / 0.45 / fly ash 10% / 27 °C / 28 days if no plant recipe was given.
2. Call `/predict`. Keep the seven means and both ends of the interval. If `uncertainty_flag` is true, the relative width exceeded a threshold in section 5.2; still show the interval.
3. Call `/score` with the means and the interval. Read `mass_balance` for kilograms, rupees, and CO₂. Read `use_class_gates` for the four statuses. Read `sustainability_score` and the letter grade as the weighted index, not as a certificate. Ignore green points as a contribution to that index.
4. Call `/recommend` with the same payload. Trust `primary_gate_status` and `primary_gate_message` over the raw classifier label. Show at most the three FAISS neighbours as literature, with author, year, journal, and DOI.
5. If a product constraint exists, call `/optimize` with weights summing to 1 and a `use_class`. Use `prediction_source == "m1"` results only. Present `balanced`, `max_strength`, `max_diversion`, and `min_cost` as points from that search. Rank the next physical cube by interval width.
6. If any gate is `verification_batch` or `lab_trial`, `POST /batches/schedule` so the passport carries day-7 and day-28 dates. Structural is always in that set when it is not refused.
7. After the lab crushes cubes, `PATCH` the individual values. CV above 0.15 needs `confirm_high_cv`. The plant offset appears in `calibration` after three `source=lab` pairs. It does not retrain M1.
8. `POST /report/pdf` with the batch id when the sheet should include the QR and the measured row.
