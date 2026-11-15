"""Owner: backend developer 2 (analytics)."""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

STALE_AFTER = timedelta(hours=24)


def hours_since(moment: datetime | None, now: datetime | None = None) -> float | None:
    if moment is None or pd.isna(moment):
        return None
    return (pd.Timestamp(now or datetime.now()) - pd.Timestamp(moment)).total_seconds() / 3600


def is_stale(last_entry_at: datetime | None, now: datetime | None = None) -> bool:
    age = hours_since(last_entry_at, now)
    return age is None or age > STALE_AFTER.total_seconds() / 3600


def with_freshness(profiles: pd.DataFrame, now: datetime | None = None) -> pd.DataFrame:
    frame = profiles.copy()
    last = pd.to_datetime(frame["last_entry_at"])
    age = pd.Timestamp(now or datetime.now()) - last
    frame["hours_since_update"] = age.dt.total_seconds() / 3600
    limit = STALE_AFTER.total_seconds() / 3600
    frame["is_stale"] = frame["hours_since_update"].isna() | (frame["hours_since_update"] > limit)
    return frame
