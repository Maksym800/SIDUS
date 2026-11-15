"""Owner: backend developer 2 (analytics; Pandas)."""
from __future__ import annotations

from typing import Callable

import pandas as pd

from data import catalog

_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def _times(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        frame[column] = pd.to_datetime(frame[column]).dt.strftime(_TIME_FORMAT)
    return frame


def metrics_table(entries: pd.DataFrame) -> pd.DataFrame:
    columns = ["recorded_at", "environment", "source", *catalog.KEYS]
    if entries.empty:
        return pd.DataFrame(columns=columns)
    return _times(entries[columns].copy(), ["recorded_at"]).reset_index(drop=True)


def diagnoses_table(runs: pd.DataFrame, findings: pd.DataFrame,
                    name_of: Callable[[str], str]) -> pd.DataFrame:
    columns = ["diagnosed_at", "entry_recorded_at", "environment", "flight_day",
               "overall_severity", "code", "diagnosis", "severity", "zone"]
    if runs.empty:
        return pd.DataFrame(columns=columns)
    merged = runs.merge(findings.rename(columns={"severity": "finding_severity"}),
                        left_on="id", right_on="run_id", how="left")
    merged["severity"] = merged["finding_severity"]
    merged["diagnosis"] = [name_of(code) if isinstance(code, str) else ""
                           for code in merged["code"]]
    merged = _times(merged, ["diagnosed_at", "entry_recorded_at"])
    return merged.sort_values(["diagnosed_at", "id"])[columns].reset_index(drop=True)


def to_csv(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8-sig")
