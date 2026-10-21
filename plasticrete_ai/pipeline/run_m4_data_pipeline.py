"""
PlastiCrete AI — Data Pipeline Runner (Legacy compatibility alias)

NOTE: Canonical data pipeline runner is `pipeline/run_data_pipeline.py`.
This script forwards to `pipeline/run_data_pipeline.py` for backward compatibility.
"""
import sys
from pathlib import Path

# Allow running from plasticrete_ai/ root
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.run_data_pipeline import (
    load_all_sources, print_coverage_report, save_master,
)

if __name__ == "__main__":
    print("[INFO] pipeline/run_m4_data_pipeline.py is aliased to pipeline/run_data_pipeline.py")
    master = load_all_sources(raw_dir=Path("data/raw"))
    save_master(master, processed_dir=Path("data/processed"))
    print_coverage_report(master)
    print("[OK] Data pipeline complete -- master_dataset.csv saved to data/processed/")
