"""Owner: frontend developer (Streamlit)."""
from __future__ import annotations

from datetime import date

import streamlit as st

from data import catalog, repository
from frontend import coordination_game, i18n, metric_inputs, state, topbar, ui
from frontend.i18n import t

_TEST_SCORE = "create_test_score"
_TEST_COUNT = "create_test_count"


def render() -> None:
    topbar.render(t("create.heading"))
    ui.html(f'<p class="ah-lead">{ui.esc(t("create.intro"))}</p>')

    if st.toggle(t("create.game_expander"), key="create_show_test"):
        ui.html(f'<p class="ah-note">{ui.esc(t("create.game_hint"))}</p>')
        try:
            result = coordination_game.play("create_test")
        except ValueError:
            result = None
            st.warning(t("game.error"))
        if result is not None:
            st.session_state[_TEST_SCORE] = result.score_pct
            st.session_state[_TEST_COUNT] = st.session_state.get(_TEST_COUNT, 0) + 1

    tested = st.session_state.get(_TEST_SCORE)
    defaults = catalog.default_values()
    if tested is not None:
        defaults["coordination_pct"] = tested

    glucose_unit = metric_inputs.glucose_unit_selector("create")
    with ui.form("create_form"):
        name_column, age_column, date_column = st.columns([2, 1, 1])
        with name_column:
            name = st.text_input(t("create.name"), max_chars=60, key="create_name")
        with age_column:
            age = st.number_input(t("create.age"), min_value=18, max_value=90, value=35,
                                  step=1, key="create_age")
        with date_column:
            flight_start = st.date_input(t("create.flight_start"), value=date.today(),
                                         format=i18n.date_input_format(),
                                         key="create_flight_start")

        ui.html(f'<h2 class="ah-heading">{ui.esc(t("create.baseline_heading"))}</h2>'
                f'<p class="ah-note">{ui.esc(t("create.prefilled_note"))}</p>')
        if tested is not None:
            ui.html(f'<p class="ah-note">{ui.esc(t("create.game_filled", score=tested))}</p>')
        values = metric_inputs.render(
            "create", defaults, baseline_only=True, glucose_unit=glucose_unit,
            coordination_token=str(st.session_state.get(_TEST_COUNT, "")))
        submitted = ui.submit_button(t("create.submit"))

    if ui.button(t("create.cancel"), key="create_cancel", stretch=False):
        _forget_test()
        state.go(state.MENU)

    if submitted:
        _create(name, int(age), flight_start, values)


def _create(name: str, age: int, flight_start: date, values: dict) -> None:
    clean_name = repository.normalize_name(name)
    if not clean_name:
        st.error(t("create.error_name_empty"))
        return
    if repository.profile_name_exists(clean_name):
        st.error(t("create.error_name_taken", name=clean_name))
        return
    try:
        profile_id = repository.create_profile(clean_name, age, flight_start, values)
    except ValueError as error:
        st.error(t("form.error_values", error=error))
        return
    _forget_test()
    state.flash(t("create.created"))
    state.open_profile(profile_id)


def _forget_test() -> None:
    for key in (_TEST_SCORE, _TEST_COUNT):
        st.session_state.pop(key, None)
