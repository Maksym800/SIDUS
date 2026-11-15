"""Owner: frontend developer (Streamlit)."""
from __future__ import annotations

import math
from typing import Any, Mapping

import streamlit as st

from backend.analytics import units
from data import catalog
from frontend import i18n, ui
from frontend.i18n import t

_COLUMNS = 3


def glucose_unit_selector(prefix: str) -> str:
    return st.radio(
        t("form.glucose_unit"), units.GLUCOSE_UNITS,
        format_func=i18n.unit_label, horizontal=True, key=f"{prefix}_glucose_unit",
    )


def render(prefix: str, defaults: Mapping[str, Any], *, baseline_only: bool,
           glucose_unit: str = units.MMOL_L, coordination_token: str = "") -> dict[str, Any]:
    values: dict[str, Any] = {}
    for group in catalog.GROUPS:
        metrics = catalog.metrics_in_group(group, baseline_only)
        if not metrics:
            continue
        ui.html(f'<h3 class="ah-group">{ui.esc(t(f"group.{group}"))}</h3>')
        for start in range(0, len(metrics), _COLUMNS):
            row = metrics[start:start + _COLUMNS]
            for column, metric in zip(st.columns(_COLUMNS), row):
                with column:
                    values[metric.key] = _input(metric, defaults.get(metric.key), prefix,
                                                glucose_unit, coordination_token)
    return values


def _help(metric: catalog.Metric) -> str | None:
    key = f"help.{metric.key}"
    return t(key) if key in i18n.TEXTS else None


def _start_value(metric: catalog.Metric, default: Any) -> float:
    value = metric.default if catalog.is_missing(default) else float(default)
    return min(max(value, metric.minimum), metric.maximum)


def _input(metric: catalog.Metric, default: Any, prefix: str, glucose_unit: str,
           coordination_token: str) -> Any:
    key = f"{prefix}_{metric.key}"
    if metric.kind == catalog.CHOICE:
        return _choice(metric, default, key)
    if metric.kind == catalog.FLAG:
        return _flag(metric, default, key)
    if metric.kind == catalog.SCORE:
        return st.slider(i18n.metric_label(metric.key), min_value=int(metric.minimum),
                         max_value=int(metric.maximum),
                         value=int(round(_start_value(metric, default))), step=1,
                         key=key, help=_help(metric))
    if metric.key == "glucose_mmol_l" and glucose_unit == units.MG_DL:
        return _glucose_mg_dl(metric, default, key)
    if metric.key == "coordination_pct" and coordination_token:
        key = f"{key}_{coordination_token}"
    return _number(metric, default, key)


def _number(metric: catalog.Metric, default: Any, key: str) -> float:
    label = i18n.metric_label(metric.key, with_unit=True)
    start = _start_value(metric, default)
    if metric.integer:
        return st.number_input(label, min_value=int(metric.minimum), max_value=int(metric.maximum),
                               value=int(round(start)), step=int(metric.step), key=key,
                               help=_help(metric))
    decimals = i18n.metric_decimals(metric)
    return st.number_input(label, min_value=float(metric.minimum), max_value=float(metric.maximum),
                           value=round(float(start), decimals), step=float(metric.step),
                           format=f"%.{decimals}f", key=key, help=_help(metric))


def _glucose_mg_dl(metric: catalog.Metric, default: Any, key: str) -> float:
    factor = units.MGDL_PER_MMOL
    low, high = math.ceil(metric.minimum * factor), math.floor(metric.maximum * factor)
    start = round(units.glucose_from_mmol(_start_value(metric, default), units.MG_DL))
    typed = st.number_input(
        i18n.metric_label(metric.key, with_unit=True, unit=units.MG_DL),
        min_value=float(low), max_value=float(high),
        value=float(min(max(start, low), high)), step=1.0, format="%.0f",
        key=f"{key}_{units.MG_DL}", help=_help(metric))
    return round(units.glucose_to_mmol(typed, units.MG_DL), 2)


def _choice(metric: catalog.Metric, default: Any, key: str) -> int:
    options = list(metric.choices)
    current = int(_start_value(metric, default))
    return st.selectbox(
        i18n.input_label(metric.key), options,
        index=options.index(current) if current in options else 0,
        format_func=lambda code: t(f"option.{metric.key}.{code}"),
        key=key, help=_help(metric))


def _flag(metric: catalog.Metric, default: Any, key: str) -> int:
    healthy = int(metric.default)
    options = [healthy, *(code for code in metric.choices if code != healthy)]
    current = int(_start_value(metric, default))
    return st.radio(
        i18n.input_label(metric.key), options,
        index=options.index(current) if current in options else 0,
        format_func=lambda code: t(f"option.{metric.key}.{code}"),
        horizontal=True, key=key, help=_help(metric))
