
from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

MAX_SAMPLES = 20_000


@dataclass(frozen=True)
class GameResult:
    score_pct: int
    on_target_s: float
    total_s: float
    longest_hold_s: float
    median_distance_px: float | None


def on_target(distances: Sequence[float], radius_px: float) -> np.ndarray:
    samples = np.asarray(distances, dtype=np.float64)
    return (samples >= 0) & (samples <= radius_px)


def score(distances: Sequence[float], radius_px: float) -> float:
    hits = on_target(distances, radius_px)
    return float(hits.mean() * 100) if hits.size else 0.0


def longest_run(hits: np.ndarray) -> int:
    if not hits.any():
        return 0
    edges = np.diff(np.concatenate(([0], hits.astype(np.int8), [0])))
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1)
    return int((ends - starts).max())


def summarize(payload: Mapping[str, Any]) -> GameResult:
    try:
        distances = np.asarray(payload["distances"], dtype=np.float64)
        radius = float(payload["radius_px"])
        interval_s = float(payload["interval_ms"]) / 1000
    except (KeyError, TypeError, ValueError):
        raise ValueError("malformed coordination test result") from None
    if distances.ndim != 1 or not 0 < distances.size <= MAX_SAMPLES:
        raise ValueError("coordination test result has no usable samples")
    if not np.isfinite(distances).all() or radius <= 0 or interval_s <= 0:
        raise ValueError("coordination test result contains invalid numbers")

    hits = on_target(distances, radius)
    inside_field = distances[distances >= 0]
    return GameResult(
        score_pct=int(round(score(distances, radius))),
        on_target_s=round(float(hits.sum()) * interval_s, 1),
        total_s=round(distances.size * interval_s, 1),
        longest_hold_s=round(longest_run(hits) * interval_s, 1),
        median_distance_px=(round(statistics.median(inside_field.tolist()), 1)
                            if inside_field.size else None),
    )


@dataclass(frozen=True)
class Progress:
    series: pd.DataFrame
    best: int
    latest: int
    mean_first: float
    mean_last: float
    change: float


def progress(entries: pd.DataFrame, window: int = 3) -> Progress | None:
    if entries.empty or "source" not in entries:
        return None
    tests = entries[(entries["source"] == "game") & entries["coordination_pct"].notna()]
    if tests.empty:
        return None
    scores = tests.set_index("recorded_at")["coordination_pct"].astype(float)
    series = pd.DataFrame({
        "score": scores,
        "average": scores.rolling(window, min_periods=1).mean(),
    })
    values = scores.to_numpy()
    first, last = values[:window], values[-window:]
    return Progress(series=series, best=int(round(values.max())), latest=int(round(values[-1])),
                    mean_first=round(statistics.fmean(first.tolist()), 1),
                    mean_last=round(statistics.fmean(last.tolist()), 1),
                    change=round(statistics.fmean(last.tolist())
                                 - statistics.fmean(first.tolist()), 1))
