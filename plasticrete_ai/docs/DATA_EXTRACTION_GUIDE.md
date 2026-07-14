# Data Extraction Guide — PlastiCrete AI M1

## Required CSV files in `data/raw/`

| File | Source | DOI | Target columns available |
|------|--------|-----|--------------------------|
| `uci_yeh_concrete.csv` | UCI ML Repository | 10.1061/(ASCE)0899-1561(1998)10:1(52) | CS only |
| `mendeley_rubberized.csv` | Mendeley Data | varies | CS |
| `nayir_yilmaz_2024.csv` | Manual extraction | 10.1016/nayir_yilmaz_2024 | CS, FS |
| `nafees_2022.csv` | MDPI Materials | 10.3390/ma15010221 | CS, STS |
| `chong_shi_2023.csv` | J. Clean. Prod. | 10.1016/j.jclepro.2023 | CS only |
| `alkharisi_dahish_2025.csv` | Manual extraction | 10.1016/alkharisi_dahish_2025 | CS, STS |
| `manual_extraction.csv` | Team extraction | various | all available |

## Column naming for manual_extraction.csv

Use the canonical column names from `modules/m1_prediction/utils/schema.py`:

```
plastic_type, replacement_pct, particle_size_mm, wc_ratio,
additive_type, additive_pct, curing_temp_c, curing_days,
compressive_strength_mpa, flexural_strength_mpa, split_tensile_mpa,
density_kgm3, water_absorption_pct, thermal_conductivity_wm, durability_index,
source_doi, study_type, mix_id
```

Leave missing target values as blank (will become NaN).

## Priority data to extract

1. **density_kgm3** — < 50 rows currently → highest priority
2. **thermal_conductivity_wm** — very sparse
3. **water_absorption_pct** — sparse
4. **durability_index** — sparse (freeze-thaw, sulfate resistance cycles)
5. **flexural_strength_mpa** — moderate coverage, more needed
