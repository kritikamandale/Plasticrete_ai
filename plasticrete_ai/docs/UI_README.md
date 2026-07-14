# PlastiCrete AI — Premium Streamlit UI

A civil-engineering-grade front end for the four PlastiCrete ML modules
(Predict · Optimise · Score · Recommend) plus an Explainability Lab and a
clustering Insights page. Structural blue-grey + amber + sustainability green,
monospaced instrument-readout numerals, blueprint-grid motifs, animated gauges,
live-updating sliders, and a full dark mode.

## Run locally

```bash
cd plasticrete_ai
pip install -r requirements.txt          # streamlit ≥ 1.40, plotly, pyyaml already listed
streamlit run app.py
```

Open http://localhost:8501. The sidebar exposes all 7 pages; the top bar has the
segment switcher, a dark-mode toggle, and **Run New Prediction**.

> Requires **Streamlit ≥ 1.40** (uses `st.navigation` / `st.Page` /
> `st.segmented_control`; verified on 1.58). To enable the **real M4 recommender**
> install `faiss-cpu` (`pip install faiss-cpu`) — without it, M4 falls back to
> realistic demo data automatically.

## `ui/` structure

```
app.py                     # nav shell: st.navigation + st.Page, theme + session bootstrap, top bar
.streamlit/config.toml     # base light theme tokens
.streamlit/style.css       # premium CSS (fonts, cards, blueprint motif, dark override, animations)
ui/
├── theme.py               # palette, config-driven metadata (TARGET_META, APP_META, SDG), load_css()
├── nav.py                 # page registry → goto() for cross-page buttons
├── components.py          # metric_card, kpi_row, plastic_chip, score gauge, compliance_pill,
│                          #   citation_card, sdg_badge, workflow_rail, application_card, quick_action_tile
├── charts.py              # Plotly (themed): radar, SHAP waterfall, gauge, Pareto, PDP/ICE,
│                          #   tornado, cluster scatter, PCA biplot, heatmap, beeswarm
├── data_bridge.py         # real module ↔ mock adapters (cached); the only thing that touches modules/
├── mock_data.py           # realistic fallback mirroring every real return shape
└── pages/
    ├── dashboard.py          m1_prediction.py     m2_optimiser.py
    ├── m3_sustainability.py   m4_recommender.py    explainability.py    insights.py
```

## How `data_bridge.py` swaps real ↔ mock

Every backend call is wrapped:

```python
def predict(mix): 
    try:    return _norm_prediction(_load_m1().predict(mix))   # real → normalised dict, source="real"
    except: return mock_data.prediction()                      # graceful fallback, source="mock"
```

- Heavy model loads (`m1.load_ensemble`, ~33 s cold) go through `@st.cache_resource`
  so they run **once per session**; per-mix results are memoised with `@st.cache_data`.
- Real dataclasses (`PredictionResult`, `RecommendationResult`, …) are **normalised to
  plain dicts** with the same keys the mock provides, so pages never branch on
  real-vs-mock. A `● live model` / `● demo data` chip shows which is active.
- Slider ranges, class lists, targets and standards come from `configs/*.yaml` +
  `modules/…/schema.py` (via `data_bridge.input_ranges()` and `ui.theme`) — never
  hard-coded where a config already owns the value.

Verified real in this environment: **M1, M2, M3**. Mock fallback: **M4** (needs `faiss-cpu`).
See [UI_RECON_NOTES.md](UI_RECON_NOTES.md) for the full interface map and gaps.

## Session flow (M1 → M3 → M4 → M2)

`st.session_state` holds one shared formulation (`mix`, `prediction`, `score`,
`recommendation`). Running **Predict** on M1 refreshes all three so Sustainability,
Recommender, and Optimiser stay in sync with the active mix. The workflow rail on
the dashboard visualises this dependency.

## Hugging Face Spaces entry note

`app.py` is the Space entrypoint — a Streamlit Space runs `streamlit run app.py`
directly, wiring the UI to the modules in-process (no sidecar API needed).

**Legacy path (preserved, untouched):** the previous `app.py` was a dual-process
launcher (uvicorn FastAPI `deployment/api/app:app` + the old
`deployment/frontend/streamlit_app.py`). Both remain under `deployment/` and in git
history for the API-based deployment; only the top-level `app.py` was refactored
into the new nav shell.

## Notes

- All charts are themed via `ui.charts` and flip with dark mode.
- `prefers-reduced-motion` disables animations (CSS-guarded).
- `use_container_width=True` is used throughout; on Streamlit builds after its
  removal date, swap to `width="stretch"` (a mechanical find-replace).
