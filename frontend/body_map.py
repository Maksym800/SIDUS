"""Owner: frontend developer (Streamlit)."""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Mapping

import streamlit as st

from frontend import ui
from frontend.i18n import t

ASSETS = Path(__file__).resolve().parent.parent / "assets"

IMAGE_CANDIDATES = ("anatomy.png", "anatomy.jpg", "anatomy.jpeg", "anatomy.webp",
                    "anatomy.svg")
_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
         ".webp": "image/webp", ".svg": "image/svg+xml"}

ZONE_LAYOUT: dict[str, dict] = {
    "head":       {"points": [(49.8, 4.4)], "size": 7.0},
    "eyes":       {"points": [(45.4, 8.0), (54.4, 8.0)], "size": 4.4},
    "neck":       {"points": [(50.2, 16.0)], "size": 6.0},
    "lungs":      {"points": [(39.8, 26.3), (61.6, 26.2)], "size": 8.0},
    "heart":      {"points": [(52.6, 28.4)], "size": 7.0},
    "metabolism": {"points": [(40.2, 35.6)], "size": 7.5},
    "immune":     {"points": [(64.2, 35.5)], "size": 6.5},
    "bones":      {"points": [(32.6, 52.2), (67.8, 52.2)], "size": 8.0},
    "muscles":    {"points": [(37.8, 65.4), (62.6, 65.4)], "size": 8.0},
}
WHOLE_BODY = "whole_body"
ZONES: tuple[str, ...] = (*ZONE_LAYOUT, WHOLE_BODY)

_FLAGGED_SCALE = 2.1


def image_path() -> Path | None:
    for name in IMAGE_CANDIDATES:
        candidate = ASSETS / name
        if candidate.is_file():
            return candidate
    return None


@st.cache_data(show_spinner=False)
def _data_uri(path: str, modified: float) -> str:
    file = Path(path)
    encoded = base64.b64encode(file.read_bytes()).decode("ascii")
    return f"data:{_MIME.get(file.suffix.lower(), 'image/png')};base64,{encoded}"


def _markers(levels: Mapping[str, int]) -> str:
    parts = []
    for zone, layout in ZONE_LAYOUT.items():
        level = int(levels.get(zone, 0))
        size = layout["size"] * (_FLAGGED_SCALE if level else 1)
        title = ui.esc(f"{t(f'zone.{zone}')}: {t(f'severity.{level}')}")
        for x, y in layout["points"]:
            parts.append(
                f'<span class="ah-zone ah-s{level}" title="{title}" '
                f'style="left:{x}%;top:{y}%;width:{size:.1f}%"></span>')
    return "".join(parts)


def _colour_key() -> str:
    items = "".join(
        f'<li class="ah-s{level}"><span class="ah-dot"></span>{ui.esc(t(f"severity.{level}"))}</li>'
        for level in (0, 1, 2))
    return f'<ul class="ah-key">{items}</ul>'


def _flagged_list(levels: Mapping[str, int]) -> str:
    flagged = sorted(((int(levels.get(zone, 0)), zone) for zone in ZONES
                      if levels.get(zone, 0)), key=lambda item: -item[0])
    if not flagged:
        return ""
    items = "".join(
        f'<li class="ah-s{level}"><span class="ah-dot"></span>{ui.esc(t(f"zone.{zone}"))}'
        f'<span class="ah-zstate">{ui.esc(t(f"severity.{level}"))}</span></li>'
        for level, zone in flagged)
    return f'<ul class="ah-zones">{items}</ul>'


def render(levels: Mapping[str, int]) -> None:
    path = image_path()
    whole = int(levels.get(WHOLE_BODY, 0))
    label = ui.esc(t("body.figure_label"))
    if path is None:
        picture, shape = "", ' style="aspect-ratio: 500 / 1204"'
    else:
        picture = f'<img src="{_data_uri(str(path), path.stat().st_mtime)}" alt="">'
        shape = ""
    ui.html(
        f'<div class="ah-body">'
        f'<div class="ah-figure ah-wb{whole}" role="img" aria-label="{label}"{shape}>'
        f'{picture}{_markers(levels)}</div>'
        f'{_colour_key()}{_flagged_list(levels)}'
        f'</div>'
    )
