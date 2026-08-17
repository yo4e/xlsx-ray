"""Deterministic comparison and evidence-only impact classification."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .formulas import (
    extract_name_tokens,
    extract_static_references,
    has_unsupported_reference_construct,
    parse_static_range,
)
from .models import (
    Change,
    DefinedNameFact,
    ImpactEvidence,
    RiskLevel,
    WorkbookFact,
    WorksheetFact,
)


def _evidence_sort_key(evidence: ImpactEvidence) -> tuple[str, str, str, str, str]:
    return (
        evidence.formula_cell,
        evidence.kind,
        evidence.reference.casefold(),
        evidence.resolved_range or "",
        evidence.reason,
    )


def _make_change(
    category: str,
    subject: str,
    before: Any,
    after: Any,
    risk: RiskLevel,
    reason: str,
    impact: Iterable[str] = (),
    impact_evidence: Iterable[ImpactEvidence] = (),
) -> Change:
    evidence = tuple(sorted(set(impact_evidence), key=_evidence_sort_key))
    return Change(
        category=category,
        subject=subject,
        before=before,
        after=after,
        risk=risk,
        reason=reason,
        impact=tuple(sorted(set(impact) | {item.formula_cell for item in evidence})),
        impact_evidence=evidence,
    )


def _sheet_rename_pairs(old: WorkbookFact, new: WorkbookFact) -> list[tuple[str, str]]:
    """Identify a rename only when one OOXML worksheet part is retained."""

    removed = {name: sheet for name, sheet in old.sheets.items() if name not in new.sheets}
    added = {name: sheet for name, sheet in new.sheets.items() if name not in old.sheets}
    pairs: list[tuple[str, str]] = []
    for old_name, old_sheet in removed.items():
        candidates = [
            new_name
            for new_name, new_sheet in added.items()
            if new_sheet.part_name == old_sheet.part_name
        ]
        if len(candidates) == 1:
            pairs.append((old_name, candidates[0]))
    return sorted(pairs)


def _formula_cells(workbook: WorkbookFact) -> Iterable[tuple[WorksheetFact, str, str]]:
    for _sheet_name, sheet in workbook.sheets.items():
        for address, cell in sheet.cells.items():
            if cell.formula:
                yield sheet, address, cell.formula


def _defined_name_candidates(
    workbook: WorkbookFact, name: str, local_sheet_id: str | None
) -> tuple[DefinedNameFact, ...]:
    return tuple(
        fact
        for (candidate_name, candidate_scope), fact in workbook.defined_names.items()
        if candidate_scope == local_sheet_id and candidate_name.casefold() == name.casefold()
    )


def _resolve_defined_name(
    workbook: WorkbookFact, formula_sheet: WorksheetFact, name: str
) -> DefinedNameFact | None:
    """Resolve a name by Excel-style active local scope then workbook scope.

    Resolution deliberately returns ``None`` for duplicate case-folded names or
    any ambiguity rather than guessing. A local name on a different sheet is
    not visible to the formula being inspected.
    """

    local = _defined_name_candidates(workbook, name, formula_sheet.local_sheet_id)
    if len(local) == 1:
        return local[0]
    if len(local) > 1:
        return None
    workbook_scope = _defined_name_candidates(workbook, name, None)
    return workbook_scope[0] if len(workbook_scope) == 1 else None


def _formula_reference_evidence(
    formula_sheet: WorksheetFact,
    formula_address: str,
    formula: str,
    changed_sheet: str,
    changed_address: str,
) -> list[ImpactEvidence]:
    formula_cell = f"{formula_sheet.name}!{formula_address}"
    if has_unsupported_reference_construct(formula):
        return []
    evidence: list[ImpactEvidence] = []
    for reference in extract_static_references(formula):
        bound = reference.with_default_sheet(formula_sheet.name)
        if not bound.contains(changed_sheet, changed_address):
            continue
        if bound.is_single_cell:
            kind = "direct_a1"
            reason = "Formula text contains this direct A1 reference; this is static review evidence only."
        else:
            kind = "range_overlap"
            reason = "Changed cell lies within this static A1 range in formula text; this is review evidence only."
        evidence.append(
            ImpactEvidence(
                formula_cell=formula_cell,
                kind=kind,
                reference=reference.source_text,
                resolved_range=bound.resolved_range,
                reason=reason,
            )
        )
    return evidence


def _formula_name_evidence_for_cell(
    workbook: WorkbookFact,
    formula_sheet: WorksheetFact,
    formula_address: str,
    formula: str,
    changed_sheet: str,
    changed_address: str,
) -> list[ImpactEvidence]:
    formula_cell = f"{formula_sheet.name}!{formula_address}"
    if has_unsupported_reference_construct(formula):
        return []
    evidence: list[ImpactEvidence] = []
    for token in extract_name_tokens(formula):
        definition = _resolve_defined_name(workbook, formula_sheet, token)
        if definition is None:
            continue
        static_range = parse_static_range(definition.value)
        if static_range is None or not static_range.contains(changed_sheet, changed_address):
            continue
        scope = "local" if definition.local_sheet_id is not None else "workbook"
        evidence.append(
            ImpactEvidence(
                formula_cell=formula_cell,
                kind="defined_name",
                reference=definition.name,
                resolved_range=static_range.resolved_range,
                reason=(
                    f"Formula text uses the {scope}-scoped defined name '{definition.name}', "
                    "whose static A1 target contains the changed cell; this is review evidence only."
                ),
            )
        )
    return evidence


def _impact_evidence_for_cell(
    workbook: WorkbookFact, sheet_name: str, address: str
) -> tuple[ImpactEvidence, ...]:
    evidence: list[ImpactEvidence] = []
    for formula_sheet, formula_address, formula in _formula_cells(workbook):
        evidence.extend(
            _formula_reference_evidence(
                formula_sheet, formula_address, formula, sheet_name, address
            )
        )
        evidence.extend(
            _formula_name_evidence_for_cell(
                workbook,
                formula_sheet,
                formula_address,
                formula,
                sheet_name,
                address,
            )
        )
    return tuple(sorted(set(evidence), key=_evidence_sort_key))


def _defined_name_usage_evidence(
    workbook: WorkbookFact, definition: DefinedNameFact
) -> tuple[ImpactEvidence, ...]:
    """Report formulas that use a changed supported name, without evaluation."""

    static_range = parse_static_range(definition.value)
    if static_range is None:
        return ()
    evidence: list[ImpactEvidence] = []
    for formula_sheet, formula_address, formula in _formula_cells(workbook):
        if has_unsupported_reference_construct(formula):
            continue
        for token in extract_name_tokens(formula):
            resolved = _resolve_defined_name(workbook, formula_sheet, token)
            if resolved != definition:
                continue
            scope = "local" if definition.local_sheet_id is not None else "workbook"
            evidence.append(
                ImpactEvidence(
                    formula_cell=f"{formula_sheet.name}!{formula_address}",
                    kind="defined_name",
                    reference=definition.name,
                    resolved_range=static_range.resolved_range,
                    reason=(
                        f"Formula text uses this changed {scope}-scoped defined name; "
                        "the displayed static target is review evidence only."
                    ),
                )
            )
    return tuple(sorted(set(evidence), key=_evidence_sort_key))


def _cell_impact_evidence(
    workbook: WorkbookFact, sheet_name: str, address: str
) -> tuple[ImpactEvidence, ...]:
    return _impact_evidence_for_cell(workbook, sheet_name, address)


def _compare_cells(
    old_sheet: WorksheetFact,
    new_sheet: WorksheetFact,
    old_workbook: WorkbookFact,
    new_workbook: WorkbookFact,
) -> list[Change]:
    changes: list[Change] = []
    addresses = sorted(set(old_sheet.cells) | set(new_sheet.cells))
    for address in addresses:
        before = old_sheet.cells.get(address)
        after = new_sheet.cells.get(address)
        subject = f"{new_sheet.name}!{address}"
        if before is None:
            risk = RiskLevel.MEDIUM if after and after.formula else RiskLevel.LOW
            evidence = _cell_impact_evidence(new_workbook, new_sheet.name, address)
            changes.append(
                _make_change(
                    "cell_added",
                    subject,
                    None,
                    after.display_value() if after else None,
                    risk,
                    "A formula cell was added."
                    if after and after.formula
                    else "A cell value was added.",
                    impact_evidence=evidence,
                )
            )
            continue
        if after is None:
            risk = RiskLevel.HIGH if before.formula else RiskLevel.MEDIUM
            evidence = _cell_impact_evidence(old_workbook, old_sheet.name, address)
            changes.append(
                _make_change(
                    "cell_removed",
                    subject,
                    before.display_value(),
                    None,
                    risk,
                    "A formula cell was removed."
                    if before.formula
                    else "A cell value was removed.",
                    impact_evidence=evidence,
                )
            )
            continue
        if before.formula != after.formula:
            evidence = _cell_impact_evidence(new_workbook, new_sheet.name, address)
            if (
                before.formula
                and after.formula
                and before.formula_normalized == after.formula_normalized
            ):
                changes.append(
                    _make_change(
                        "formula_formatting_changed",
                        subject,
                        before.formula,
                        after.formula,
                        RiskLevel.LOW,
                        "Formula text changed only in conservative function-casing normalization.",
                        impact_evidence=evidence,
                    )
                )
            else:
                changes.append(
                    _make_change(
                        "formula_changed",
                        subject,
                        before.formula,
                        after.formula,
                        RiskLevel.HIGH,
                        "A formula changed; formula results are not calculated by XLSX-Ray.",
                        impact_evidence=evidence,
                    )
                )
        elif before.formula is None and after.formula is None and before.value != after.value:
            changes.append(
                _make_change(
                    "cell_value_changed",
                    subject,
                    before.value,
                    after.value,
                    RiskLevel.LOW,
                    "A non-formula cell value changed.",
                    impact_evidence=_cell_impact_evidence(new_workbook, new_sheet.name, address),
                )
            )
    return changes


def _compare_sheet_facts(old_sheet: WorksheetFact, new_sheet: WorksheetFact) -> list[Change]:
    changes: list[Change] = []
    if old_sheet.data_validations != new_sheet.data_validations:
        before = list(old_sheet.data_validations)
        after = list(new_sheet.data_validations)
        risk = RiskLevel.HIGH if len(after) < len(before) else RiskLevel.MEDIUM
        reason = (
            "A data-validation rule was removed or replaced."
            if risk is RiskLevel.HIGH
            else "A data-validation rule was added or changed."
        )
        changes.append(
            _make_change("data_validation_changed", new_sheet.name, before, after, risk, reason)
        )
    if old_sheet.protection != new_sheet.protection:
        before = old_sheet.protection
        after = new_sheet.protection
        risk = RiskLevel.HIGH if before and not after else RiskLevel.MEDIUM
        reason = (
            "Worksheet protection was removed."
            if risk is RiskLevel.HIGH
            else "Worksheet protection changed."
        )
        changes.append(
            _make_change(
                "worksheet_protection_changed", new_sheet.name, before, after, risk, reason
            )
        )
    return changes


def _defined_name_impact_evidence(
    before: DefinedNameFact | None,
    after: DefinedNameFact | None,
    old: WorkbookFact,
    new: WorkbookFact,
) -> tuple[ImpactEvidence, ...]:
    evidence: list[ImpactEvidence] = []
    if before is not None:
        evidence.extend(_defined_name_usage_evidence(old, before))
    if after is not None:
        evidence.extend(_defined_name_usage_evidence(new, after))
    return tuple(sorted(set(evidence), key=_evidence_sort_key))


def _compare_defined_names(old: WorkbookFact, new: WorkbookFact) -> list[Change]:
    changes: list[Change] = []
    keys = sorted(
        set(old.defined_names) | set(new.defined_names),
        key=lambda key: (key[0].casefold(), key[1] is not None, key[1] or ""),
    )
    for key in keys:
        before = old.defined_names.get(key)
        after = new.defined_names.get(key)
        subject = key[0] if key[1] is None else f"{key[0]} (localSheetId={key[1]})"
        evidence = _defined_name_impact_evidence(before, after, old, new)
        if before is None:
            changes.append(
                _make_change(
                    "defined_name_added",
                    subject,
                    None,
                    after.value if after else None,
                    RiskLevel.MEDIUM,
                    "A defined name was added.",
                    impact_evidence=evidence,
                )
            )
        elif after is None:
            changes.append(
                _make_change(
                    "defined_name_removed",
                    subject,
                    before.value,
                    None,
                    RiskLevel.HIGH,
                    "A defined name was removed.",
                    impact_evidence=evidence,
                )
            )
        elif before.value != after.value:
            changes.append(
                _make_change(
                    "defined_name_changed",
                    subject,
                    before.value,
                    after.value,
                    RiskLevel.HIGH,
                    "A defined name reference changed.",
                    impact_evidence=evidence,
                )
            )
    return changes


def compare_workbooks(old: WorkbookFact, new: WorkbookFact) -> tuple[Change, ...]:
    """Return a stable sequence of explainable workbook differences."""

    changes: list[Change] = []
    renames = _sheet_rename_pairs(old, new)
    rename_old = {old_name for old_name, _ in renames}
    rename_new = {new_name for _, new_name in renames}
    for old_name, new_name in renames:
        changes.append(
            _make_change(
                "sheet_renamed",
                old_name,
                old_name,
                new_name,
                RiskLevel.MEDIUM,
                "A worksheet name changed while its OOXML worksheet part was retained.",
            )
        )

    for name in sorted(set(old.sheets) - set(new.sheets) - rename_old):
        changes.append(
            _make_change(
                "sheet_removed", name, name, None, RiskLevel.HIGH, "A worksheet was removed."
            )
        )
    for name in sorted(set(new.sheets) - set(old.sheets) - rename_new):
        changes.append(
            _make_change("sheet_added", name, None, name, RiskLevel.LOW, "A worksheet was added.")
        )

    common_names = sorted(set(old.sheets) & set(new.sheets))
    for old_name, new_name in renames:
        old_sheet = old.sheets[old_name]
        new_sheet = new.sheets[new_name]
        changes.extend(_compare_cells(old_sheet, new_sheet, old, new))
        changes.extend(_compare_sheet_facts(old_sheet, new_sheet))
    for name in common_names:
        changes.extend(_compare_cells(old.sheets[name], new.sheets[name], old, new))
        changes.extend(_compare_sheet_facts(old.sheets[name], new.sheets[name]))

    changes.extend(_compare_defined_names(old, new))

    old_links, new_links = set(old.external_links), set(new.external_links)
    for link in sorted(new_links - old_links):
        changes.append(
            _make_change(
                "external_link_added",
                link,
                None,
                link,
                RiskLevel.HIGH,
                "An external workbook link was introduced.",
            )
        )
    for link in sorted(old_links - new_links):
        changes.append(
            _make_change(
                "external_link_removed",
                link,
                link,
                None,
                RiskLevel.MEDIUM,
                "An external workbook link was removed.",
            )
        )

    if old.workbook_protection != new.workbook_protection:
        risk = (
            RiskLevel.HIGH
            if old.workbook_protection and not new.workbook_protection
            else RiskLevel.MEDIUM
        )
        reason = (
            "Workbook protection was removed."
            if risk is RiskLevel.HIGH
            else "Workbook protection changed."
        )
        changes.append(
            _make_change(
                "workbook_protection_changed",
                "workbook",
                old.workbook_protection,
                new.workbook_protection,
                risk,
                reason,
            )
        )

    if old.has_vba != new.has_vba:
        changes.append(
            _make_change(
                "vba_presence_changed",
                "xl/vbaProject.bin",
                old.has_vba,
                new.has_vba,
                RiskLevel.HIGH,
                "VBA package presence changed. XLSX-Ray never executes VBA.",
            )
        )

    return tuple(
        sorted(changes, key=lambda change: (change.risk * -1, change.category, change.subject))
    )
