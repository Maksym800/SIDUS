"""Owner: frontend developer (Streamlit)."""
from __future__ import annotations

from typing import Any, Mapping

from backend.diagnosis import service
from data import repository
from frontend import state


def save_entry(profile_id: int, values: Mapping[str, Any], source: str) -> int:
    environment = state.environment()
    entry_id = repository.add_entry(profile_id, values, environment, source=source)
    try:
        service.assess_latest(profile_id, environment)
    except service.EngineError:
        pass
    return entry_id


def current_profile() -> dict[str, Any] | None:
    profile_id = state.profile_id()
    return None if profile_id is None else repository.get_profile(profile_id)
