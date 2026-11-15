from __future__ import annotations

import streamlit as st

from backend.analytics import coordination
from data import repository
from frontend import actions, coordination_game, i18n, state, theme, topbar, ui
from frontend.i18n import t

_RESULT = "game_result"


def render() -> None:
    profile = actions.current_profile()
    if profile is None:
        state.go(state.MENU, profile_id=None)
        return

    topbar.render(profile["name"])
    if ui.button(t("game.back"), key="game_back", stretch=False):
        state.go(state.ASTRONAUT, game_result=None)
    ui.html(f'<h2 class="ah-heading">{ui.esc(t("game.heading"))}</h2>'
            f'<p class="ah-lead">'
            f'{ui.esc(t("game.intro", seconds=coordination_game.DURATION_S))}</p>')

    try:
        finished = coordination_game.play("game_field")
    except ValueError:
        finished = None
        st.warning(t("game.error"))
    if finished is not None:
        st.session_state[_RESULT] = finished

    result = st.session_state.get(_RESULT)
    if result is None:
        _progress(profile)
        return

    baseline = repository.get_baseline(profile["id"])
    details = t("game.details",
                on=i18n.format_number(result.on_target_s, 1),
                total=i18n.format_number(result.total_s, 0),
                hold=i18n.format_number(result.longest_hold_s, 1))
    compare = t("game.baseline", baseline=baseline["coordination_pct"])
    ui.html(f'<h2 class="ah-heading">{ui.esc(t("game.result", score=result.score_pct))}</h2>'
            f'<p class="ah-note">{ui.esc(details)}<br>{ui.esc(compare)}</p>')

    if ui.button(t("game.save"), key="game_save", stretch=False):
        values = repository.entry_values(repository.get_latest_entry(profile["id"]))
        values["coordination_pct"] = result.score_pct
        actions.save_entry(profile["id"], values, "game")
        state.flash(t("game.saved", score=result.score_pct))
        state.go(state.ASTRONAUT, game_result=None)

    _progress(profile)


def _progress(profile) -> None:
    ui.html(f'<h2 class="ah-heading">{ui.esc(t("game.progress_heading"))}</h2>')
    entries = repository.get_entries(profile["id"])
    summary = coordination.progress(entries)
    if summary is None or len(summary.series) < 2:
        ui.html(f'<p class="ah-note">{ui.esc(t("game.progress_empty"))}</p>')
        return
    baseline = repository.get_baseline(profile["id"])["coordination_pct"]
    chart = summary.series.assign(baseline=float(baseline)).rename(columns={
        "score": t("game.series.score"), "average": t("game.series.average"),
        "baseline": t("game.series.baseline")})
    st.line_chart(chart, color=[theme.ACCENT, theme.BUTTON, theme.STATUS[0]], height=280)
    change = f"{'+' if summary.change > 0 else ''}{i18n.format_number(summary.change, 1)}"
    ui.html(f'<p class="ah-note">{ui.esc(t("game.progress_summary", count=len(summary.series), best=summary.best, latest=summary.latest, first=i18n.format_number(summary.mean_first, 1), last=i18n.format_number(summary.mean_last, 1), change=change))}</p>')
