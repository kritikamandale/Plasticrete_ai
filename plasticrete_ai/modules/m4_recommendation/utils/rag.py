"""
FAISS-based RAG retrieval for M4 knowledge base analogues.
"""
from __future__ import annotations

from typing import List

import numpy as np

from modules.m4_recommendation.utils.schema import RAGAnalogue
from modules.m4_recommendation.model import classifiers


def retrieve(m1_properties: dict, top_k: int = 3) -> List[RAGAnalogue]:
    """Retrieve the top-k most similar knowledge base entries via FAISS L2 search."""
    prop_cols = classifiers.config.get("property_features", [
        "compressive_strength_mpa", "flexural_strength_mpa", "split_tensile_mpa",
        "density_kgm3", "water_absorption_pct", "thermal_conductivity_wm", "durability_index",
    ])

    query        = np.array([[m1_properties.get(p, 0.0) for p in prop_cols]], dtype=np.float32)
    query_scaled = classifiers.rag_scaler.transform(query).astype(np.float32)
    distances, indices = classifiers.faiss_index.search(query_scaled, top_k)

    results: List[RAGAnalogue] = []
    for rank, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
        e = classifiers.rag_kb[idx]
        results.append(RAGAnalogue(
            rank=rank,
            id=e["id"],
            author=e["author"],
            year=e["year"],
            journal=e["journal"],
            doi=e["doi"],
            primary_application=e["primary_application"],
            secondary_application=e.get("secondary_application", "N/A"),
            l2_distance=round(float(dist), 4),
            properties={p: e[p] for p in prop_cols},
        ))
    return results
