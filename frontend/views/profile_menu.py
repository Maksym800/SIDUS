from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

import streamlit as st

from backend.analytics import flight, freshness
from data import repository
from frontend import i18n, state, topbar, ui
from frontend.i18n import t

_CARDS_PER_ROW = 3


def render() -> None:
    topbar.render(t("app.title"))
    state.show_flash()

    now = datetime.now()
    profiles = freshness.with_freshness(repository.list_profiles(), now)

    ui.html(f'<h2 class="ah-heading">{ui.esc(t("menu.heading"))}</h2>'
            f'<p class="ah-lead">{ui.esc(t("menu.intro"))}</p>')

    if profiles.empty:
        st.info(t("menu.empty"))
    else:
        records = profiles.to_dict("records")
        for start in range(0, len(records), _CARDS_PER_ROW):
            row = records[start:start + _CARDS_PER_ROW]
            for column, profile in zip(st.columns(_CARDS_PER_ROW), row):
                with column:
                    _card(profile, now)
        if bool(profiles["is_stale"].any()):
            ui.html(f'<p class="ah-note">{ui.esc(t("menu.stale_legend"))}</p>')

    if ui.button(t("menu.create"), key="menu_create", stretch=False):
        state.go(state.CREATE)


def _flight_line(profile: Mapping[str, Any], now: datetime) -> str:
    start = profile["flight_start"].date()
    day = flight.flight_day(start, now.date())
    if day >= 1:
        return t("menu.flight_day", day=day)
    return t("menu.preflight", days=flight.days_to_launch(start, now.date()))


def _card(profile: Mapping[str, Any], now: datetime) -> None:
    profile_id = int(profile["id"])
    stale = bool(profile["is_stale"])
    alert = ""
    if stale:
        warning = ui.esc(t("menu.stale"))
        alert = f'<span class="ah-alert" role="img" aria-label="{warning}" title="{warning}">!</span>'
    updated = t("menu.last_update", when=i18n.format_datetime(profile["last_entry_at"]))

    with st.container(border=True, key=f"card_profile_{profile_id}"):
        ui.html(
            f'<p class="ah-pname">{alert}<span>{ui.esc(profile["name"])}</span></p>'
            f'<p class="ah-meta">{ui.esc(t("menu.age", age=int(profile["age"])))}</p>'
            f'<p class="ah-meta">{ui.esc(_flight_line(profile, now))}</p>'
            f'<p class="ah-meta{" ah-late" if stale else ""}">{ui.esc(updated)}</p>')
        if ui.button(t("menu.open"), key=f"menu_open_{profile_id}"):
            state.open_profile(profile_id)
