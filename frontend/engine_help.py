from __future__ import annotations

import sys

import streamlit as st

from backend.diagnosis import build
from frontend import ui
from frontend.i18n import t

_BUILD_ERROR = "engine_build_error"

_INSTALL = {
    "windows": "winget install BrechtSanders.WinLibs.POSIX.UCRT",
    "macos": "xcode-select --install",
    "linux": "sudo apt install build-essential",
}
_CHECK = "gcc --version"
_BUILD = "python -m backend.diagnosis.build"


def system() -> str:
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def _try_again() -> None:
    try:
        build.build()
    except build.BuildError as error:
        st.session_state[_BUILD_ERROR] = str(error)
        return
    st.session_state.pop(_BUILD_ERROR, None)
    st.rerun()


def render(error: Exception | None) -> None:
    missing = build.find_compiler() is None
    detail = st.session_state.get(_BUILD_ERROR) or (str(error) if error else "")
    os_key = system()

    reason = t("engine.reason_missing") if missing else t("engine.reason_failed")
    ui.html(
        f'<div class="ah-callout">'
        f'<h3>{ui.esc(t("engine.title"))}</h3>'
        f'<p>{ui.esc(t("engine.lead"))}</p>'
        f'<p class="ah-note">{ui.esc(reason)}</p>'
        f'</div>')

    if missing:
        ui.html(f'<p class="ah-group">{ui.esc(t("engine.steps_heading", os=t(f"engine.os.{os_key}")))}</p>')
        st.markdown(f"**1.** {t(f'engine.step_install.{os_key}')}")
        st.code(_INSTALL[os_key], language="bash")
        st.markdown(f"**2.** {t(f'engine.step_restart.{os_key}')}")
        st.markdown(f"**3.** {t('engine.step_check')}")
        st.code(_CHECK, language="bash")
        st.markdown(f"**4.** {t('engine.step_again')}")
    else:
        ui.html(f'<p class="ah-group">{ui.esc(t("engine.steps_heading", os=t(f"engine.os.{os_key}")))}</p>')
        st.markdown(f"**1.** {t('engine.step_build')}")
        st.code(_BUILD, language="bash")
        st.markdown(f"**2.** {t('engine.step_again')}")

    if ui.button(t("engine.retry"), key="engine_retry", stretch=False):
        _try_again()
        detail = st.session_state.get(_BUILD_ERROR) or detail
        if st.session_state.get(_BUILD_ERROR):
            st.error(t("engine.still_failing"))

    ui.html(f'<p class="ah-note">{ui.esc(t("engine.data_safe"))}</p>')
    if detail:
        with st.expander(t("engine.details")):
            st.code(detail, language="text")
