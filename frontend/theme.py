"""Owner: frontend developer (Streamlit)."""
from __future__ import annotations

from frontend import ui

BACKGROUND = "#15323d"
TEXT = "#f2efe9"
BUTTON = "#52b788"
ACCENT = "#9cb8bf"

STATUS = {0: "#8b93a7", 1: "#e9c46a", 2: "#e65c4f"}

DISPLAY_FONT = ('"Bahnschrift", "DIN Alternate", "Avenir Next Condensed", '
                '"Roboto Condensed", "Arial Narrow", sans-serif')

CSS = f"""
:root {{
  --ah-bg: {BACKGROUND};
  --ah-text: {TEXT};
  --ah-button: {BUTTON};
  --ah-accent: {ACCENT};
  --ah-line: rgba(156, 184, 191, 0.3);
  --ah-ok: {STATUS[0]};
  --ah-caution: {STATUS[1]};
  --ah-critical: {STATUS[2]};
  --ah-display: {DISPLAY_FONT};
}}

.stApp {{ background: var(--ah-bg); color: var(--ah-text); }}
.stApp .stMainBlockContainer, .stApp .block-container {{
  max-width: 1180px; padding-top: 3.4rem; padding-bottom: 4rem;
}}
.stApp h1, .stApp h2, .stApp h3 {{
  font-family: var(--ah-display); font-weight: 600; letter-spacing: 0.01em; color: var(--ah-text);
}}
.stApp [data-testid="stCaptionContainer"] {{ color: var(--ah-accent); }}
.stApp hr {{ border-color: var(--ah-line); }}

.stApp .stButton button, .stApp .stFormSubmitButton button,
.stApp [data-testid="stFormSubmitButton"] button {{
  background-color: var(--ah-button) !important; border: 1px solid var(--ah-button) !important;
  color: var(--ah-bg) !important; font-weight: 600; border-radius: 6px;
}}
.stApp .stButton button:not(:disabled):hover, .stApp .stFormSubmitButton button:hover,
.stApp [data-testid="stFormSubmitButton"] button:hover {{
  background-color: #6ac59b !important; border-color: #6ac59b !important;
}}
.stApp .stButton button:not(:disabled):active, .stApp .stFormSubmitButton button:active,
.stApp [data-testid="stFormSubmitButton"] button:active {{
  background-color: #46a377 !important; border-color: #46a377 !important;
}}
.stApp .stButton button:focus-visible, .stApp .stFormSubmitButton button:focus-visible,
.stApp [data-testid="stFormSubmitButton"] button:focus-visible {{
  outline: 2px solid var(--ah-text); outline-offset: 2px; box-shadow: none;
}}
.stApp .stButton button:disabled {{
  background-color: transparent !important; border-color: var(--ah-line) !important;
  color: rgba(156, 184, 191, 0.55) !important;
}}
.stApp .stButton button p, .stApp .stFormSubmitButton button p,
.stApp .stButton button div, .stApp .stFormSubmitButton button div {{
  color: inherit !important; font-weight: inherit;
}}

.ah-title {{
  font-family: var(--ah-display); font-size: 2.3rem; font-weight: 600; line-height: 1.1;
  margin: 0; padding: 0; color: var(--ah-text);
}}
.ah-heading {{
  font-family: var(--ah-display); font-size: 1.6rem; font-weight: 600; line-height: 1.2;
  margin: 0.4rem 0 0.2rem; padding: 0; color: var(--ah-text);
}}
.ah-subheading {{
  font-family: var(--ah-display); font-size: 1.25rem; font-weight: 600; line-height: 1.25;
  margin: 0 0 0.2rem; padding: 0; color: var(--ah-text);
}}
.ah-group {{
  font-family: var(--ah-display); font-size: 1.15rem; font-weight: 600;
  margin: 1.1rem 0 0; padding: 0;
}}
.ah-lead {{ max-width: 68ch; margin: 0 0 0.6rem; line-height: 1.5; color: var(--ah-text); }}
.ah-note {{ max-width: 70ch; margin: 0 0 0.5rem; font-size: 0.92rem; line-height: 1.45;
  color: var(--ah-accent); }}

.ah-pname {{
  display: flex; align-items: center; gap: 0.55rem; margin: 0 0 0.35rem;
  font-family: var(--ah-display); font-size: 1.5rem; font-weight: 600; line-height: 1.2;
  color: var(--ah-text); overflow-wrap: anywhere;
}}
.ah-alert {{
  flex: none; display: inline-flex; align-items: center; justify-content: center;
  width: 1.55rem; height: 1.55rem; border-radius: 50%;
  background: var(--ah-caution); color: var(--ah-bg); font-size: 1.1rem; font-weight: 700;
}}
.ah-meta {{ margin: 0; font-size: 0.93rem; line-height: 1.55; color: var(--ah-accent); }}
.ah-meta.ah-late {{ color: var(--ah-caution); }}

.ah-body {{
  padding: 1.1rem 0.9rem 1.2rem; border: 1px solid var(--ah-line); border-radius: 14px;
  background: radial-gradient(ellipse at 50% 38%, rgba(156, 184, 191, 0.09), rgba(21, 50, 61, 0) 72%);
}}
.ah-figure {{ position: relative; width: 100%; max-width: 300px; margin: 0 auto; }}
.ah-figure img {{
  display: block; width: 100%; height: auto; user-select: none; pointer-events: none;
  transition: filter 0.4s ease;
}}
.ah-zone {{
  position: absolute; aspect-ratio: 1 / 1; border-radius: 50%;
  transform: translate(-50%, -50%);
}}
.ah-zone.ah-s0 {{ border: 1.5px solid var(--ah-ok); background: rgba(139, 147, 167, 0.22); }}
.ah-zone.ah-s1 {{
  background: radial-gradient(circle, var(--ah-caution) 0 26%, rgba(233, 196, 106, 0.55) 27% 46%,
    rgba(233, 196, 106, 0) 70%);
}}
.ah-zone.ah-s2 {{
  background: radial-gradient(circle, var(--ah-critical) 0 26%, rgba(230, 92, 79, 0.6) 27% 46%,
    rgba(230, 92, 79, 0) 70%);
  animation: ah-pulse 1.5s ease-in-out infinite;
}}
@keyframes ah-pulse {{
  0%, 100% {{ transform: translate(-50%, -50%) scale(1); }}
  50% {{ transform: translate(-50%, -50%) scale(1.3); }}
}}
@media (prefers-reduced-motion: reduce) {{ .ah-zone.ah-s2 {{ animation: none; }} }}
.ah-figure.ah-wb1 img {{ filter: drop-shadow(0 0 7px rgba(233, 196, 106, 0.85)); }}
.ah-figure.ah-wb2 img {{ filter: drop-shadow(0 0 9px rgba(230, 92, 79, 0.95)); }}

.ah-key, .ah-zones {{ list-style: none; padding: 0; }}
.ah-key {{
  display: flex; flex-wrap: wrap; justify-content: center; gap: 0.3rem 1.1rem;
  margin: 1.1rem 0 0; font-size: 0.86rem; color: var(--ah-accent);
}}
.ah-key li, .ah-zones li {{ display: flex; align-items: center; gap: 0.45rem; margin: 0; padding: 0; }}
.ah-dot {{ flex: none; width: 0.72rem; height: 0.72rem; border-radius: 50%; background: var(--ah-ok); }}
.ah-s1 > .ah-dot {{ background: var(--ah-caution); }}
.ah-s2 > .ah-dot {{ background: var(--ah-critical); }}
.ah-zones {{
  max-width: 350px; margin: 0.9rem auto 0; padding-top: 0.7rem;
  border-top: 1px solid var(--ah-line); display: grid; gap: 0.3rem; font-size: 0.95rem;
}}
.ah-zones li {{ color: var(--ah-text); font-weight: 600; }}
.ah-zstate {{ margin-left: auto; padding-left: 0.8rem; font-weight: 400; color: var(--ah-accent);
  white-space: nowrap; }}

.ah-findings {{ display: flex; flex-direction: column; gap: 1.5rem; margin: 0.5rem 0 1.1rem; }}
.ah-finding {{ border-left: 4px solid var(--ah-ok); padding: 0.05rem 0 0.05rem 1rem; }}
.ah-finding.ah-s1 {{ border-left-color: var(--ah-caution); }}
.ah-finding.ah-s2 {{ border-left-color: var(--ah-critical); }}
.ah-finding h3 {{ font-size: 1.3rem; line-height: 1.25; margin: 0 0 0.3rem; padding: 0; }}
.ah-finding p {{ max-width: 64ch; margin: 0 0 0.5rem; line-height: 1.5; }}
.ah-where {{ font-size: 0.9rem; color: var(--ah-accent); }}
.ah-chip {{
  display: inline-block; margin-right: 0.5rem; padding: 0.05rem 0.6rem; border-radius: 999px;
  background: var(--ah-ok); color: var(--ah-bg); font-size: 0.82rem; font-weight: 700;
}}
.ah-chip.ah-s1 {{ background: var(--ah-caution); }}
.ah-chip.ah-s2 {{ background: var(--ah-critical); }}
.ah-evidence {{ list-style: none; margin: 0 0 0.5rem; padding: 0; font-size: 0.95rem;
  color: var(--ah-accent); }}
.ah-evidence li {{ margin: 0; padding: 0; }}
.ah-evidence b {{ color: var(--ah-text); font-weight: 600; }}
.ah-advice b {{ color: var(--ah-accent); font-weight: 600; }}
.ah-finding.ah-compact h3 {{ font-size: 1.05rem; margin: 0; }}
.ah-finding.ah-compact .ah-where {{ margin: 0.15rem 0 0; }}

.ah-month {{
  margin: 0; text-align: center; font-family: var(--ah-display); font-size: 1.2rem;
  font-weight: 600; color: var(--ah-text);
}}
.ah-weekday {{ text-align: center; font-size: 0.8rem; color: var(--ah-accent); }}
.ah-cal {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; max-width: 360px;
  margin: 0 auto; }}
.ah-cal > div {{
  display: flex; align-items: center; justify-content: center; height: 2.15rem;
  border: 1px solid transparent; border-radius: 6px; font-size: 0.92rem; color: var(--ah-text);
}}
.ah-cal > .ah-weekday {{ height: 1.5rem; }}
.ah-cal > .ah-done {{ background: var(--ah-button); color: var(--ah-bg); font-weight: 700; }}
.ah-cal > .ah-rest {{ border: 1px dashed var(--ah-accent); color: var(--ah-accent); }}
.ah-cal > .ah-today {{ outline: 2px solid var(--ah-text); outline-offset: 1px; }}
.ah-cal > .ah-later {{ color: rgba(156, 184, 191, 0.45); }}
.ah-callegend {{
  list-style: none; display: flex; flex-wrap: wrap; justify-content: center;
  gap: 0.3rem 1.1rem; max-width: 360px; margin: 0.7rem auto 0; padding: 0;
  font-size: 0.84rem; color: var(--ah-accent);
}}
.ah-callegend li {{ display: flex; align-items: center; gap: 0.4rem; margin: 0; padding: 0; }}
.ah-swatch {{ flex: none; width: 0.95rem; height: 0.95rem; border-radius: 4px;
  border: 1px solid transparent; }}
.ah-swatch.ah-done {{ background: var(--ah-button); }}
.ah-swatch.ah-rest {{ border: 1px dashed var(--ah-accent); }}
.ah-swatch.ah-today {{ outline: 2px solid var(--ah-text); outline-offset: -2px; }}

[class*="st-key-history_day_"] button {{ min-height: 2.5rem; padding: 0.2rem 0; }}

.ah-callout {{
  border: 1px solid var(--ah-line); border-left: 4px solid var(--ah-accent); border-radius: 10px;
  background: rgba(156, 184, 191, 0.08); padding: 0.9rem 1.2rem 0.6rem; margin: 0.3rem 0 0.9rem;
}}
.ah-callout h3 {{ font-size: 1.3rem; margin: 0 0 0.35rem; padding: 0; }}
.ah-callout p {{ max-width: 64ch; margin: 0 0 0.55rem; line-height: 1.5; }}

.ah-reminder {{
  border-left: 4px solid var(--ah-button); padding: 0.1rem 0 0.1rem 1rem; margin: 0.3rem 0 0.9rem;
  max-width: 60ch; line-height: 1.5;
}}
.ah-reminder p {{ margin: 0 0 0.3rem; }}
.ah-reminder .ah-note {{ margin: 0; }}
"""


def inject() -> None:
    ui.html(f"<style>{CSS}</style>")


def severity_colour(level: int) -> str:
    return STATUS.get(int(level), STATUS[0])
