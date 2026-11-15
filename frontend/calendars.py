from __future__ import annotations

from datetime import date
from typing import Any, Mapping

import streamlit as st

from backend.analytics import history, workouts
from frontend import i18n, theme, ui
from frontend.i18n import t


def month_navigation(state_key: str, today: date) -> tuple[int, int]:
    if state_key not in st.session_state:
        st.session_state[state_key] = (today.year, today.month)
    year, month = st.session_state[state_key]

    back, title, forward = st.columns([1, 4, 1], vertical_alignment="center")
    step = 0
    with back:
        if ui.button("‹", key=f"{state_key}_previous", help=t("calendar.previous")):
            step = -1
    with forward:
        if ui.button("›", key=f"{state_key}_next", help=t("calendar.next")):
            step = 1
    if step:
        st.session_state[state_key] = history.shift_month(year, month, step)
        st.rerun()
    with title:
        ui.html(f'<p class="ah-month">{ui.esc(i18n.month_title(year, month))}</p>')
    return year, month


def workout_calendar(marks: Mapping[int, str], year: int, month: int, today: date) -> None:
    cells = [f'<div class="ah-weekday">{ui.esc(name)}</div>' for name in i18n.weekdays()]
    for week in history.month_grid(year, month):
        for day in week:
            if not day:
                cells.append("<div></div>")
                continue
            this_day = date(year, month, day)
            classes, label = [], str(day)
            status = marks.get(day)
            if status == workouts.DONE:
                classes.append("ah-done")
                label = f'{day}: {t("workout.legend_done")}'
            elif status == workouts.NOT_SCHEDULED:
                classes.append("ah-rest")
                label = f'{day}: {t("workout.legend_none")}'
            elif this_day > today:
                classes.append("ah-later")
            if this_day == today:
                classes.append("ah-today")
            cells.append(f'<div class="{" ".join(classes)}" title="{ui.esc(label)}">{day}</div>')
    legend = "".join(
        f'<li><span class="ah-swatch {css}"></span>{ui.esc(t(text))}</li>'
        for css, text in (("ah-done", "workout.legend_done"), ("ah-rest", "workout.legend_none"),
                          ("ah-today", "workout.legend_today")))
    ui.html(f'<div class="ah-cal">{"".join(cells)}</div><ul class="ah-callegend">{legend}</ul>')


def _day_key(day: date) -> str:
    return f"history_day_{day:%Y%m%d}"


def history_calendar(summary: Mapping[int, Mapping[str, Any]], year: int, month: int,
                     selected: date | None) -> date | None:
    header = st.columns(7)
    for column, name in zip(header, i18n.weekdays()):
        with column:
            ui.html(f'<div class="ah-weekday">{ui.esc(name)}</div>')

    clicked = None
    rules = []
    for week in history.month_grid(year, month):
        for column, day in zip(st.columns(7), week):
            if not day:
                continue
            this_day = date(year, month, day)
            info = summary.get(day)
            with column:
                if ui.button(str(day), key=_day_key(this_day), disabled=info is None):
                    clicked = this_day
            if info is not None:
                colour = theme.severity_colour(info["severity"] or 0)
                rules.append(f".st-key-{_day_key(this_day)} button "
                             f"{{ box-shadow: inset 0 -5px 0 {colour}; }}")
            if selected == this_day:
                rules.append(f".st-key-{_day_key(this_day)} button "
                             f"{{ outline: 2px solid {theme.TEXT}; outline-offset: 2px; }}")
    if rules:
        ui.html(f"<style>{' '.join(rules)}</style>")
    return clicked
