from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

import streamlit as st

from backend.analytics import deviations, flight, freshness
from backend.diagnosis import service
from data import catalog, repository
from frontend import (actions, body_map, engine_help, findings, i18n, state, topbar, ui,
                      workout_panel)
from frontend.i18n import t

_ROW_HEIGHT = 35


def render() -> None:
    profile = actions.current_profile()
    if profile is None:
        state.go(state.MENU, profile_id=None)
        return

    topbar.render(profile["name"])
    now = datetime.now()

    assessment, engine_error = None, None
    try:
        assessment = service.assess_latest(profile["id"], state.environment())
    except service.EngineError as error:
        engine_error = error
    latest = assessment.entry if assessment else repository.get_latest_entry(profile["id"])
    baseline = assessment.baseline if assessment else repository.get_baseline(profile["id"])

    _status_row(profile, latest, now)
    state.show_flash()
    if freshness.is_stale(latest["recorded_at"], now):
        st.warning(t("astro.stale_warning"))

    figure_column, findings_column = st.columns([4, 7], gap="large")
    with figure_column:
        body_map.render(assessment.zone_levels() if assessment else {})
    with findings_column:
        _action_buttons()
        _assessment(assessment, engine_error)

    _metrics_table(profile, latest, baseline)
    st.divider()
    workout_panel.render(profile, now)


def _status_row(profile: Mapping[str, Any], latest: Mapping[str, Any], now: datetime) -> None:
    back_column, text_column = st.columns([1.4, 6], vertical_alignment="center")
    with back_column:
        if ui.button(t("astro.back"), key="astronaut_back"):
            state.go(state.MENU, profile_id=None)
    day = flight.flight_day(profile["flight_start"], now.date())
    if day >= 1:
        flight_text = t("astro.flight_day", day=day, stage=t(f"stage.{flight.flight_stage(day)}"))
    else:
        flight_text = t("astro.preflight",
                        days=flight.days_to_launch(profile["flight_start"], now.date()))
    updated = t("astro.updated", when=i18n.format_datetime(latest["recorded_at"]))
    with text_column:
        ui.html(f'<p class="ah-note">{ui.esc(flight_text)}<br>{ui.esc(updated)}</p>')


def _assessment(assessment: service.Assessment | None, engine_error: Exception | None) -> None:
    ui.html(f'<h2 class="ah-heading">{ui.esc(t("astro.assessment_heading"))}</h2>')
    if assessment is None:
        engine_help.render(engine_error)
        return
    if assessment.findings:
        ui.html(findings.findings_html(assessment.findings, assessment.entry, assessment.baseline))
    else:
        ui.html(findings.all_clear_html())
    assessed = t("astro.assessed_note",
                 when=i18n.format_datetime(assessment.diagnosed_at),
                 env=t(f"env.{assessment.environment}"),
                 entry_when=i18n.format_datetime(assessment.entry["recorded_at"]))
    ui.html(f'<p class="ah-note">{ui.esc(assessed)}</p>'
            f'<p class="ah-note">{ui.esc(t("astro.disclaimer"))}</p>')


def _action_buttons() -> None:
    edit_column, game_column, history_column = st.columns(3)
    with edit_column:
        if ui.button(t("astro.edit"), key="astronaut_edit"):
            state.go(state.EDIT)
    with game_column:
        if ui.button(t("astro.game"), key="astronaut_game"):
            state.go(state.GAME, game_result=None)
    with history_column:
        if ui.button(t("astro.history"), key="astronaut_history"):
            state.go(state.HISTORY)


def _metrics_table(profile: Mapping[str, Any], latest: Mapping[str, Any],
                   baseline: Mapping[str, Any]) -> None:
    with st.expander(t("astro.metrics_expander")):
        entries = repository.get_entries(profile["id"])
        numbers = deviations.comparison_table(latest, baseline, entries).set_index("metric")
        rows = []
        for key in catalog.KEYS:
            row = {
                t("table.metric"): i18n.metric_label(key),
                t("table.current"): i18n.format_metric(key, latest.get(key)),
                t("table.baseline"): i18n.format_metric(key, baseline.get(key)),
                t("table.change"): "",
                t("table.recent"): "",
                t("table.trend"): "",
            }
            if key in numbers.index:
                figures = numbers.loc[key]
                row[t("table.change")] = i18n.format_change(key, figures["change"])
                row[t("table.recent")] = i18n.format_metric(key, figures["recent"])
                if figures["trend"]:
                    row[t("table.trend")] = t(f"trend.{figures['trend']}")
            rows.append(row)
        st.dataframe(rows, hide_index=True, height=_ROW_HEIGHT * (len(rows) + 1) + 3)
