"""Small, transparent audit rules for a single canonical workbook."""

from __future__ import annotations

from .models import AuditFinding, AuditResult, RiskLevel, WorkbookFact


def audit_workbook(workbook: WorkbookFact) -> AuditResult:
    """Generate explainable presence-based findings without evaluating workbook logic."""

    findings: list[AuditFinding] = []
    if workbook.has_vba:
        findings.append(
            AuditFinding(
                category="vba_present",
                subject="xl/vbaProject.bin",
                risk=RiskLevel.HIGH,
                reason="The workbook contains a VBA project. XLSX-Ray did not execute or inspect macro code.",
                evidence={"has_vba": True},
            )
        )
    for link in workbook.external_links:
        findings.append(
            AuditFinding(
                category="external_link_present",
                subject=link,
                risk=RiskLevel.HIGH,
                reason="The workbook contains an external link. XLSX-Ray did not follow the target.",
                evidence={"target": link},
            )
        )
    if not workbook.workbook_protection:
        findings.append(
            AuditFinding(
                category="workbook_protection_absent",
                subject="workbook",
                risk=RiskLevel.LOW,
                reason="No workbook protection fact was found. This is a review prompt, not a security assessment.",
                evidence={"workbook_protection": {}},
            )
        )
    for name, sheet in workbook.sheets.items():
        if not sheet.protection:
            findings.append(
                AuditFinding(
                    category="worksheet_protection_absent",
                    subject=name,
                    risk=RiskLevel.LOW,
                    reason="No worksheet protection fact was found. This is a review prompt, not a security assessment.",
                    evidence={"worksheet_protection": {}},
                )
            )
    for feature in workbook.unsupported_features:
        findings.append(
            AuditFinding(
                category="unsupported_feature_present",
                subject="workbook",
                risk=RiskLevel.MEDIUM,
                reason="A workbook feature outside the v0.1 semantic model is present.",
                evidence={"feature": feature},
            )
        )
    return AuditResult(
        source=workbook.source,
        findings=tuple(
            sorted(findings, key=lambda item: (item.risk * -1, item.category, item.subject))
        ),
        warnings=workbook.warnings,
    )
