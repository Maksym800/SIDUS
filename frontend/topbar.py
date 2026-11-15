"""Owner: frontend developer (Streamlit)."""
from __future__ import annotations

import streamlit as st

from data import catalog
from frontend import state, ui
from frontend.i18n import t


def render(title: str) -> None:
    title_column, environment_column, language_column = st.columns(
        [5, 2.4, 1.5], vertical_alignment="bottom")

    with title_column:
        ui.html(f'<h1 class="ah-title">{ui.esc(title)}</h1>')

    with environment_column:
        codes = list(catalog.ENVIRONMENTS)
        chosen = st.selectbox(
            t("topbar.environment"), codes,
            index=codes.index(state.environment()),
            format_func=lambda code: t(f"env.{code}"),
            key="topbar_environment",
        )
        if chosen != state.environment():
            state.set_environment(chosen)

    with language_column:
        if ui.button(t("lang.switch_to"), key="topbar_language",
                     help=t("topbar.language_help")):
            state.set_language("uk" if state.language() == "en" else "en")
            st.rerun()
