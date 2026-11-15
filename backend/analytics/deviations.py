
from __future__ import annotations

import statistics
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from data import catalog

TREND_WINDOW = 7
TREND_THRESHOLD = 0.02
TREND_NOISE_FACTOR = 3

UP, DOWN, FLAT, UNKNOWN = "up", "down", "flat", ""


def _clean(values: Iterable[Any]) -> list[float]:
    return [float(value) for value in values if not catalog.is_missing(value)]


def trend(values: Sequence[Any]) -> str:
    points = np.asarray(_clean(values), dtype=np.float64)
    if points.size < 3:
        return UNKNOWN
    steps = np.arange(points.size)
    slope, start = np.polyfit(steps, points, 1)
    drift = slope * (points.size - 1)
    scatter = statistics.pstdev((points - (slope * steps + start)).tolist())
    scale = abs(statistics.fmean(points.tolist())) or 1.0
    if abs(drift) < TREND_THRESHOLD * scale or abs(drift) < TREND_NOISE_FACTOR * scatter:
        return FLAT
    return UP if drift > 0 else DOWN


def zscore(value: Any, earlier: Sequence[Any]) -> float | None:
    history = _clean(earlier)
    if catalog.is_missing(value) or len(history) < 3:
        return None
    spread = statistics.stdev(history)
    if spread == 0:
        return None
    return (float(value) - statistics.fmean(history)) / spread


def comparison_table(current: Mapping[str, Any], baseline: Mapping[str, Any],
                     history: pd.DataFrame | None = None,
                     keys: Sequence[str] = catalog.NUMERIC_KEYS) -> pd.DataFrame:
    rows = []
    for key in keys:
        now, norm = current.get(key), baseline.get(key)
        known = not catalog.is_missing(now) and not catalog.is_missing(norm)
        change = float(now) - float(norm) if known else np.nan
        recent = _clean(history[key].tail(TREND_WINDOW)) if history is not None and key in history else []
        rows.append({
            "metric": key,
            "current": np.nan if catalog.is_missing(now) else float(now),
            "baseline": np.nan if catalog.is_missing(norm) else float(norm),
            "change": change,
            "change_pct": change / float(norm) * 100 if known and float(norm) != 0 else np.nan,
            "recent": statistics.median(recent) if recent else np.nan,
            "trend": trend(recent),
        })
    return pd.DataFrame(rows, columns=["metric", "current", "baseline", "change",
                                       "change_pct", "recent", "trend"])


def changed_keys(entry: Mapping[str, Any], previous: Mapping[str, Any] | None) -> set[str]:
    if previous is None:
        return set()
    changed = set()
    for key in catalog.KEYS:
        new, old = entry.get(key), previous.get(key)
        if catalog.is_missing(new) and catalog.is_missing(old):
            continue
        if catalog.is_missing(new) or catalog.is_missing(old) or float(new) != float(old):
            changed.add(key)
    return changed
