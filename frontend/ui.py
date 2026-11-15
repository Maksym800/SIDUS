from __future__ import annotations

import html as _html
import inspect
from functools import lru_cache
from typing import Any

import streamlit as st


def esc(text: Any) -> str:
    return _html.escape(str(text), quote=True)


def html(body: str) -> None:
    if hasattr(st, "html"):
        st.html(body)
    else:
        st.markdown(body, unsafe_allow_html=True)


@lru_cache(maxsize=None)
def _accepts(command: str, option: str) -> bool:
    try:
        return option in inspect.signature(getattr(st, command)).parameters
    except (AttributeError, TypeError, ValueError):
        return False


def _layout_options(command: str, stretch: bool, wrap: bool) -> dict[str, Any]:
    options: dict[str, Any] = {}
    if stretch:
        if _accepts(command, "width"):
            options["width"] = "stretch"
        elif _accepts(command, "use_container_width"):
            options["use_container_width"] = True
    if wrap and _accepts(command, "wrap"):
        options["wrap"] = True
    return options


def button(label: str, key: str, *, stretch: bool = True, wrap: bool = True,
           **options: Any) -> bool:
    return st.button(label, key=key, **_layout_options("button", stretch, wrap), **options)


def download_button(label: str, data: bytes, file_name: str, key: str, *,
                    mime: str = "text/csv", **options: Any) -> bool:
    return st.download_button(label, data, file_name=file_name, mime=mime, key=key,
                              **_layout_options("download_button", True, False), **options)


def submit_button(label: str, *, stretch: bool = False, **options: Any) -> bool:
    return st.form_submit_button(
        label, **_layout_options("form_submit_button", stretch, True), **options)


def form(key: str):
    if _accepts("form", "enter_to_submit"):
        return st.form(key, enter_to_submit=False)
    return st.form(key)
