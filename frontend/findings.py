from __future__ import annotations

from typing import Any, Iterable, Mapping

from backend.diagnosis import knowledge_base
from data import catalog
from frontend import i18n, ui
from frontend.i18n import t


def _evidence(code: str, entry: Mapping[str, Any], baseline: Mapping[str, Any]) -> str:
    lines = []
    for key in knowledge_base.related_metrics(code):
        value = entry.get(key)
        if catalog.is_missing(value):
            continue
        label = ui.esc(i18n.metric_label(key))
        shown = f"<b>{ui.esc(i18n.format_metric(key, value))}</b>"
        norm = baseline.get(key)
        if catalog.is_missing(norm):
            line = t("astro.evidence_plain", label=label, value=shown)
        else:
            line = t("astro.evidence", label=label, value=shown,
                     baseline=ui.esc(i18n.format_metric(key, norm)))
        lines.append(f"<li>{line}</li>")
    return f'<ul class="ah-evidence">{"".join(lines)}</ul>' if lines else ""


def finding_html(code: str, severity: int, zone: str, entry: Mapping[str, Any] | None = None,
                 baseline: Mapping[str, Any] | None = None, compact: bool = False) -> str:
    text = knowledge_base.describe(code, i18n.language())
    where = (f'<p class="ah-where"><span class="ah-chip ah-s{severity}">'
             f'{ui.esc(t(f"severity.{severity}"))}</span>{ui.esc(t(f"zone.{zone}"))}</p>')
    if compact:
        return (f'<article class="ah-finding ah-compact ah-s{severity}">'
                f'<h3>{ui.esc(text.name)}</h3>{where}</article>')
    evidence = _evidence(code, entry or {}, baseline or {})
    return (
        f'<article class="ah-finding ah-s{severity}">'
        f'<h3>{ui.esc(text.name)}</h3>{where}'
        f'<p>{ui.esc(text.explanation)}</p>{evidence}'
        f'<p class="ah-advice"><b>{ui.esc(t("astro.advice_label"))}:</b> {ui.esc(text.advice)}</p>'
        f'</article>'
    )


def findings_html(findings: Iterable[Any], entry: Mapping[str, Any] | None = None,
                  baseline: Mapping[str, Any] | None = None, compact: bool = False) -> str:
    parts = []
    for finding in findings:
        if isinstance(finding, Mapping):
            code, severity, zone = finding["code"], finding["severity"], finding["zone"]
        else:
            code, severity, zone = finding.code, finding.severity, finding.zone
        parts.append(finding_html(code, int(severity), zone, entry, baseline, compact))
    return f'<div class="ah-findings">{"".join(parts)}</div>'


def all_clear_html() -> str:
    return (f'<div class="ah-findings"><article class="ah-finding ah-s0">'
            f'<h3>{ui.esc(t("astro.all_clear_title"))}</h3>'
            f'<p>{ui.esc(t("astro.all_clear_body"))}</p></article></div>')
