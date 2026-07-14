"""PlastiCrete AI — premium Streamlit UI layer.

All UI code lives here. The backend (`modules/`, `pipeline/`, `models/`) is
treated as read-only and reached only through `ui.data_bridge`, which falls
back to `ui.mock_data` whenever a real module is unavailable.
"""
