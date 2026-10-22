# Dataset card

Counts below are read from `data/processed/master_dataset.csv`.
The split is `Preprocessor.split` with `configs/m1_config.yaml`
(`test_size=0.15`, `validation_size=0.15`, `random_seed=42`).
Synthetic rows (`study_type` or `source_doi` containing synthetic or ctgan) are moved into train.
The CSV has one DOI for the UCI pretraining rows and one DOI for the plastic rows.
Grouped holdout runs only when there are at least three DOI groups.
With two groups, holding one out would place every plastic row in test, so the split stays row-wise and both sources appear in train and test.
Individual papers cannot be held out: those paper ids are not columns in this file.

`models/m1/evaluation_report.json` is the evaluation of the weights on disk.
This script does not retrain those weights, so that file is still the evaluation from the run that saved them.

- Rows: 3030
- Train / val / test after the synthetic move: 2120 / 455 / 455
- DOI groups: 2
- DOIs in both train and test: 2
- DOIs in both train and val: 2
- DOIs in both val and test: 2
- Synthetic rows left in val: 0
- Synthetic rows left in test: 0

## Rows by study_type

- experimental: 2000
- pretraining: 1030

## Rows by source_doi

- 10.1061/(ASCE)0899-1561(1998)10:1(52): 1030
- PlastiCreteAI_M1_Final_2000: 2000

## Missing targets

- compressive_strength_mpa: 0 missing of 3030
- flexural_strength_mpa: 1030 missing of 3030
- split_tensile_mpa: 1030 missing of 3030
- density_kgm3: 1030 missing of 3030
- water_absorption_pct: 1030 missing of 3030
- thermal_conductivity_wm: 1030 missing of 3030
- durability_index: 1030 missing of 3030

## Licence and bias

Licences are not recorded on the CSV. See `docs/DATA_LICENSES.md` once that note exists.
Rows tagged synthetic or ctgan are generated, not measured. They stay in the training partition.

Train/test DOI overlap: 10.1061/(ASCE)0899-1561(1998)10:1(52), PlastiCreteAI_M1_Final_2000
