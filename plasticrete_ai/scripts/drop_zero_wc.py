"""Remove knowledge-base rows whose w/c is 0 and rebuild the FAISS index.

The source table for those rows is not in the repo, so the ratio is not guessed.
The index is rebuilt from the remaining rows with the scaler already on disk.
"""
from __future__ import annotations

import json
from pathlib import Path

import faiss
import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROPS = [
    "compressive_strength_mpa",
    "flexural_strength_mpa",
    "split_tensile_mpa",
    "density_kgm3",
    "water_absorption_pct",
    "thermal_conductivity_wm",
    "durability_index",
]


def main() -> None:
    kb_path = ROOT / "models" / "m4" / "m4_rag_knowledge_base.json"
    entries = json.loads(kb_path.read_text(encoding="utf-8"))
    dropped = [
        entry for entry in entries
        if entry.get("wc_ratio") == 0 and str(entry.get("plastic_type") or "").lower() not in {"", "none"}
    ]
    kept = [entry for entry in entries if entry not in dropped]
    lines = [
        "# Knowledge-base rows removed",
        "",
        "These rows had wc_ratio 0. The source table is not in the repo, so the ratio was not guessed and the row was removed.",
        "The FAISS index was rebuilt from the remaining rows with the existing property scaler.",
        "",
    ]
    for entry in dropped:
        lines.append(f"- {entry['id']}: stored wc_ratio {entry.get('wc_ratio')}, doi {entry.get('doi')}")
    (ROOT / "reports" / "kb_dropped.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    kb_path.write_text(json.dumps(kept, indent=2) + "\n", encoding="utf-8")
    scaler = joblib.load(ROOT / "models" / "m4" / "m4_rag_property_scaler.pkl")
    matrix = np.array([[entry[name] for name in PROPS] for entry in kept], dtype=np.float32)
    scaled = scaler.transform(matrix).astype(np.float32)
    index = faiss.IndexFlatL2(scaled.shape[1])
    index.add(scaled)
    faiss.write_index(index, str(ROOT / "models" / "m4" / "m4_faiss_index.bin"))
    print(f"kept {len(kept)} dropped {len(dropped)} ntotal {index.ntotal}")


if __name__ == "__main__":
    main()
