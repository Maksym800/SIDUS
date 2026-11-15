"""Owner: backend developer 2 (analytics)."""
from __future__ import annotations

MGDL_PER_MMOL = 18.016

MMOL_L = "mmol_l"
MG_DL = "mg_dl"
GLUCOSE_UNITS = (MMOL_L, MG_DL)


def glucose_from_mmol(value: float, unit: str) -> float:
    return value * MGDL_PER_MMOL if unit == MG_DL else value


def glucose_to_mmol(value: float, unit: str) -> float:
    return value / MGDL_PER_MMOL if unit == MG_DL else value
