"""Knowledge-base validator. Does not call the model."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.validate_kb import validate  # noqa: E402


def test_placeholder_and_synthetic_flags_on_disk():
    entries = json.loads((ROOT / "models" / "m4" / "m4_rag_knowledge_base.json").read_text(encoding="utf-8"))
    for entry in entries:
        entry_id = str(entry.get("id", ""))
        doi = str(entry.get("doi") or "")
        if entry_id.startswith("SYN_") or doi == "verify-on-publisher":
            assert entry.get("verified") is False
    assert validate(entries) == []


def test_validator_rejects_empty_doi_and_zero_wc():
    problems = validate([
        {"id": "A", "doi": "", "wc_ratio": 0.45, "plastic_type": "PET"},
        {"id": "B", "doi": "10.1000/example", "wc_ratio": 0, "plastic_type": "PET"},
    ])
    assert any("missing DOI" in line for line in problems)
    assert any("wc_ratio is 0" in line for line in problems)
