# Model card

Intended use: screen a plastic-aggregate mix before a cube is cast. The output is a 90% interval from the saved M1 ensemble. It is not a structural design.

Training data: `data/processed/master_dataset.csv`. Two source ids are in that file (UCI Yeh pretraining rows, and `PlastiCreteAI_M1_Final_2000`). Paper-level ids are not columns, so a grouped holdout of individual papers is not possible from this file. See `reports/dataset_card.md`.

Metrics below are copied from `models/m1/evaluation_report.json` for the weights on disk. This card does not recompute them.

- compressive_strength_mpa: R² 0.9104, RMSE 5.6011, MAE 3.6123, n_test 455
- flexural_strength_mpa: R² 0.9435, RMSE 0.319, MAE 0.2205, n_test 282
- split_tensile_mpa: R² 0.9393, RMSE 0.3731, MAE 0.2501, n_test 282
- density_kgm3: R² 0.8874, RMSE 30.2412, MAE 23.7415, n_test 282
- water_absorption_pct: R² 0.8928, RMSE 0.2961, MAE 0.233, n_test 282
- thermal_conductivity_wm: R² 0.929, RMSE 0.0578, MAE 0.045, n_test 282
- durability_index: R² 0.9192, RMSE 4.2642, MAE 3.393, n_test 282

Known limits: inputs outside `configs/m1_config.yaml` raise the extrapolation flag. A missing interval is not an allowed product. There is no field cube dataset in the repo. Plant calibration starts after three lab pairs on the batch passport.

Retraining policy: do not overwrite `models/m1` until a grouped split can be built from paper ids that are actually in the table.
