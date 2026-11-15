"""Owner: backend developer 2 (analytics; Pandas)."""
from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Any

import pandas as pd

_MONDAY_FIRST = calendar.Calendar(firstweekday=0)


def month_grid(year: int, month: int) -> list[list[int]]:
    return _MONDAY_FIRST.monthdayscalendar(year, month)


def shift_month(year: int, month: int, step: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + step
    return index // 12, index % 12 + 1


def month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
    next_year, next_month = shift_month(year, month, 1)
    return datetime(year, month, 1), datetime(next_year, next_month, 1)


def latest_runs(runs: pd.DataFrame) -> pd.DataFrame:
    if runs.empty:
        return runs
    return (runs.sort_values(["diagnosed_at", "id"])
                .drop_duplicates("entry_id", keep="last"))


def day_summary(entries: pd.DataFrame, runs: pd.DataFrame) -> dict[int, dict[str, Any]]:
    if entries.empty:
        return {}
    daily = entries[["id", "recorded_at"]].assign(day=entries["recorded_at"].dt.day)
    last = latest_runs(runs)
    if last.empty:
        daily = daily.assign(overall_severity=float("nan"))
    else:
        daily = daily.merge(last[["entry_id", "overall_severity"]],
                            left_on="id", right_on="entry_id", how="left")
    grouped = daily.groupby("day").agg(entries=("id", "count"),
                                       severity=("overall_severity", "max"))
    return {
        int(day): {"entries": int(row.entries),
                   "severity": None if pd.isna(row.severity) else int(row.severity)}
        for day, row in grouped.iterrows()
    }


def entries_on(entries: pd.DataFrame, day: date) -> pd.DataFrame:
    if entries.empty:
        return entries
    return entries[entries["recorded_at"].dt.date == day].sort_values(["recorded_at", "id"])


def runs_by_entry(runs: pd.DataFrame, findings: pd.DataFrame) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    if runs.empty:
        return grouped
    by_run: dict[int, list[dict[str, Any]]] = {}
    for row in findings.itertuples(index=False):
        by_run.setdefault(int(row.run_id), []).append(
            {"code": str(row.code), "severity": int(row.severity), "zone": str(row.zone)})
    for row in runs.sort_values(["diagnosed_at", "id"]).itertuples(index=False):
        grouped.setdefault(int(row.entry_id), []).append({
            "id": int(row.id),
            "environment": str(row.environment),
            "diagnosed_at": row.diagnosed_at.to_pydatetime(),
            "flight_day": int(row.flight_day),
            "overall_severity": int(row.overall_severity),
            "findings": by_run.get(int(row.id), []),
        })
    return grouped
