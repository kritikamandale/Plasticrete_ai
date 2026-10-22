# Label provenance

This note says where each sustainability and recommendation label comes from. It does not add a new score.

## M3

`score_mix` in `modules/m3_sustainability/__init__.py` does four things:

- Embodied carbon, cost, plastic kilograms, and bottle equivalents come from `modules/shared/mass_balance.py` and the factor file `data/external/mass_balance_factors.json`.
- `use_class_gates` come from `modules/shared/use_class_gate.py` and `data/external/use_class_gates.json`. A product is allowed only when its own standard clears on the conservative side of the 90% interval. That gate is the compliance verdict the API returns.
- `bis_overall_pass` is overwritten from those gates: it is true only when some non-structural gate status is `allowed`. It is not a separate laboratory result.
- `sustainability_score` is a weighted index of the carbon saving, the plastic mass, the replacement percentage, and the fraction of gates that cleared. Rating-point counts are not added. The grade letters are thresholds on that index.

The BIS checker and the green-rating helper still run inside `score_mix`, but the pass flag the caller sees is the gate result. Calling that flag "accuracy against ground truth" would be wrong. It is agreement with the rule file.

## M4

`recommend` classifies a product with the saved random forest, then `modules/m4_recommendation/model/recommender.py` drops any application whose use-class gate is not `allowed` or `lab_trial`. When the classifier's first choice fails the gate, the primary application moves to the highest suitability score that still passes. The gate message is what the studio shows.

The classifier was trained on labels produced by the same kind of rule, not on a held-out set of plant certificates. Its score is agreement with that rule, not a measured hit rate on built products.

## What is not a label

Predicted strength, the 90% interval, and the mass-balance totals are model or table outputs. They are not compliance labels.
