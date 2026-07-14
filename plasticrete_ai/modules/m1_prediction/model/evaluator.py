"""
Evaluator: compute per-target R2, RMSE, MAE, MAPE and save report.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
from loguru import logger
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from modules.m1_prediction.utils.preprocessor import Preprocessor
from modules.m1_prediction.utils.schema import TARGET_COLUMNS

R2_THRESHOLD = 0.80

TARGET_R2_EXPECTED = {
    "compressive_strength_mpa": (0.88, 0.94),
    "flexural_strength_mpa":    (0.82, 0.90),
    "split_tensile_mpa":        (0.80, 0.88),
    "density_kgm3":             (0.90, 0.96),
    "water_absorption_pct":     (0.75, 0.85),
    "thermal_conductivity_wm":  (0.65, 0.78),
    "durability_index":         (0.70, 0.82),
}


def evaluate(
    ensemble,
    X_test: np.ndarray,
    y_test: np.ndarray,
    preprocessor: Preprocessor,
    save_dir: Optional[str | Path] = "models/m1",
) -> dict:
    """
    Run ensemble.predict_batch(), compare to y_test, print and save report.
    Returns metrics dict.
    """
    means, _, _ = ensemble.predict_batch(X_test)

    y_orig = preprocessor.inverse_transform_targets(y_test.copy())

    results = {}
    rows = []
    header = "  {:<35} {:>7} {:>8} {:>8} {:>8}  Status".format(
        "Target", "R2", "RMSE", "MAE", "MAPE%"
    )
    sep = "-" * 80

    print("\n" + "=" * 80)
    print("M1 EVALUATION REPORT (test set)")
    print(sep)
    print(header)
    print(sep)

    for i, target in enumerate(TARGET_COLUMNS):
        mask = ~np.isnan(y_orig[:, i])
        n_valid = mask.sum()

        if n_valid < 5:
            status = "[SKIP]"
            row = dict(target=target, r2=None, rmse=None, mae=None, mape=None,
                       n_test=int(n_valid), status="skipped")
            print("  {:<35} {:>7} {:>8} {:>8} {:>8}  {} ({} rows)".format(
                target, "N/A", "N/A", "N/A", "N/A", status, n_valid))
            results[target] = row
            rows.append(row)
            continue

        yt   = y_orig[mask, i]
        yhat = means[mask, i]

        r2   = r2_score(yt, yhat)
        rmse = float(np.sqrt(mean_squared_error(yt, yhat)))
        mae  = float(mean_absolute_error(yt, yhat))
        nz   = np.abs(yt) > 1e-6
        mape = float(np.mean(np.abs((yt[nz] - yhat[nz]) / yt[nz])) * 100) if nz.any() else float("nan")

        pass_fail = "[PASS]" if r2 >= R2_THRESHOLD else "[FAIL]"
        expected  = TARGET_R2_EXPECTED.get(target, (R2_THRESHOLD, 1.0))
        range_str = "[{:.2f}-{:.2f}]".format(expected[0], expected[1])

        row = dict(
            target=target, r2=round(r2, 4), rmse=round(rmse, 4),
            mae=round(mae, 4), mape=round(mape, 2) if not np.isnan(mape) else None,
            n_test=int(n_valid), expected_range=range_str, status=pass_fail,
        )
        results[target] = row
        rows.append(row)

        mape_str = "{:>8.2f}".format(mape) if not np.isnan(mape) else "     N/A"
        print("  {:<35} {:>7.4f} {:>8.4f} {:>8.4f} {}  {}  {}".format(
            target, r2, rmse, mae, mape_str, pass_fail, range_str
        ))

    print("=" * 80 + "\n")

    if save_dir:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        report_path = save_dir / "evaluation_report.json"
        with open(report_path, "w") as f:
            json.dump(rows, f, indent=2)
        logger.info("Evaluation report saved -> {}".format(report_path))

    return results
