from __future__ import annotations

import random
from datetime import datetime, timedelta

import pandas as pd

from data import catalog, db, repository

ENVIRONMENT = "orbit"


def _baseline(**changes) -> dict:
    return {**catalog.default_values(), **changes}


def _drift(start: float, end: float, share: float, noise: float, rng: random.Random) -> float:
    return start + (end - start) * share + rng.uniform(-noise, noise)


def _entry(baseline: dict, share: float, targets: dict, rng: random.Random) -> dict:
    values = dict(baseline)
    values.update({
        "vision_clear": 1,
        "heart_rate_bpm": baseline["heart_rate_bpm"] + rng.randint(-3, 4),
        "bp_systolic": baseline["bp_systolic"] + rng.randint(-4, 4),
        "bp_diastolic": baseline["bp_diastolic"] + rng.randint(-3, 3),
        "hrv_rmssd_ms": baseline["hrv_rmssd_ms"] + rng.randint(-4, 4),
        "sleep_hours": rng.choice((6.5, 7.0, 7.0, 7.5, 7.5, 8.0)),
        "sleep_efficiency_pct": rng.randint(86, 93),
        "body_temp_c": round(baseline["body_temp_c"] + rng.uniform(-0.2, 0.2), 1),
        "spo2_pct": rng.randint(97, 99),
        "coordination_pct": baseline["coordination_pct"] + rng.randint(-5, 5),
        "glucose_mmol_l": round(baseline["glucose_mmol_l"] + rng.uniform(-0.4, 0.5), 1),
        "cortisol_nmol_l": baseline["cortisol_nmol_l"] + 5 * rng.randint(-8, 8),
        "mood_score": rng.choice((7, 8, 8, 9)),
        "stress_score": rng.choice((2, 3, 3, 4)),
    })
    for key, (end, noise) in targets.items():
        metric = catalog.BY_KEY[key]
        value = _drift(baseline[key], end, share, noise, rng)
        value = min(max(value, metric.minimum), metric.maximum)
        values[key] = round(value) if metric.integer else round(value, 2)
    return values


CREW = (
    ("Olena Marchenko (demo)", 34, 46, 0,
     _baseline(mass_kg=62.0, heart_rate_bpm=58, muscle_thickness_mm=38.0, coordination_pct=74),
     {"muscle_thickness_mm": (34.6, 0.2), "bone_resorption_ntx": (55, 1.5), "mass_kg": (60.6, 0.2),
      "radiation_total_msv": (5.0 + 46 * 0.6, 0.3), "neutron_rate_usv_h": (4.5, 1.0)},
     {}),
    ("Taras Bondar (demo)", 41, 12, 3,
     _baseline(mass_kg=84.0, heart_rate_bpm=66, bp_systolic=124, bp_diastolic=80,
               radiation_total_msv=38.0, coordination_pct=66),
     {"radiation_total_msv": (38.0 + 12 * 0.6, 0.2), "neutron_rate_usv_h": (4.0, 1.0)},
     {}),
    ("Iryna Savchuk (demo)", 38, 80, 0,
     _baseline(mass_kg=68.0, heart_rate_bpm=60, hrv_rmssd_ms=55, coordination_pct=78),
     {"muscle_thickness_mm": (37.5, 0.2), "bone_resorption_ntx": (58, 1.5),
      "blood_flow_cm_s": (16.0, 0.6), "cortisol_nmol_l": (520, 15),
      "radiation_total_msv": (5.0 + 80 * 0.62, 0.3), "neutron_rate_usv_h": (5.0, 1.0)},
     {"heart_rate_bpm": 132, "body_temp_c": 38.6, "viral_activation": 1, "vision_clear": 0,
      "vascular_condition": 1, "sleep_hours": 4.5, "sleep_efficiency_pct": 72,
      "mood_score": 4, "stress_score": 8, "hrv_rmssd_ms": 31}),
)


def _diagnose(profile: dict, baseline: dict, entry: dict) -> bool:
    try:
        from backend.analytics import flight
        from backend.diagnosis import engine
        day = max(flight.flight_day(profile["flight_start"], entry["recorded_at"].date()), 0)
        environment = entry["environment"]
        found = engine.evaluate(repository.entry_values(entry), repository.entry_values(baseline),
                                environment, day)
    except Exception as error:
        print(f"  diagnosis skipped: {error}")
        return False
    repository.save_diagnosis(entry["id"], profile["id"], environment, day,
                              [(f.code, f.severity, f.zone) for f in found],
                              diagnosed_at=entry["recorded_at"])
    return True


def _seed_one(name, age, flight_days, quiet_days, baseline, targets, last_day, now) -> None:
    if repository.profile_name_exists(name):
        print(f"{name}: already there, skipped")
        return
    rng = random.Random(name)
    launch = (now - timedelta(days=flight_days - 1)).date()
    created = datetime.combine(launch - timedelta(days=14), datetime.min.time()) + timedelta(hours=10)
    profile_id = repository.create_profile(name, age, launch, baseline, created_at=created)
    profile = repository.get_profile(profile_id)
    stored_baseline = repository.get_baseline(profile_id)
    can_diagnose = _diagnose(profile, stored_baseline, stored_baseline)

    last_entry_day = now.date() - timedelta(days=quiet_days)
    days = pd.date_range(launch + timedelta(days=1), last_entry_day, freq="2D").date.tolist()
    if not days or days[-1] != last_entry_day:
        days.append(last_entry_day)
    for index, day in enumerate(days):
        share = (index + 1) / len(days)
        values = _entry(baseline, share, targets, rng)
        moment = datetime.combine(day, datetime.min.time()) + timedelta(
            hours=rng.randint(7, 9), minutes=rng.randint(0, 59))
        if day == last_entry_day:
            values.update(last_day)
            moment = min(moment, now - timedelta(minutes=5))
        entry_id = repository.add_entry(profile_id, values, ENVIRONMENT, recorded_at=moment)
        if can_diagnose:
            _diagnose(profile, stored_baseline, repository.get_entry(entry_id))

    for offset in range(flight_days):
        day = launch + timedelta(days=offset)
        if day >= now.date() or day > last_entry_day:
            break
        status = (repository.WORKOUT_NOT_SCHEDULED if day.weekday() == 6
                  else repository.WORKOUT_DONE if rng.random() < 0.85 else None)
        if status:
            repository.set_workout(profile_id, day, status, recorded_at=datetime.combine(
                day, datetime.min.time()) + timedelta(hours=18))
    print(f"{name}: {len(days)} entries from {days[0]} to {days[-1]}")


def main() -> None:
    db.init_db()
    now = datetime.now().replace(microsecond=0)
    for member in CREW:
        _seed_one(*member, now)
    if repository.get_setting("environment") is None:
        repository.set_setting("environment", ENVIRONMENT)
        print(f"Mission environment set to {ENVIRONMENT}.")
    print(f"Database: {db.db_path()}")


if __name__ == "__main__":
    main()
