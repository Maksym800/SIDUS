"""Owner: frontend developer (Streamlit)."""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from data import repository
from frontend import actions, i18n, metric_inputs, state, topbar, ui
from frontend.i18n import t


def render() -> None:
    profile = actions.current_profile()
    if profile is None:
        state.go(state.MENU, profile_id=None)
        return
    current = repository.get_latest_entry(profile["id"])

    topbar.render(profile["name"])
    ui.html(f'<h2 class="ah-heading">{ui.esc(t("edit.heading"))}</h2>'
            f'<p class="ah-lead">{ui.esc(t("edit.intro"))}</p>')

    glucose_unit = metric_inputs.glucose_unit_selector("edit")
    with ui.form("edit_form"):
        values = metric_inputs.render("edit", repository.entry_values(current),
                                      baseline_only=False, glucose_unit=glucose_unit)
        submitted = ui.submit_button(t("edit.save"))

    if ui.button(t("edit.cancel"), key="edit_cancel", stretch=False):
        state.go(state.ASTRONAUT)

    if submitted:
        try:
            actions.save_entry(profile["id"], values, "manual")
        except ValueError as error:
            st.error(t("form.error_values", error=error))
            return
        state.flash(t("edit.saved", when=i18n.format_time(datetime.now())))
        state.go(state.ASTRONAUT)
