# PlastiCrete AI — M4 Public Contract

**Version:** 1.0  
**Breaking change policy:** Any rename or removal of a field in `RecommendationResult`, `CostBenefit`, or `RAGAnalogue` constitutes a breaking change → bump to v2.0 and notify maintainers.

---

## Import boundary

Other modules import **only** from:

```python
import modules.m4_recommendation as m4
```

Never import from `modules.m4_recommendation.model.*` or `utils.*`.

---

## Public functions

### `load_models(model_dir=None) → None`

Call once at startup. Loads RF classifiers, scalers, label encoder, FAISS index, and JSON knowledge bases from `models/m4/`.

```python
m4.load_models()
```

---

### `recommend(mix_params, m1_properties) → RecommendationResult`

Classify the best construction application for a given mix and return full economics + RAG analogues.

**`mix_params` keys:**

| Key              | Type  | Description                        |
|------------------|-------|------------------------------------|
| `plastic_type`   | str   | PET, HDPE, LDPE, PVC, PP, Mixed    |
| `replacement_pct`| float | % aggregate replaced by plastic    |
| `particle_size_mm`| float | Plastic particle size (mm)        |
| `wc_ratio`       | float | Water-cement ratio                 |
| `additive_type`  | str   | fly_ash, silica_fume, fibres, none |
| `additive_pct`   | float | % additive by cement mass          |
| `curing_temp_c`  | float | Curing temperature (°C)            |
| `curing_days`    | int   | Curing duration (days)             |

**`m1_properties` keys:** all 7 M1 target outputs (compressive_strength_mpa, flexural_strength_mpa, split_tensile_mpa, density_kgm3, water_absorption_pct, thermal_conductivity_wm, durability_index).

---

## RecommendationResult dataclass

```python
@dataclass
class RecommendationResult:
    primary_application:     str
    primary_confidence_pct:  float
    suitable_applications:   List[str]
    suitability_scores:      Dict[str, float]
    cost_benefit:            CostBenefit
    rag_analogues:           List[RAGAnalogue]   # top-3 FAISS hits
```

See `utils/schema.py` for `CostBenefit` and `RAGAnalogue` field definitions.
