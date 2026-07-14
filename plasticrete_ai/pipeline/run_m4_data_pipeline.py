"""
Stage 0 standalone runner: raw → processed → master_dataset.csv
Run: python pipeline/run_data_pipeline.py
"""
import sys
from pathlib import Path

# Allow running from plasticrete_ai/ root
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.m1_prediction.utils.data_loader import (
    load_all_sources, print_coverage_report, save_master,
)

if __name__ == "__main__":
    master = load_all_sources(raw_dir=Path("data/raw"))
    save_master(master, processed_dir=Path("data/processed"))
    print_coverage_report(master)
    print("[OK] Data pipeline complete -- master_dataset.csv saved to data/processed/")
