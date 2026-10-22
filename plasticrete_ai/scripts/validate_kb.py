"""Fail when a knowledge-base entry has no DOI or a cement mix has w/c 0.

Does not invent replacement values.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB_PATH = ROOT / "models" / "m4" / "m4_rag_knowledge_base.json"


def validate(entries: list[dict]) -> list[str]:
    """Return one message per broken entry. Empty means the file passes."""
    problems: list[str] = []
    for entry in entries:
        entry_id = str(entry.get("id", ""))
        doi = str(entry.get("doi") or "").strip()
        if not doi:
            problems.append(f"{entry_id or '<no id>'}: missing DOI")
        wc = entry.get("wc_ratio")
        plastic = str(entry.get("plastic_type") or "")
        cement_based = plastic.lower() not in {"", "none"}
        if cement_based and wc == 0:
            problems.append(f"{entry_id}: wc_ratio is 0 on a cement-based mix")
    return problems


def main() -> int:
    entries = json.loads(KB_PATH.read_text(encoding="utf-8"))
    problems = validate(entries)
    if problems:
        for line in problems:
            print(line)
        return 1
    print(f"{len(entries)} entries passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
