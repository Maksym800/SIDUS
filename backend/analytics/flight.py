"""Owner: backend developer 2 (analytics)."""
from __future__ import annotations

from datetime import date

PREFLIGHT = "preflight"
ADAPTATION = "adaptation"
MAIN = "main"
LONG_DURATION = "long_duration"

STAGE_LIMITS = ((ADAPTATION, 14), (MAIN, 150))


def flight_day(flight_start: date, on: date) -> int:
    return (on - flight_start).days + 1


def days_to_launch(flight_start: date, on: date) -> int:
    return max((flight_start - on).days, 0)


def flight_stage(day: int) -> str:
    if day < 1:
        return PREFLIGHT
    for stage, last_day in STAGE_LIMITS:
        if day <= last_day:
            return stage
    return LONG_DURATION
