"""
PlastiCrete AI — Module 5: PDF Mix Design Report Generator
============================================================
Public surface:
    generate_report(mix_params, prediction, score, recommendation) -> bytes
        Returns a PDF as raw bytes, ready for a FastAPI StreamingResponse.
"""
from __future__ import annotations

from modules.m5_report.report_generator import generate_report

__all__ = ["generate_report"]
