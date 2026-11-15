"""Owner: frontend developer (Streamlit)."""
from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from backend.analytics import coordination
from frontend import theme
from frontend.i18n import t

DURATION_S = 30
HIT_RADIUS_PX = 32

_COMPONENT_DIR = Path(__file__).resolve().parent / "components" / "coordination_game"
_component = components.declare_component("coordination_game", path=str(_COMPONENT_DIR))

_LABELS = ("start", "again", "ready", "get_ready", "time", "on_target", "finished", "seconds")


def play(key: str) -> coordination.GameResult | None:
    payload = _component(
        duration=DURATION_S,
        radius=HIT_RADIUS_PX,
        labels={name: t(f"game.js.{name}") for name in _LABELS},
        colors={"background": theme.BACKGROUND, "text": theme.TEXT,
                "button": theme.BUTTON, "accent": theme.ACCENT},
        key=key,
        default=None,
    )
    if not isinstance(payload, dict):
        return None
    seen_key = f"{key}_last_test"
    if payload.get("id") == st.session_state.get(seen_key):
        return None
    st.session_state[seen_key] = payload.get("id")
    return coordination.summarize(payload)
