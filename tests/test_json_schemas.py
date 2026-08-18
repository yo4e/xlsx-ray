from __future__ import annotations

import json
from importlib.resources import files

from jsonschema import Draft202012Validator

from xlsx_ray.models import (
    AuditFinding,
    AuditResult,
    Change,
    DiffResult,
    ImpactEvidence,
    RiskLevel,
)


def _schema(name: str) -> dict[str, object]:
    path = files("xlsx_ray").joinpath("schemas", name)
    return json.loads(path.read_text(encoding="utf-8"))


def test_diff_output_matches_published_schema() -> None:
    schema = _schema("diff-0.2.schema.json")
    Draft202012Validator.check_schema(schema)
    result = DiffResult(
        old_source="before.xlsx",
        new_source="after.xlsx",
        changes=(
            Change(
                category="formula_changed",
                subject="Inputs!A1",
                before="=1",
                after="=2",
                risk=RiskLevel.HIGH,
                reason="A formula changed; formula results are not calculated by XLSX-Ray.",
                impact=("Model!B1",),
                impact_evidence=(
                    ImpactEvidence(
                        formula_cell="Model!B1",
                        kind="defined_name",
                        reference="InputValue",
                        resolved_range="Inputs!$A$1",
                        reason="Static reviewer evidence only.",
                    ),
                ),
            ),
        ),
        warnings=("example warning",),
    )

    Draft202012Validator(schema).validate(result.to_dict())


def test_audit_output_matches_published_schema() -> None:
    schema = _schema("audit-0.1.schema.json")
    Draft202012Validator.check_schema(schema)
    result = AuditResult(
        source="workbook.xlsm",
        findings=(
            AuditFinding(
                category="vba_present",
                subject="workbook.xlsm",
                risk=RiskLevel.HIGH,
                reason="The package contains a VBA project.",
                evidence={"has_vba": True},
            ),
        ),
        warnings=(),
    )

    Draft202012Validator(schema).validate(result.to_dict())
