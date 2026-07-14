"""
Design tokens, config-driven metadata, and CSS injection for PlastiCrete AI.

`load_css()` reads `.streamlit/style.css` and (in dark mode) appends a variable
override so the whole palette flips with a single toggle.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent
_CSS_PATH = _ROOT / ".streamlit" / "style.css"

# ── Palette (mirrors the CSS variables so Plotly can share it) ────────────────
PALETTE = {
    "bg":         "#F7F8FA",
    "surface":    "#FFFFFF",
    "text":       "#0F172A",
    "muted":      "#64748B",
    "border":     "#E2E8F0",
    "primary":    "#2B3A55",
    "primary_2":  "#3E5277",
    "amber":      "#F59E0B",
    "green":      "#16A34A",
    "green_2":    "#22C55E",
    "red":        "#DC2626",
}

PALETTE_DARK = {
    **PALETTE,
    "bg":       "#0B1220",
    "surface":  "#111A2B",
    "text":     "#E2E8F0",
    "muted":    "#94A3B8",
    "border":   "#243247",
}

PLASTIC_COLORS = {
    "PET": "#06B6D4", "HDPE": "#8B5CF6", "LDPE": "#EC4899",
    "PVC": "#F97316", "PP": "#10B981", "Mixed": "#64748B",
}
PLASTIC_TYPES = ["PET", "HDPE", "LDPE", "PVC", "PP", "Mixed"]
ADDITIVE_TYPES = ["none", "fly_ash", "silica_fume", "fibres"]

# UN SDG official colours + labels
SDG_INFO = {
    3:  ("#4C9F38", "Good Health & Well-being"),
    9:  ("#FD6925", "Industry, Innovation & Infrastructure"),
    11: ("#FD9D24", "Sustainable Cities & Communities"),
    12: ("#BF8B2E", "Responsible Consumption & Production"),
    13: ("#3F7E44", "Climate Action"),
}

# ── 7 predicted properties: label · unit · standard · (min,max) · icon ────────
TARGET_META = {
    "compressive_strength_mpa": ("Compressive Strength", "MPa", "IS 516",   (0.0, 90.0),  "🧱"),
    "flexural_strength_mpa":    ("Flexural Strength",    "MPa", "ASTM C78", (0.0, 15.0),  "〰️"),
    "split_tensile_mpa":        ("Split Tensile",        "MPa", "IS 5816",  (0.0, 10.0),  "🔩"),
    "density_kgm3":             ("Density",              "kg/m³", "—",       (1200.0, 2600.0), "⚖️"),
    "water_absorption_pct":     ("Water Absorption",     "%",   "IS 2185",  (0.0, 25.0),  "💧"),
    "thermal_conductivity_wm":  ("Thermal Conductivity", "W/m·K", "—",      (0.10, 2.50), "🌡️"),
    "durability_index":         ("Durability Index",     "/100", "0–100 composite", (0.0, 100.0), "🛡️"),
}
TARGET_ORDER = list(TARGET_META.keys())

# ── M4: 12 real application categories → display label · icon · structural? ──
APP_META = {
    "paving_block_light":          ("Paving Blocks · Light",       "🧱", False),
    "paving_block_heavy":          ("Paving Blocks · Heavy-Duty",  "🧱", True),
    "floor_tile_indoor":           ("Floor Tiles · Indoor",        "▦",  False),
    "floor_tile_outdoor":          ("Floor Tiles · Outdoor",       "▦",  False),
    "hollow_concrete_block":       ("Hollow Concrete Blocks",      "🧱", False),
    "lightweight_partition_block": ("Partition Wall Panels",       "🧱", False),
    "structural_concrete":         ("Structural Concrete",         "🏗️", True),
    "nonstructural_concrete_fill": ("Non-Structural Concrete Fill","🪨", False),
    "plastic_sand_paver":          ("Plastic-Sand Pavers",         "🟫", False),
    "wall_cladding_panel":         ("Wall Cladding Panels",        "🪟", False),
    "thermal_insulation_panel":    ("Thermal Insulation Panels",   "🌡️", False),
    "kerb_stone":                  ("Kerb Stones",                 "⬛", True),
}

# BIS standards shown on the compliance checklist
BIS_STANDARDS = {
    "is_1237": ("IS 1237",  "Cement concrete flooring tiles"),
    "is_2185": ("IS 2185",  "Concrete masonry blocks"),
    "is_516":  ("IS 516",   "Methods of test for concrete strength"),
    "is_5816": ("IS 5816",  "Splitting tensile strength of concrete"),
    "nbc":     ("NBC 2016", "National Building Code (structural)"),
}


def label_app(key: str) -> str:
    return APP_META.get(key, (key.replace("_", " ").title(), "🧱", False))[0]


def plastic_class(ptype: str) -> str:
    return ptype.lower()


_DARK_OVERRIDE = """
<style id="pc-dark">
:root {
  --pc-bg:#0B1220; --pc-surface:#111A2B; --pc-surface-2:#0F1826; --pc-inset:#0E1727;
  --pc-text:#E2E8F0; --pc-text-muted:#94A3B8; --pc-border:#243247; --pc-border-strong:#334155;
  --pc-amber-soft:#3a2c07; --pc-green-soft:#0c2a19; --pc-red-soft:#33161a;
  --pc-grid-line:rgba(148,163,184,.08);
  --pc-shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.35);
  --pc-shadow-lg:0 2px 4px rgba(0,0,0,.45), 0 18px 48px rgba(0,0,0,.5);
}
[data-testid="stMetricValue"], .stMarkdown, .stMarkdown p { color: var(--pc-text); }
.pc-pill.pass{color:#86efac} .pc-pill.warn{color:#fcd34d} .pc-pill.fail{color:#fca5a5}
</style>
"""


def load_css(dark: bool = False) -> None:
    """Inject the base stylesheet, plus the dark override when requested."""
    try:
        css = _CSS_PATH.read_text(encoding="utf-8")
    except OSError:
        css = ""
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    if dark:
        st.markdown(_DARK_OVERRIDE, unsafe_allow_html=True)


def palette(dark: bool = False) -> dict:
    return PALETTE_DARK if dark else PALETTE


def page_header(title: str, subtitle: str = "", eyebrow: str = "") -> None:
    """Consistent page title block."""
    eb = f"<div class='pc-eyebrow-dark'>{eyebrow}</div>" if eyebrow else ""
    sub = f"<p class='pc-card-sub' style='font-size:.92rem;margin-top:2px'>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"<div style='margin-bottom:14px'>{eb}"
        f"<h1 style='font-size:1.7rem;margin:2px 0 0'>{title}</h1>{sub}</div>",
        unsafe_allow_html=True,
    )
