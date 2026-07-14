"""
Full M1 training pipeline: data → augment → train → evaluate → save.

Usage:
  python pipeline/run_m1_training.py                      # default
  python pipeline/run_m1_training.py --tune-xgb           # Optuna HPO (~2 hrs)
  python pipeline/run_m1_training.py --no-transfer         # skip transfer learning
  python pipeline/run_m1_training.py --no-ctgan            # skip CTGAN augmentation
  python pipeline/run_m1_training.py --config path/to/config.yaml
"""
import argparse
import sys
import time
from pathlib import Path

# Allow running from plasticrete_ai/ root
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from loguru import logger

from modules.m1_prediction.model.trainer import M1Trainer


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PlastiCrete AI — M1 Training Pipeline")
    p.add_argument("--tune-xgb",    action="store_true", help="Run Optuna HPO for XGBoost")
    p.add_argument("--no-transfer", action="store_true", help="Skip transfer learning")
    p.add_argument("--no-ctgan",    action="store_true", help="Skip CTGAN augmentation")
    p.add_argument("--config",      default="configs/m1_config.yaml",
                   help="Path to YAML config file")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    config_path = Path(args.config)
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
        logger.info(f"Config loaded from {config_path}")
    else:
        logger.warning(f"Config not found at {config_path} — using defaults")
        config = {}

    save_dir = config.get("model_output", {}).get("save_dir", "models/m1/")

    trainer = M1Trainer(
        config=config,
        raw_dir=config.get("data", {}).get("raw_dir", "data/raw"),
        processed_dir=config.get("data", {}).get("processed_dir", "data/processed"),
        save_dir=save_dir,
    )

    t_start = time.time()
    ensemble = trainer.run(
        tune_xgb=args.tune_xgb,
        use_transfer=not args.no_transfer,
        use_ctgan=not args.no_ctgan,
    )
    total = time.time() - t_start

    print(f"\n{'='*60}")
    print("[OK] PlastiCrete AI -- M1 Training Complete")
    print(f"   Total wall time: {total/60:.1f} min")
    print(f"   Models saved:    {save_dir}")
    print(f"   Evaluation:      {save_dir}evaluation_report.json")
    print(f"\n   Next step:")
    print(f"   uvicorn deployment.api.app:app --port 8000")
    print(f"   Run M2 prompt to build the Bayesian optimisation module.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
