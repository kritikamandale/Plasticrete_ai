"""
Tiny navigation registry so any page can jump to another page.

`app.py` builds the `st.Page` objects and registers them here; page modules call
`goto("m1")` from button callbacks. Kept separate to avoid circular imports.
"""
from __future__ import annotations

import streamlit as st

_PAGES: dict = {}


def register(key: str, page) -> None:
    _PAGES[key] = page


def get(key: str):
    return _PAGES.get(key)


def goto(key: str) -> None:
    page = _PAGES.get(key)
    if page is not None:
        st.switch_page(page)
