# Limitations

- `master_dataset.csv` collapses the plastic rows onto one source id. Train and test both contain that id. `reports/dataset_card.md` records the overlap. The weights were not retrained in the audit.
- M3 pass flags and the sustainability index are rules over the mass balance and the use-class gate. M4's classifier agrees or disagrees with that gate. Neither number is a hit rate against a built product. See `reports/label_provenance.md` and `reports/rules_vs_model.json`.
- `models/m2/bo_demo_result.json` and `sensitivity_analysis.json` are surrogate snapshots. They do not match each other. The live search calls M1. The gap is in `reports/m2_vs_m1_gap.json`.
- Prices and emission factors are the rows in `data/external/mass_balance_factors.json`. A user-entered ₹/kg is echoed, not replaced with a market rate.
- No cube results ship with the repository. A passport stays unvalidated until a lab writes measurements with `source=lab`.
