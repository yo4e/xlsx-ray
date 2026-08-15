"""Stable human- and machine-readable renderers for XLSX-Ray results."""

from __future__ import annotations

import json
from typing import Any

from .models import AuditResult, Change, DiffResult


def json_output(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _fence(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = str(value).replace("|", "\\|").replace("\n", " ")
    return f"`{text}`"


def _change_row(change: Change) -> str:
    impact = ", ".join(f"`{item}`" for item in change.impact) if change.impact else "—"
    return " | ".join(
        [
            f"`{change.risk.label}`",
            f"`{change.category}`",
            f"`{change.subject}`",
            _fence(change.before),
            _fence(change.after),
            change.reason,
            impact,
        ]
    )


def render_diff_markdown(result: DiffResult) -> str:
    """Render an intentionally concise report suitable for a PR summary."""

    highest = result.highest_risk.label if result.highest_risk else "none"
    lines = [
        "# XLSX-Ray workbook diff",
        "",
        f"- **Before:** `{result.old_source}`",
        f"- **After:** `{result.new_source}`",
        f"- **Changes:** {len(result.changes)}",
        f"- **Highest risk:** `{highest}`",
        "",
        "| Risk | Category | Subject | Before | After | Why it matters | Direct formula dependents |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    if result.changes:
        lines.extend(f"| {_change_row(change)} |" for change in result.changes)
    else:
        lines.append(
            "| `low` | `no_changes` | — | — | — | No supported workbook facts changed. | — |"
        )
    if result.warnings:
        lines.extend(["", "## Inspection warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(
        [
            "",
            "> XLSX-Ray is read-only and does not calculate formulas, execute VBA, or follow external links. Direct formula dependents are textual references only.",
            "",
        ]
    )
    return "\n".join(lines)


def render_audit_markdown(result: AuditResult) -> str:
    highest = result.highest_risk.label if result.highest_risk else "none"
    lines = [
        "# XLSX-Ray workbook audit",
        "",
        f"- **Workbook:** `{result.source}`",
        f"- **Findings:** {len(result.findings)}",
        f"- **Highest risk:** `{highest}`",
        "",
        "| Risk | Category | Subject | Why it matters | Evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    if result.findings:
        for finding in result.findings:
            lines.append(
                " | ".join(
                    [
                        f"| `{finding.risk.label}`",
                        f"`{finding.category}`",
                        f"`{finding.subject}`",
                        finding.reason,
                        _fence(finding.evidence) + " |",
                    ]
                )
            )
    else:
        lines.append("| `low` | `no_findings` | — | No supported audit findings. | — |")
    if result.warnings:
        lines.extend(["", "## Inspection warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "> XLSX-Ray never executes VBA, evaluates formulas, or follows links.", ""])
    return "\n".join(lines)
