"""Owner: data engineer (Pandas + SQLite)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd

from data import catalog, db

_ENTRY_DATES = {"recorded_at": db.TIME_FORMAT}
_RUN_DATES = {"diagnosed_at": db.TIME_FORMAT}


def _now() -> datetime:
    return datetime.now().replace(microsecond=0)


def _stamp(moment: datetime | None) -> str:
    return (moment or _now()).strftime(db.TIME_FORMAT)


def _frame(sql: str, params: Sequence[Any] = (), dates: Mapping[str, str] | None = None) -> pd.DataFrame:
    with db.connect() as conn:
        return pd.read_sql_query(sql, conn, params=list(params),
                                 parse_dates=dict(dates) if dates else None)


def _plain(value: Any) -> Any:
    if value is None or value is pd.NaT:
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and value != value:
        return None
    return value


def _record(row: pd.Series) -> dict[str, Any]:
    record = {key: _plain(value) for key, value in row.items()}
    for key, value in record.items():
        metric = catalog.BY_KEY.get(key)
        if metric is not None and metric.integer and value is not None:
            record[key] = int(round(value))
    if "is_baseline" in record:
        record["is_baseline"] = bool(record["is_baseline"])
    return record


def _check_environment(environment: str) -> None:
    if environment not in catalog.ENVIRONMENTS:
        raise ValueError(f"unknown environment: {environment!r}")


def normalize_name(name: str) -> str:
    return " ".join(str(name).split())


def profile_name_exists(name: str) -> bool:
    wanted = normalize_name(name).casefold()
    names = _frame("SELECT name FROM profiles")["name"]
    return any(str(existing).casefold() == wanted for existing in names)


def create_profile(name: str, age: int, flight_start: date,
                   baseline: Mapping[str, Any],
                   created_at: datetime | None = None) -> int:
    name = normalize_name(name)
    if not name:
        raise ValueError("name is required")
    if profile_name_exists(name):
        raise ValueError(f"profile {name!r} already exists")
    values = catalog.clean_values(baseline)
    values["vision_clear"] = None
    stamp = _stamp(created_at)
    with db.connect() as conn:
        cursor = conn.execute(
            "INSERT INTO profiles (name, age, flight_start, created_at) VALUES (?, ?, ?, ?)",
            (name, int(age), flight_start.strftime(db.DATE_FORMAT), stamp),
        )
        profile_id = int(cursor.lastrowid)
        _insert_entry(conn, profile_id, values, catalog.BASELINE_ENVIRONMENT,
                      "baseline", stamp, is_baseline=True)
    return profile_id


def list_profiles() -> pd.DataFrame:
    frame = _frame(
        """
        SELECT p.id, p.name, p.age, p.flight_start, p.created_at,
               MAX(e.recorded_at) AS last_entry_at,
               COUNT(e.id)        AS entries
        FROM profiles p
        LEFT JOIN metric_entries e ON e.profile_id = p.id
        GROUP BY p.id
        """,
        dates={"flight_start": db.DATE_FORMAT, "created_at": db.TIME_FORMAT,
               "last_entry_at": db.TIME_FORMAT},
    )
    order = frame["name"].str.casefold().sort_values(kind="stable").index
    return frame.loc[order].reset_index(drop=True)


def get_profile(profile_id: int) -> dict[str, Any] | None:
    frame = _frame("SELECT * FROM profiles WHERE id = ?", (int(profile_id),),
                   dates={"flight_start": db.DATE_FORMAT, "created_at": db.TIME_FORMAT})
    if frame.empty:
        return None
    profile = _record(frame.iloc[0])
    profile["flight_start"] = profile["flight_start"].date()
    return profile


def _insert_entry(conn, profile_id: int, values: Mapping[str, Any], environment: str,
                  source: str, stamp: str, is_baseline: bool = False) -> int:
    columns = ["profile_id", "recorded_at", "is_baseline", "source", "environment",
               *catalog.KEYS]
    row = [profile_id, stamp, int(is_baseline), source, environment,
           *(values.get(key) for key in catalog.KEYS)]
    placeholders = ", ".join("?" for _ in columns)
    cursor = conn.execute(
        f"INSERT INTO metric_entries ({', '.join(columns)}) VALUES ({placeholders})", row
    )
    return int(cursor.lastrowid)


def add_entry(profile_id: int, values: Mapping[str, Any], environment: str,
              source: str = "manual", recorded_at: datetime | None = None) -> int:
    _check_environment(environment)
    if source not in catalog.SOURCES or source == "baseline":
        raise ValueError(f"unknown source: {source!r}")
    cleaned = catalog.clean_values(values)
    with db.connect() as conn:
        return _insert_entry(conn, int(profile_id), cleaned, environment, source,
                             _stamp(recorded_at))


def get_entries(profile_id: int, start: datetime | None = None,
                end: datetime | None = None) -> pd.DataFrame:
    sql = "SELECT * FROM metric_entries WHERE profile_id = ?"
    params: list[Any] = [int(profile_id)]
    if start is not None:
        sql += " AND recorded_at >= ?"
        params.append(start.strftime(db.TIME_FORMAT))
    if end is not None:
        sql += " AND recorded_at < ?"
        params.append(end.strftime(db.TIME_FORMAT))
    return _frame(sql + " ORDER BY recorded_at, id", params, dates=_ENTRY_DATES)


def _one_entry(sql: str, params: Sequence[Any]) -> dict[str, Any] | None:
    frame = _frame(sql, params, dates=_ENTRY_DATES)
    return None if frame.empty else _record(frame.iloc[0])


def get_entry(entry_id: int) -> dict[str, Any] | None:
    return _one_entry("SELECT * FROM metric_entries WHERE id = ?", (int(entry_id),))


def get_latest_entry(profile_id: int) -> dict[str, Any] | None:
    return _one_entry(
        "SELECT * FROM metric_entries WHERE profile_id = ? "
        "ORDER BY recorded_at DESC, id DESC LIMIT 1", (int(profile_id),))


def get_baseline(profile_id: int) -> dict[str, Any] | None:
    return _one_entry(
        "SELECT * FROM metric_entries WHERE profile_id = ? AND is_baseline = 1 "
        "ORDER BY id LIMIT 1", (int(profile_id),))


def get_previous_entry(entry: Mapping[str, Any]) -> dict[str, Any] | None:
    stamp = entry["recorded_at"].strftime(db.TIME_FORMAT)
    return _one_entry(
        "SELECT * FROM metric_entries WHERE profile_id = ? "
        "AND (recorded_at < ? OR (recorded_at = ? AND id < ?)) "
        "ORDER BY recorded_at DESC, id DESC LIMIT 1",
        (int(entry["profile_id"]), stamp, stamp, int(entry["id"])))


def entry_values(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {key: entry.get(key) for key in catalog.KEYS}


def save_diagnosis(entry_id: int, profile_id: int, environment: str, flight_day: int,
                   findings: Iterable[tuple[str, int, str]],
                   diagnosed_at: datetime | None = None) -> int:
    _check_environment(environment)
    rows = [(str(code), int(severity), str(zone)) for code, severity, zone in findings]
    overall = max((severity for _, severity, _ in rows), default=0)
    with db.connect() as conn:
        cursor = conn.execute(
            "INSERT INTO diagnosis_runs (entry_id, profile_id, environment, flight_day, "
            "overall_severity, diagnosed_at) VALUES (?, ?, ?, ?, ?, ?)",
            (int(entry_id), int(profile_id), environment, int(flight_day), overall,
             _stamp(diagnosed_at)),
        )
        run_id = int(cursor.lastrowid)
        conn.executemany(
            "INSERT INTO diagnosis_findings (run_id, code, severity, zone) VALUES (?, ?, ?, ?)",
            [(run_id, *row) for row in rows],
        )
    return run_id


def get_findings(run_ids: Iterable[int]) -> pd.DataFrame:
    ids = [int(run_id) for run_id in run_ids]
    if not ids:
        return pd.DataFrame(columns=["run_id", "code", "severity", "zone"])
    marks = ", ".join("?" for _ in ids)
    return _frame(
        f"SELECT run_id, code, severity, zone FROM diagnosis_findings "
        f"WHERE run_id IN ({marks}) ORDER BY run_id, severity DESC, id", ids)


def get_latest_run(entry_id: int, environment: str) -> dict[str, Any] | None:
    frame = _frame(
        "SELECT * FROM diagnosis_runs WHERE entry_id = ? AND environment = ? "
        "ORDER BY diagnosed_at DESC, id DESC LIMIT 1",
        (int(entry_id), environment), dates=_RUN_DATES)
    if frame.empty:
        return None
    run = _record(frame.iloc[0])
    run["findings"] = [_record(row) for _, row in get_findings([run["id"]]).iterrows()]
    return run


def get_runs(profile_id: int, start: datetime | None = None,
             end: datetime | None = None) -> pd.DataFrame:
    sql = ("SELECT r.*, e.recorded_at AS entry_recorded_at FROM diagnosis_runs r "
           "JOIN metric_entries e ON e.id = r.entry_id WHERE r.profile_id = ?")
    params: list[Any] = [int(profile_id)]
    if start is not None:
        sql += " AND e.recorded_at >= ?"
        params.append(start.strftime(db.TIME_FORMAT))
    if end is not None:
        sql += " AND e.recorded_at < ?"
        params.append(end.strftime(db.TIME_FORMAT))
    return _frame(sql + " ORDER BY r.diagnosed_at, r.id", params,
                  dates={**_RUN_DATES, "entry_recorded_at": db.TIME_FORMAT})


WORKOUT_DONE = "done"
WORKOUT_NOT_SCHEDULED = "not_scheduled"


def set_workout(profile_id: int, day: date, status: str,
                recorded_at: datetime | None = None) -> None:
    if status not in (WORKOUT_DONE, WORKOUT_NOT_SCHEDULED):
        raise ValueError(f"unknown workout status: {status!r}")
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO workouts (profile_id, day, status, recorded_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT (profile_id, day) DO UPDATE SET "
            "status = excluded.status, recorded_at = excluded.recorded_at",
            (int(profile_id), day.strftime(db.DATE_FORMAT), status, _stamp(recorded_at)),
        )


def clear_workout(profile_id: int, day: date) -> None:
    with db.connect() as conn:
        conn.execute("DELETE FROM workouts WHERE profile_id = ? AND day = ?",
                     (int(profile_id), day.strftime(db.DATE_FORMAT)))


def get_workouts(profile_id: int, start: date | None = None,
                 end: date | None = None) -> pd.DataFrame:
    sql = "SELECT * FROM workouts WHERE profile_id = ?"
    params: list[Any] = [int(profile_id)]
    if start is not None:
        sql += " AND day >= ?"
        params.append(start.strftime(db.DATE_FORMAT))
    if end is not None:
        sql += " AND day < ?"
        params.append(end.strftime(db.DATE_FORMAT))
    return _frame(sql + " ORDER BY day", params,
                  dates={"day": db.DATE_FORMAT, "recorded_at": db.TIME_FORMAT})


def get_workout_status(profile_id: int, day: date) -> str | None:
    frame = _frame("SELECT status FROM workouts WHERE profile_id = ? AND day = ?",
                   (int(profile_id), day.strftime(db.DATE_FORMAT)))
    return None if frame.empty else str(frame.iloc[0]["status"])


def get_setting(key: str, default: str | None = None) -> str | None:
    frame = _frame("SELECT value FROM settings WHERE key = ?", (key,))
    return default if frame.empty else str(frame.iloc[0]["value"])


def set_setting(key: str, value: str) -> None:
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
