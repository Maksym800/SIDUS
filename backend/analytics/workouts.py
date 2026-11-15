"""Owner: backend developer 2 (analytics; NumPy + Statistics + Pandas)."""
from __future__ import annotations

import statistics
from datetime import date

import numpy as np
import pandas as pd

from data.repository import WORKOUT_DONE as DONE
from data.repository import WORKOUT_NOT_SCHEDULED as NOT_SCHEDULED

__all__ = ["DONE", "NOT_SCHEDULED", "needs_reminder", "month_marks", "done_in_month",
           "weekly_average"]


def needs_reminder(status_today: str | None) -> bool:
    return status_today is None


def month_marks(workouts: pd.DataFrame, year: int, month: int) -> dict[int, str]:
    if workouts.empty:
        return {}
    days = workouts["day"]
    in_month = workouts[(days.dt.year == year) & (days.dt.month == month)]
    return {int(day): str(status)
            for day, status in zip(in_month["day"].dt.day, in_month["status"])}


def done_in_month(workouts: pd.DataFrame, year: int, month: int) -> int:
    return sum(1 for status in month_marks(workouts, year, month).values() if status == DONE)


def weekly_average(workouts: pd.DataFrame, today: date, weeks: int = 4) -> float:
    if workouts.empty or weeks < 1:
        return 0.0
    done_days = workouts.loc[workouts["status"] == DONE, "day"]
    days_ago = (pd.Timestamp(today) - done_days).dt.days.to_numpy()
    days_ago = days_ago[(days_ago >= 0) & (days_ago < 7 * weeks)]
    per_week = np.bincount(days_ago // 7, minlength=weeks)[:weeks]
    return float(statistics.fmean(per_week.tolist()))
