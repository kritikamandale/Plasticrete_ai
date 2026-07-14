# PlastiCrete AI — M1 Public Contract

**Version:** 1.0  
**Breaking change policy:** Any rename or removal of a `PredictionResult` field constitutes a breaking change → bump to v2.0 and notify M2/M3/M4 maintainers.

---

## Import boundary

M2, M3, and M4 import **only** from:

```python
import modules.m1_prediction as m1
```

Never import from `modules.m1_prediction.model.*`, `utils.*`, or `explainability.*`.

---

## Public functions

### `load_ensemble(model_dir: str, config: dict) → None`

Call once at startup before any prediction. Loads all sub-models and the preprocessor from disk.

```python
m1.load_ensemble("models/m1/", config)
```

---

### `predict(input_dict: dict) → PredictionResult`

Single-sample prediction with SHAP explanations. Used by M3, M4, and the `/predict` API endpoint.

**Input dict keys** (all required):

| Key              | Type  | Valid values / range       |
|------------------|-------|----------------------------|
| `plastic_type`   | str   | `PET`, `HDPE`, `LDPE`, `PVC`, `PP`, `Mixed`, `None` |
| `replacement_pct`| float | 0.0 – 40.0 (% by volume)  |
| `particle_size_mm`| float | 0.5 – 20.0 mm             |
| `wc_ratio`       | float | 0.35 – 0.65               |
| `additive_type`  | str   | `fly_ash`, `silica_fume`, `fibres`, `none` |
| `additive_pct`   | float | 0.0 – 30.0 (% by mass)    |
| `curing_temp_c`  | float | 20.0 – 80.0 °C            |
| `curing_days`    | int   | 3 – 90 days               |

**Example:**

```python
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
```

---

### `predict_batch(X: np.ndarray) → Tuple[means, ci_low, ci_high]`

Vectorised batch prediction for M2's optimisation loop. No SHAP, no MC Dropout (speed-optimised).

- `X`: shape `(n_samples, n_features)` — must be preprocessed via `get_preprocessor().transform_input()`
- Returns three `ndarray`s each of shape `(n_samples, 7)` in **original units** (MPa, kg/m³, etc.)
- **Column order is fixed** — see TARGET_COLUMNS below
- Target < 50 ms per call

---

### `get_preprocessor() → Preprocessor`

Returns the fitted `Preprocessor` instance. M2 calls this to transform candidate mixes before `predict_batch()`.

```python
prep = m1.get_preprocessor()
X = prep.transform_input(input_dict)   # shape (1, n_features)
means, ci_low, ci_high = m1.predict_batch(X)
```

---

## PredictionResult dataclass

```python
@dataclass
class PredictionResult:
    compressive_strength_mpa:  Optional[float]              # MPa
    flexural_strength_mpa:     Optional[float]              # MPa
    split_tensile_mpa:         Optional[float]              # MPa
    density_kgm3:              Optional[float]              # kg/m³
    water_absorption_pct:      Optional[float]              # %
    thermal_conductivity_wm:   Optional[float]              # W/m·K
    durability_index:          Optional[float]              # 0–100
    ci_low:                    Dict[str, float]             # 90% CI lower
    ci_high:                   Dict[str, float]             # 90% CI upper
    shap_values:               Dict[str, Dict[str, float]]  # target → {feature: shap}
    uncertainty_flag:          bool                         # True if CI/mean > threshold
    low_coverage_targets:      List[str]                    # targets with < 50 train rows
```

`None` values indicate the target model was skipped due to insufficient training data.

Call `.to_dict()` to get a JSON-serialisable plain dict.

---

## TARGET_COLUMNS order (for predict_batch column alignment)

```
Index 0: compressive_strength_mpa
Index 1: flexural_strength_mpa
Index 2: split_tensile_mpa
Index 3: density_kgm3
Index 4: water_absorption_pct
Index 5: thermal_conductivity_wm
Index 6: durability_index
```

Always use `from modules.m1_prediction.utils.schema import TARGET_COLUMNS` for safe indexing.
