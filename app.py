"""Owner: frontend developer (Streamlit)."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from data import db
from frontend import state, theme
from frontend.i18n import t
from frontend.views import astronaut, edit_metrics, game, history, profile_create, profile_menu

ICON = Path(__file__).resolve().parent / "assets" / "favicon.png"

SCREENS = {
    state.MENU: profile_menu.render,
    state.CREATE: profile_create.render,
    state.ASTRONAUT: astronaut.render,
    state.EDIT: edit_metrics.render,
    state.HISTORY: history.render,
    state.GAME: game.render,
}


def main() -> None:
    db.init_db()
    state.init()
    st.set_page_config(page_title=t("app.title"),
                       page_icon=str(ICON) if ICON.is_file() else "🚀",
                       layout="wide", initial_sidebar_state="collapsed")
    theme.inject()
    SCREENS.get(state.view(), profile_menu.render)()


main()
