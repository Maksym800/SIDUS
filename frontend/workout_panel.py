"""Owner: frontend developer (Streamlit)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

import streamlit as st

from backend.analytics import flight, history, workouts
from data import repository
from frontend import calendars, i18n, ui
from frontend.i18n import t


def render(profile: Mapping[str, Any], now: datetime) -> None:
    today = now.date()
    profile_id = profile["id"]
    ui.html(f'<h2 class="ah-heading">{ui.esc(t("workout.heading"))}</h2>')

    reminder_column, calendar_column = st.columns([6, 5], gap="large")

    with reminder_column:
        status = repository.get_workout_status(profile_id, today)
        if workouts.needs_reminder(status):
            stage = t(f"stage.{flight.flight_stage(flight.flight_day(profile['flight_start'], today))}")
            ui.html(
                f'<div class="ah-reminder"><p>{ui.esc(t("workout.reminder"))}</p>'
                f'<p class="ah-note">{ui.esc(t("workout.stage", stage=stage))}</p></div>')
            done_column, none_column = st.columns(2)
            with done_column:
                if ui.button(t("workout.done_button"), key="workout_done"):
                    repository.set_workout(profile_id, today, workouts.DONE)
                    st.rerun()
            with none_column:
                if ui.button(t("workout.none_button"), key="workout_none"):
                    repository.set_workout(profile_id, today, workouts.NOT_SCHEDULED)
                    st.rerun()
        else:
            answer = "workout.done_status" if status == workouts.DONE else "workout.none_status"
            ui.html(f'<p class="ah-lead">{ui.esc(t(answer))}</p>')
            if ui.button(t("workout.change"), key="workout_change", stretch=False):
                repository.clear_workout(profile_id, today)
                st.rerun()

        everything = repository.get_workouts(profile_id)
        done_this_month = workouts.done_in_month(everything, today.year, today.month)
        average = i18n.format_number(workouts.weekly_average(everything, today), 1)
        ui.html(
            f'<p class="ah-note">{ui.esc(t("workout.month_total", count=done_this_month))}<br>'
            f'{ui.esc(t("workout.weekly_average", value=average))}</p>')

    with calendar_column:
        year, month = calendars.month_navigation("workout_month", today)
        first, after_last = history.month_bounds(year, month)
        shown = repository.get_workouts(profile_id, first.date(), after_last.date())
        calendars.workout_calendar(workouts.month_marks(shown, year, month), year, month, today)
