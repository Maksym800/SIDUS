from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

NUMBER = "number"
CHOICE = "choice"
FLAG = "flag"
SCORE = "score"

ENVIRONMENTS = ("earth", "mars", "moon", "deep_space", "orbit")
BASELINE_ENVIRONMENT = "earth"

SOURCES = ("baseline", "manual", "game")


@dataclass(frozen=True)
class Metric:

    key: str
    kind: str
    group: str
    unit: str = ""
    minimum: float = 0.0
    maximum: float = 0.0
    step: float = 1.0
    default: float = 0.0
    integer: bool = False
    in_baseline: bool = True
    choices: tuple = ()

    @property
    def sql_type(self) -> str:
        return "INTEGER" if self.integer else "REAL"


def _number(key, group, unit, minimum, maximum, step, default, integer=False):
    return Metric(key, NUMBER, group, unit, minimum, maximum, step, default, integer)


def _choice(key, group, default=0, choices=(0, 1, 2), in_baseline=True, kind=CHOICE):
    return Metric(key, kind, group, "", min(choices), max(choices), 1, default,
                  True, in_baseline, tuple(choices))


def _score(key, group, default):
    return Metric(key, SCORE, group, "points", 1, 10, 1, default, True)


METRICS: tuple[Metric, ...] = (
    _number("mass_kg", "body", "kg", 35, 200, 0.1, 75.0),
    _number("heart_rate_bpm", "cardio", "bpm", 25, 230, 1, 62, integer=True),
    _number("bp_systolic", "cardio", "mmhg", 60, 260, 1, 118, integer=True),
    _number("bp_diastolic", "cardio", "mmhg", 30, 160, 1, 76, integer=True),
    _choice("ecg_rhythm", "cardio"),
    _number("hrv_rmssd_ms", "cardio", "ms", 1, 300, 1, 48, integer=True),
    _number("blood_flow_cm_s", "cardio", "cm_s", 0, 150, 0.5, 25.0),
    _choice("vascular_condition", "cardio"),
    _choice("vision_clear", "vision", default=1, choices=(0, 1), in_baseline=False, kind=FLAG),
    _number("sleep_hours", "sleep", "h", 0, 16, 0.5, 7.5),
    _number("sleep_efficiency_pct", "sleep", "pct", 0, 100, 1, 90, integer=True),
    _number("muscle_thickness_mm", "muscle", "mm", 5, 120, 0.5, 42.0),
    _choice("muscle_structure", "muscle"),
    _number("body_temp_c", "vitals", "celsius", 32, 43, 0.1, 36.6),
    _number("spo2_pct", "vitals", "pct", 50, 100, 1, 98, integer=True),
    _number("coordination_pct", "neuro", "pct", 0, 100, 1, 70, integer=True),
    _number("glucose_mmol_l", "blood", "mmol_l", 1, 35, 0.1, 5.0),
    _number("cortisol_nmol_l", "blood", "nmol_l", 10, 2000, 5, 350, integer=True),
    _choice("viral_activation", "blood", default=0, choices=(0, 1), kind=FLAG),
    _number("calcium_mmol_l", "blood", "mmol_l", 1, 4, 0.01, 2.35),
    _number("bone_resorption_ntx", "blood", "ntx", 1, 500, 1, 40, integer=True),
    _score("mood_score", "psych", 8),
    _score("stress_score", "psych", 3),
    _number("radiation_total_msv", "radiation", "msv", 0, 5000, 0.1, 5.0),
    _number("neutron_rate_usv_h", "radiation", "usv_h", 0, 1000, 0.01, 0.01),
)

BY_KEY: dict[str, Metric] = {metric.key: metric for metric in METRICS}
KEYS: tuple[str, ...] = tuple(BY_KEY)
BASELINE_KEYS: tuple[str, ...] = tuple(m.key for m in METRICS if m.in_baseline)
NUMERIC_KEYS: tuple[str, ...] = tuple(m.key for m in METRICS if m.kind in (NUMBER, SCORE))
GROUPS: tuple[str, ...] = tuple(dict.fromkeys(m.group for m in METRICS))


def metrics_in_group(group: str, baseline_only: bool = False) -> list[Metric]:
    return [m for m in METRICS
            if m.group == group and (m.in_baseline or not baseline_only)]


def default_values(baseline_only: bool = True) -> dict[str, float]:
    return {m.key: m.default for m in METRICS if m.in_baseline or not baseline_only}


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return math.isnan(float(value))
    except (TypeError, ValueError):
        return False


def clean_values(values: Mapping[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for metric in METRICS:
        raw = values.get(metric.key)
        if is_missing(raw):
            if metric.in_baseline:
                raise ValueError(f"{metric.key}: value is required")
            cleaned[metric.key] = None
            continue
        try:
            number = float(raw)
        except (TypeError, ValueError):
            raise ValueError(f"{metric.key}: {raw!r} is not a number") from None
        if metric.choices:
            if number not in metric.choices:
                raise ValueError(f"{metric.key}: {raw!r} is not one of {metric.choices}")
        elif not metric.minimum <= number <= metric.maximum:
            raise ValueError(
                f"{metric.key}: {number:g} is outside {metric.minimum:g}-{metric.maximum:g}"
            )
        cleaned[metric.key] = int(round(number)) if metric.integer else number
    return cleaned
