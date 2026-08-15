"""Immutable-ish canonical models used by XLSX-Ray's read-only OOXML inspector."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Any


class RiskLevel(IntEnum):
    """Ordered, explainable CI severity levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3

    @classmethod
    def parse(cls, value: str) -> RiskLevel:
        try:
            return cls[value.upper()]
        except KeyError as exc:
            choices = ", ".join(member.name.lower() for member in cls)
            raise ValueError(f"unknown risk level '{value}'; choose one of: {choices}") from exc

    @property
    def label(self) -> str:
        return self.name.lower()


@dataclass(frozen=True)
class CellFact:
    address: str
    value: str | None = None
    formula: str | None = None
    formula_normalized: str | None = None
    data_type: str | None = None

    def display_value(self) -> str | None:
        return self.formula if self.formula is not None else self.value


@dataclass(frozen=True)
class WorksheetFact:
    name: str
    part_name: str
    cells: dict[str, CellFact] = field(default_factory=dict)
    data_validations: tuple[str, ...] = ()
    protection: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DefinedNameFact:
    name: str
    value: str
    local_sheet_id: str | None = None


@dataclass(frozen=True)
class WorkbookFact:
    source: str
    sheets: dict[str, WorksheetFact]
    defined_names: dict[tuple[str, str | None], DefinedNameFact]
    external_links: tuple[str, ...]
    workbook_protection: dict[str, str]
    has_vba: bool
    unsupported_features: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class Change:
    category: str
    subject: str
    before: Any
    after: Any
    risk: RiskLevel
    reason: str
    impact: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["risk"] = self.risk.label
        data["impact"] = list(self.impact)
        return data


@dataclass(frozen=True)
class DiffResult:
    old_source: str
    new_source: str
    changes: tuple[Change, ...]
    warnings: tuple[str, ...] = ()

    @property
    def highest_risk(self) -> RiskLevel | None:
        return max((change.risk for change in self.changes), default=None)

    @property
    def counts(self) -> dict[str, int]:
        return {
            level.label: sum(change.risk is level for change in self.changes) for level in RiskLevel
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "0.1",
            "old_source": self.old_source,
            "new_source": self.new_source,
            "summary": {
                "change_count": len(self.changes),
                "highest_risk": self.highest_risk.label if self.highest_risk else None,
                "risk_counts": self.counts,
            },
            "changes": [change.to_dict() for change in self.changes],
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class AuditFinding:
    category: str
    subject: str
    risk: RiskLevel
    reason: str
    evidence: Any

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["risk"] = self.risk.label
        return data


@dataclass(frozen=True)
class AuditResult:
    source: str
    findings: tuple[AuditFinding, ...]
    warnings: tuple[str, ...] = ()

    @property
    def highest_risk(self) -> RiskLevel | None:
        return max((finding.risk for finding in self.findings), default=None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "0.1",
            "source": self.source,
            "summary": {
                "finding_count": len(self.findings),
                "highest_risk": self.highest_risk.label if self.highest_risk else None,
            },
            "findings": [finding.to_dict() for finding in self.findings],
            "warnings": list(self.warnings),
        }
