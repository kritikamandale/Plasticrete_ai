"""Replay the M1 preprocessor split and write reports/dataset_card.md.

Does not train and does not read or write model weights.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.m1_prediction.utils.preprocessor import Preprocessor, _synthetic_mask  # noqa: E402
from modules.m1_prediction.utils.schema import SOURCE_DOI, STUDY_TYPE, TARGET_COLUMNS  # noqa: E402


def _overlap(left: pd.DataFrame, right: pd.DataFrame) -> list[str]:
    a = set(left[SOURCE_DOI].fillna("unknown").astype(str))
    b = set(right[SOURCE_DOI].fillna("unknown").astype(str))
    return sorted(a & b)


def main() -> None:
    cfg = yaml.safe_load((ROOT / "configs" / "m1_config.yaml").read_text(encoding="utf-8"))
    pre = cfg["preprocessing"]
    master_path = ROOT / "data" / "processed" / "master_dataset.csv"
    df = pd.read_csv(master_path)
    train, val, test = Preprocessor().split(
        df,
        test_size=float(pre["test_size"]),
        val_size=float(pre["validation_size"]),
        random_seed=int(pre["random_seed"]),
    )

    doi_counts = Counter(df[SOURCE_DOI].fillna("unknown").astype(str))
    study_counts = Counter(df[STUDY_TYPE].fillna("unknown").astype(str))
    train_test = _overlap(train, test)
    train_val = _overlap(train, val)
    val_test = _overlap(val, test)
    syn_val = int(_synthetic_mask(val).sum())
    syn_test = int(_synthetic_mask(test).sum())

    lines = [
        "# Dataset card",
        "",
        "Counts below are read from `data/processed/master_dataset.csv`.",
        "The split is `Preprocessor.split` with `configs/m1_config.yaml`",
        f"(`test_size={pre['test_size']}`, `validation_size={pre['validation_size']}`, `random_seed={pre['random_seed']}`).",
        "Synthetic rows (`study_type` or `source_doi` containing synthetic or ctgan) are moved into train.",
        "The CSV has one DOI for the UCI pretraining rows and one DOI for the plastic rows.",
        "Grouped holdout runs only when there are at least three DOI groups.",
        "With two groups, holding one out would place every plastic row in test, so the split stays row-wise and both sources appear in train and test.",
        "Individual papers cannot be held out: those paper ids are not columns in this file.",
        "",
        "`models/m1/evaluation_report.json` is the evaluation of the weights on disk.",
        "This script does not retrain those weights, so that file is still the evaluation from the run that saved them.",
        "",
        f"- Rows: {len(df)}",
        f"- Train / val / test after the synthetic move: {len(train)} / {len(val)} / {len(test)}",
        f"- DOI groups: {len(doi_counts)}",
        f"- DOIs in both train and test: {len(train_test)}",
        f"- DOIs in both train and val: {len(train_val)}",
        f"- DOIs in both val and test: {len(val_test)}",
        f"- Synthetic rows left in val: {syn_val}",
        f"- Synthetic rows left in test: {syn_test}",
        "",
        "## Rows by study_type",
        "",
    ]
    for name, count in sorted(study_counts.items()):
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Rows by source_doi", ""])
    for name, count in sorted(doi_counts.items()):
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Missing targets", ""])
    for col in TARGET_COLUMNS:
        missing = int(df[col].isna().sum()) if col in df.columns else len(df)
        lines.append(f"- {col}: {missing} missing of {len(df)}")
    lines.extend([
        "",
        "## Licence and bias",
        "",
        "Licences are not recorded on the CSV. See `docs/DATA_LICENSES.md` once that note exists.",
        "Rows tagged synthetic or ctgan are generated, not measured. They stay in the training partition.",
        "",
    ])
    if train_test:
        lines.append("Train/test DOI overlap: " + ", ".join(train_test))
        lines.append("")

    out = ROOT / "reports" / "dataset_card.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    print(f"doi train/test overlap={len(train_test)} synthetic val={syn_val} test={syn_test}")


if __name__ == "__main__":
    main()
