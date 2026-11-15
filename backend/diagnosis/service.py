from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping

from backend.analytics import flight
from backend.diagnosis import engine
from backend.diagnosis.engine import EngineError, Finding
from data import repository

__all__ = ["Assessment", "EngineError", "Finding", "assess_entry", "assess_latest",
           "zone_levels"]


@dataclass(frozen=True)
class Assessment:

    entry: Mapping[str, Any]
    baseline: Mapping[str, Any]
    run_id: int
    environment: str
    flight_day: int
    diagnosed_at: datetime
    findings: tuple[Finding, ...]

    @property
    def overall(self) -> int:
        return max((finding.severity for finding in self.findings), default=engine.OK)

    def zone_levels(self) -> dict[str, int]:
        return zone_levels(self.findings)


def zone_levels(findings: Iterable[Finding]) -> dict[str, int]:
    levels: dict[str, int] = {}
    for finding in findings:
        levels[finding.zone] = max(levels.get(finding.zone, engine.OK), finding.severity)
    return levels


def assess_entry(profile: Mapping[str, Any], entry: Mapping[str, Any],
                 baseline: Mapping[str, Any], environment: str) -> Assessment:
    run = repository.get_latest_run(entry["id"], environment)
    if run is None:
        day = max(flight.flight_day(profile["flight_start"], entry["recorded_at"].date()), 0)
        found = engine.evaluate(repository.entry_values(entry),
                                repository.entry_values(baseline), environment, day)
        repository.save_diagnosis(
            entry["id"], profile["id"], environment, day,
            [(finding.code, finding.severity, finding.zone) for finding in found],
        )
        run = repository.get_latest_run(entry["id"], environment)
    findings = tuple(Finding(row["code"], int(row["severity"]), row["zone"])
                     for row in run["findings"])
    return Assessment(entry=entry, baseline=baseline, run_id=run["id"],
                      environment=environment, flight_day=run["flight_day"],
                      diagnosed_at=run["diagnosed_at"], findings=findings)


def assess_latest(profile_id: int, environment: str) -> Assessment | None:
    profile = repository.get_profile(profile_id)
    if profile is None:
        return None
    entry = repository.get_latest_entry(profile_id)
    baseline = repository.get_baseline(profile_id)
    if entry is None or baseline is None:
        return None
    return assess_entry(profile, entry, baseline, environment)
