# PlastiCrete AI

An explainable machine learning platform that predicts 7 mechanical and physical properties of plastic waste composite construction materials from 8 mix design inputs — replacing ₹5,000–₹20,000 lab tests with millisecond inference.

---

## Module status

| Module | Status | Description |
|--------|--------|-------------|
| **M1 — Prediction** | ✅ Active | Ensemble (XGBoost + RF + DNN) property predictor |
| **M2 — Optimisation** | ✅ Active | XGBoost-surrogate constrained optimisation via Optuna |
| **M3 — Sustainability** | ✅ Active | Embodied carbon (LCA), BIS compliance, IGBC/GRIHA/LEED scorer |
| **M4 — Recommendation** | ✅ Active | RF classifier + FAISS RAG application recommender |

---

## Quick start

```bash
cd plasticrete_ai
pip install -r requirements.txt
python pipeline/run_m1_training.py
uvicorn deployment.api.app:app --port 8000
```

Optional flags:
```bash
python pipeline/run_m1_training.py --tune-xgb      # Optuna HPO (~2 hrs)
python pipeline/run_m1_training.py --no-transfer    # skip DNN transfer learning
python pipeline/run_m1_training.py --no-ctgan       # skip CTGAN augmentation
```

---

## File tree

```
plasticrete_ai/
├── README.md
├── requirements.txt
├── .env.example
├── configs/
│   ├── m1_config.yaml
│   ├── m2_config.yaml
│   ├── m3_config.yaml
│   └── m4_config.yaml
├── data/
│   ├── raw/                    ← immutable source CSVs
│   ├── processed/              ← master_dataset.csv
│   ├── augmented/              ← CTGAN synthetic rows
│   └── external/               ← BIS tables, ICE factors
├── modules/
│   ├── m1_prediction/
│   │   ├── __init__.py         ← PUBLIC CONTRACT
│   │   ├── CONTRACT.md
│   │   ├── utils/schema.py     ← SINGLE SOURCE OF TRUTH
│   │   ├── utils/data_loader.py
│   │   ├── utils/preprocessor.py
│   │   ├── utils/feature_engineering.py
│   │   ├── model/xgboost_model.py
│   │   ├── model/random_forest_model.py
│   │   ├── model/dnn_model.py
│   │   ├── model/ensemble.py
│   │   ├── model/trainer.py
│   │   ├── model/evaluator.py
│   │   ├── explainability/shap_explainer.py
│   │   ├── explainability/lime_explainer.py
│   │   └── explainability/pdp_ice_plots.py
│   ├── m2_optimization/        ← surrogate-model optimiser (Optuna)
│   ├── m3_sustainability/      ← LCA + BIS + green rating scorer
│   └── m4_recommendation/      ← RF classifier + FAISS RAG
├── models/m1/                  ← trained artefacts
├── pipeline/
│   ├── run_data_pipeline.py
│   └── run_m1_training.py
├── deployment/
│   ├── api/app.py              ← FastAPI
│   └── frontend/streamlit_app.py
└── docs/
```

---

## M1 → M2/M3/M4 contract

```python
import modules.m1_prediction as m1

# At startup
m1.load_ensemble("models/m1/", config)

# Single prediction (M3, M4, API)
result = m1.predict({
    "plastic_type":    "PET",
    "replacement_pct": 15.0,
    "particle_size_mm": 4.0,
    "wc_ratio":        0.45,
    "additive_type":   "fly_ash",
    "additive_pct":    10.0,
    "curing_temp_c":   27.0,
    "curing_days":     28,
})
# result.compressive_strength_mpa → float or None
# result.ci_low, result.ci_high   → Dict[str, float]
# result.shap_values              → Dict[str, Dict[str, float]]

# Batch prediction (M2 optimisation loop — no SHAP, fast)
prep = m1.get_preprocessor()
X = prep.transform_input(input_dict)          # (1, n_features)
means, ci_low, ci_high = m1.predict_batch(X) # each (1, 7)
```

`PredictionResult` field → column order mapping:

| Index | Field | Unit |
|-------|-------|------|
| 0 | compressive_strength_mpa | MPa |
| 1 | flexural_strength_mpa | MPa |
| 2 | split_tensile_mpa | MPa |
| 3 | density_kgm3 | kg/m³ |
| 4 | water_absorption_pct | % |
| 5 | thermal_conductivity_wm | W/m·K |
| 6 | durability_index | 0–100 |

---

## Data checklist

Place these files in `data/raw/` (see `docs/DATA_EXTRACTION_GUIDE.md`):

| File | DOI | Rows |
|------|-----|------|
| `uci_yeh_concrete.csv` | auto-fetched via ucimlrepo | 1030 |
| `mendeley_rubberized.csv` | Mendeley | ~1200 |
| `nayir_yilmaz_2024.csv` | 10.1016/nayir_yilmaz_2024 | ~428 |
| `nafees_2022.csv` | 10.3390/ma15010221 | ~640 |
| `chong_shi_2023.csv` | J. Clean. Prod. 2023 | 103 |
| `alkharisi_dahish_2025.csv` | 10.1016/alkharisi_dahish_2025 | ~296 |
| `manual_extraction.csv` | team-extracted | TBD |

---

## Expected performance (R² on held-out test set)

| Target | Expected R² range |
|--------|--------------------|
| compressive_strength_mpa | 0.88 – 0.94 |
| flexural_strength_mpa | 0.82 – 0.90 |
| split_tensile_mpa | 0.80 – 0.88 |
| density_kgm3 | 0.90 – 0.96 |
| water_absorption_pct | 0.75 – 0.85 |
| thermal_conductivity_wm | 0.65 – 0.78 |
| durability_index | 0.70 – 0.82 |
