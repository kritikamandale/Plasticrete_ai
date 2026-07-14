# PlastiCrete AI — M2 Public Contract

**Version:** 1.0  
**Breaking change policy:** Any rename or removal of a key in the `run_optimization` return dict constitutes a breaking change → bump to v2.0 and notify M3/M4 maintainers.

---

## Import boundary

Other modules import **only** from:

```python
import modules.m2_optimization as m2
```

Never import from `modules.m2_optimization.model.*` or `utils.*`.

---

## Public functions

### `load_models() → None`

Call once at startup before any optimisation run. Loads all XGBoost surrogate models, encoders, and scalers from `models/m2/`.

```python
m2.load_models()
```

---

### `run_optimization(constraints, weights, mode) → dict`

Find the optimal plastic-concrete mix via Optuna TPE Bayesian optimisation.

**`constraints` keys:**

| Key                        | Type          | Description                        |
|----------------------------|---------------|------------------------------------|
| `plastic_type`             | str or None   | Fix to one type, or None for any   |
| `replacement_pct_max`      | float         | Max % aggregate replacement (≤40)  |
| `compressive_strength_min` | float         | Minimum CS required (MPa)          |
| `cost_max_inr_per_m3`      | float or None | Hard cost ceiling (INR/m³)         |

**`weights` keys** (must sum to 1.0 for meaningful scores):

| Key                    | Default |
|------------------------|---------|
| `compressive_strength` | 0.40    |
| `cost_per_m3`          | 0.30    |
| `co2_per_m3`           | 0.20    |
| `plastic_content_pct`  | 0.10    |

**Return dict shape:**

```python
{
    "best_mix": {
        "replacement_pct":  float,
        "particle_size_mm": float,
        "wc_ratio":         float,
        "additive_pct":     float,
        "curing_temp_c":    float,
        "curing_days":      float,
    },
    "predicted_cs_mpa":                  float,
    "predicted_cost_inr_m3":             float,
    "predicted_co2_kgco2e_m3":           float,
    "predicted_plastic_diversion_kg_m3": float,
    "composite_score":                   float,
    "mode":                              str,
}
```
