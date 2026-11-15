"""Owner: frontend developer (Streamlit)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping

import streamlit as st

from backend.analytics import deviations, export, history
from data import catalog, repository
from backend.diagnosis import knowledge_base
from frontend import actions, calendars, findings, i18n, state, topbar, ui
from frontend.i18n import t

_ROW_HEIGHT = 35
_SELECTED_DAY = "history_day"


def render() -> None:
    profile = actions.current_profile()
    if profile is None:
        state.go(state.MENU, profile_id=None)
        return

    topbar.render(profile["name"])
    if ui.button(t("history.back"), key="history_back", stretch=False):
        state.go(state.ASTRONAUT)
    ui.html(f'<h2 class="ah-heading">{ui.esc(t("history.heading"))}</h2>'
            f'<p class="ah-lead">{ui.esc(t("history.intro"))}</p>')

    calendar_column, day_column = st.columns([5, 7], gap="large")
    with calendar_column:
        year, month = calendars.month_navigation("history_month", date.today())
        first, after_last = history.month_bounds(year, month)
        entries = repository.get_entries(profile["id"], first, after_last)
        runs = repository.get_runs(profile["id"], first, after_last)
        summary = history.day_summary(entries, runs)
        selected = st.session_state.get(_SELECTED_DAY)
        clicked = calendars.history_calendar(summary, year, month, selected)
        if clicked is not None:
            st.session_state[_SELECTED_DAY] = clicked
            st.rerun()
        if not summary:
            ui.html(f'<p class="ah-note">{ui.esc(t("history.empty_month"))}</p>')

    with day_column:
        in_shown_month = (selected is not None and (selected.year, selected.month) == (year, month)
                          and selected.day in summary)
        if in_shown_month:
            _day(profile, history.entries_on(entries, selected), runs, selected)
        elif summary:
            st.info(t("history.pick_day"))

    st.divider()
    _export(profile)


def _export(profile: Mapping[str, Any]) -> None:
    ui.html(f'<h2 class="ah-subheading">{ui.esc(t("history.export_heading"))}</h2>'
            f'<p class="ah-note">{ui.esc(t("history.export_note"))}</p>')
    entries = repository.get_entries(profile["id"])
    if entries.empty:
        ui.html(f'<p class="ah-note">{ui.esc(t("history.export_nothing"))}</p>')
        return
    runs = repository.get_runs(profile["id"])
    run_findings = repository.get_findings(runs["id"])
    language = state.language()
    metrics = export.metrics_table(entries)
    diagnoses = export.diagnoses_table(
        runs, run_findings, lambda code: knowledge_base.describe(code, language).name)
    stem = f"{profile['name'].strip().replace(' ', '_')}_{datetime.now():%Y%m%d}"
    first, second = st.columns(2)
    with first:
        ui.download_button(t("history.export_metrics"), export.to_csv(metrics),
                           f"{stem}_metrics.csv", key="export_metrics")
    with second:
        ui.download_button(t("history.export_diagnoses"), export.to_csv(diagnoses),
                           f"{stem}_diagnoses.csv", key="export_diagnoses")


def _day(profile: Mapping[str, Any], day_entries, runs, day: date) -> None:
    ui.html(f'<h2 class="ah-heading">{ui.esc(i18n.format_date(day))}</h2>'
            f'<p class="ah-note">{ui.esc(t("history.changed_note"))}</p>')
    baseline = repository.get_baseline(profile["id"])
    entry_ids = [int(entry_id) for entry_id in day_entries["id"]]
    day_runs = runs[runs["entry_id"].isin(entry_ids)]
    diagnoses = history.runs_by_entry(day_runs, repository.get_findings(day_runs["id"]))

    for entry_id in entry_ids:
        entry = repository.get_entry(entry_id)
        with st.container(border=True, key=f"card_entry_{entry_id}"):
            _entry(entry, baseline, diagnoses.get(entry_id, []))


def _entry(entry: Mapping[str, Any], baseline: Mapping[str, Any],
           diagnoses: list[dict[str, Any]]) -> None:
    title = t("history.entry_title", time=i18n.format_time(entry["recorded_at"], seconds=True))
    source = t(f"history.source.{entry['source']}")
    environment = t("history.environment", env=t(f"env.{entry['environment']}"))
    ui.html(f'<h3 class="ah-subheading">{ui.esc(title)}</h3>'
            f'<p class="ah-note">{ui.esc(source)}<br>{ui.esc(environment)}</p>')

    if not diagnoses:
        ui.html(f'<p class="ah-note">{ui.esc(t("history.no_diagnosis"))}</p>')
    for diagnosis in diagnoses:
        heading = t("history.diagnosis_title",
                    when=i18n.format_datetime(diagnosis["diagnosed_at"]),
                    env=t(f"env.{diagnosis['environment']}"))
        if diagnosis["findings"]:
            body = findings.findings_html(diagnosis["findings"], compact=True)
        else:
            body = f'<p class="ah-lead">{ui.esc(t("history.diagnosis_clear"))}</p>'
        ui.html(f'<p class="ah-note">{ui.esc(heading)}</p>{body}')

    with st.expander(t("history.metrics_expander")):
        changed = deviations.changed_keys(entry, repository.get_previous_entry(entry))
        rows = []
        for key in catalog.KEYS:
            value = i18n.format_metric(key, entry.get(key))
            rows.append({
                t("table.metric"): i18n.metric_label(key),
                t("table.value"): f"{value} *" if key in changed else value,
                t("table.baseline"): i18n.format_metric(key, baseline.get(key)),
            })
        st.dataframe(rows, hide_index=True, height=_ROW_HEIGHT * (len(rows) + 1) + 3)
