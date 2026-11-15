"""Owner: frontend developer (Streamlit)."""
from __future__ import annotations

from typing import Any

import streamlit as st

from data import catalog, repository
from frontend import i18n

MENU, CREATE, ASTRONAUT, EDIT, HISTORY, GAME = (
    "menu", "create", "astronaut", "edit", "history", "game")

_LANGUAGE_SETTING = "language"
_ENVIRONMENT_SETTING = "environment"


def init() -> None:
    session = st.session_state
    if "lang" not in session:
        saved = repository.get_setting(_LANGUAGE_SETTING, i18n.DEFAULT_LANGUAGE)
        session["lang"] = saved if saved in i18n.LANGUAGES else i18n.DEFAULT_LANGUAGE
    if "env" not in session:
        saved = repository.get_setting(_ENVIRONMENT_SETTING, catalog.BASELINE_ENVIRONMENT)
        session["env"] = saved if saved in catalog.ENVIRONMENTS else catalog.BASELINE_ENVIRONMENT
    session.setdefault("view", MENU)
    session.setdefault("profile_id", None)


def view() -> str:
    return st.session_state["view"]


def profile_id() -> int | None:
    return st.session_state["profile_id"]


def language() -> str:
    return st.session_state["lang"]


def environment() -> str:
    return st.session_state["env"]


def set_language(code: str) -> None:
    st.session_state["lang"] = code
    repository.set_setting(_LANGUAGE_SETTING, code)


def set_environment(code: str) -> None:
    st.session_state["env"] = code
    repository.set_setting(_ENVIRONMENT_SETTING, code)


def go(target: str, **updates: Any) -> None:
    st.session_state["view"] = target
    for key, value in updates.items():
        st.session_state[key] = value
    st.rerun()


_PER_PROFILE_KEYS = ("workout_month", "history_month", "history_day", "game_result")


def open_profile(profile: int) -> None:
    for key in _PER_PROFILE_KEYS:
        st.session_state.pop(key, None)
    go(ASTRONAUT, profile_id=profile)


def flash(message: str) -> None:
    st.session_state["flash"] = message


def show_flash() -> None:
    message = st.session_state.pop("flash", None)
    if message:
        st.success(message)
