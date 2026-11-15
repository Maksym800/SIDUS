from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from data import catalog

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "astro_health.db"

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


def db_path() -> Path:
    return Path(os.environ.get("ASTRO_HEALTH_DB") or DEFAULT_DB_PATH)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _metric_columns_sql() -> str:
    return ",\n".join(f"    {m.key} {m.sql_type}" for m in catalog.METRICS)


def _schema_sql() -> str:
    environments = ", ".join(f"'{e}'" for e in catalog.ENVIRONMENTS)
    sources = ", ".join(f"'{s}'" for s in catalog.SOURCES)
    return f"""
CREATE TABLE IF NOT EXISTS profiles (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL UNIQUE,
    age           INTEGER NOT NULL CHECK (age BETWEEN 18 AND 90),
    flight_start  TEXT    NOT NULL,              -- YYYY-MM-DD
    created_at    TEXT    NOT NULL               -- YYYY-MM-DD HH:MM:SS
);

-- One row per saved set of metrics. Rows are never updated: editing the
-- metrics adds a new row, so the full history stays available.
CREATE TABLE IF NOT EXISTS metric_entries (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id    INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    recorded_at   TEXT    NOT NULL,              -- when the metrics were entered
    is_baseline   INTEGER NOT NULL DEFAULT 0 CHECK (is_baseline IN (0, 1)),
    source        TEXT    NOT NULL DEFAULT 'manual' CHECK (source IN ({sources})),
    environment   TEXT    NOT NULL CHECK (environment IN ({environments})),
{_metric_columns_sql()}
);
CREATE INDEX IF NOT EXISTS idx_entries_profile_time
    ON metric_entries (profile_id, recorded_at);

-- One row per run of the diagnosis engine over an entry.
CREATE TABLE IF NOT EXISTS diagnosis_runs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id          INTEGER NOT NULL REFERENCES metric_entries(id) ON DELETE CASCADE,
    profile_id        INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    environment       TEXT    NOT NULL CHECK (environment IN ({environments})),
    flight_day        INTEGER NOT NULL,
    overall_severity  INTEGER NOT NULL CHECK (overall_severity IN (0, 1, 2)),
    diagnosed_at      TEXT    NOT NULL           -- when the diagnosis was determined
);
CREATE INDEX IF NOT EXISTS idx_runs_entry ON diagnosis_runs (entry_id, environment);

-- The suspected conditions found by one run (no rows = nothing suspected).
CREATE TABLE IF NOT EXISTS diagnosis_findings (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id    INTEGER NOT NULL REFERENCES diagnosis_runs(id) ON DELETE CASCADE,
    code      TEXT    NOT NULL,
    severity  INTEGER NOT NULL CHECK (severity IN (1, 2)),
    zone      TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_findings_run ON diagnosis_findings (run_id);

CREATE TABLE IF NOT EXISTS workouts (
    profile_id   INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    day          TEXT    NOT NULL,               -- YYYY-MM-DD
    status       TEXT    NOT NULL CHECK (status IN ('done', 'not_scheduled')),
    recorded_at  TEXT    NOT NULL,
    PRIMARY KEY (profile_id, day)
);

CREATE TABLE IF NOT EXISTS settings (
    key    TEXT PRIMARY KEY,
    value  TEXT NOT NULL
);
"""


def _add_missing_metric_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(metric_entries)")}
    for metric in catalog.METRICS:
        if metric.key not in existing:
            conn.execute(
                f"ALTER TABLE metric_entries ADD COLUMN {metric.key} {metric.sql_type}"
            )


def init_db() -> None:
    db_path().parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(_schema_sql())
        _add_missing_metric_columns(conn)
