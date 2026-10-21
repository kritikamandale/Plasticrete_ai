# PlastiCrete AI — M3 Public Contract

**Version:** 1.0  
**Breaking change policy:** Any rename or removal of fields in `score_mix()` output constitutes a breaking change → bump to v2.0 and notify maintainers.

---

## Import boundary

Other modules import **only** from:

```python
import modules.m3_sustainability as m3
```

Never import directly from `modules.m3_sustainability.core.*` or `utils.*`.

---

## Public functions

### `load_models(model_dir: str = "", config: dict | None = None) -> None`

Call once at startup (e.g. in FastAPI lifespan). Initializes all M3 scoring components (BIS checker, LCA calculator, Green rater, Score aggregator, Remediation advisor) from config.

```python
m3.load_models()
```

---

### `score_mix(mix_params: dict, m1_props: dict) -> dict`

Computes the embodied carbon (LCA), BIS standard compliance (IS 1237 / IS 2185 / IS 456), green rating credits (IGBC, GRIHA, LEED), overall sustainability score, and prescriptive remediation recommendations.

**`mix_params` keys:**

| Key | Type | Description |
| :--- | :--- | :--- |
| `plastic_type` | str | `PET`, `HDPE`, `LDPE`, `PVC`, `PP`, `Mixed` |
| `replacement_pct` | float | Aggregate volume replacement (0.0 – 40.0%) |
| `particle_size_mm` | float | Plastic particle size (0.5 – 20.0 mm) |
| `wc_ratio` | float | Water-cement ratio (0.35 – 0.65) |
| `additive_type` | str | `fly_ash`, `silica_fume`, `fibres`, `none` |
| `additive_pct` | float | % additive by cement mass (0.0 – 30.0%) |
| `curing_temp_c` | float | Curing temperature (20.0 – 80.0 °C) |
| `curing_days` | int / float | Curing duration in days (3 – 90) |

**`m1_props` keys:** (all 7 predicted mechanical and physical properties from M1)

| Key | Type | Unit |
| :--- | :--- | :--- |
| `compressive_strength_mpa` | float | MPa |
| `flexural_strength_mpa` | float | MPa |
| `split_tensile_mpa` | float | MPa |
| `density_kgm3` | float | kg/m³ |
| `water_absorption_pct` | float | % |
| `thermal_conductivity_wm` | float | W/m·K |
| `durability_index` | float | 0–100 |

---

## Output Dictionary (`ScoreResponse`)

Returns a flat dictionary matching all 16 fields:

| Field | Type | Description |
| :--- | :--- | :--- |
| `sustainability_score` | float | Composite score (0 – 100) |
| `sustainability_grade` | str | Rating grade (e.g., `A+`, `A`, `B`, `C`) |
| `embodied_carbon_kgco2e_m3` | float | Embodied carbon in kg CO₂e / m³ |
| `co2_saving_pct` | float | % carbon reduction vs conventional concrete |
| `plastic_diversion_kg_m3` | float | Plastic diverted in kg / m³ |
| `pet_bottle_equiv` | float | Equivalent standard 500ml PET bottles diverted |
| `bis_overall_pass` | bool | True if meeting required BIS threshold |
| `igbc_total_credits` | float | IGBC Green building rating credits |
| `griha_material_criterion_pts` | float | GRIHA points earned |
| `leed_total_points` | float | LEED v4.1 points earned |
| `total_green_credits` | float | Total combined green rating credits |
| `top_negative_factor` | str | Primary limiting factor |
| `remediation_action_1` | str | Recommended corrective measure 1 |
| `remediation_action_2` | str | Recommended corrective measure 2 |
| `remediation_action_3` | str | Recommended corrective measure 3 |
| `estimated_score_gain` | float | Potential score gain with remediation |
