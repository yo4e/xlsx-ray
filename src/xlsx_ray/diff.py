"""Deterministic comparison and explainable risk classification for workbook facts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from .formulas import canonical_reference, extract_references
from .models import Change, RiskLevel, WorkbookFact, WorksheetFact


def _make_change(
    category: str,
    subject: str,
    before: Any,
    after: Any,
    risk: RiskLevel,
    reason: str,
    impact: Iterable[str] = (),
) -> Change:
    return Change(
        category=category,
        subject=subject,
        before=before,
        after=after,
        risk=risk,
        reason=reason,
        impact=tuple(sorted(set(impact))),
    )


def _sheet_rename_pairs(old: WorkbookFact, new: WorkbookFact) -> list[tuple[str, str]]:
    """Conservatively identify a rename when an OOXML worksheet part is retained.

    A rename is high confidence only when exactly one removed and one added
    sheet share the same worksheet part. Ambiguous cases remain add/remove
    events rather than making an unsupported identity claim.
    """

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


def _dependency_index(workbook: WorkbookFact) -> dict[str, set[str]]:
    """Index direct textual A1 references for evidence, not calculation semantics."""

    index: dict[str, set[str]] = defaultdict(set)
    for sheet_name, sheet in workbook.sheets.items():
        for address, cell in sheet.cells.items():
            if not cell.formula:
                continue
            target = f"{sheet_name}!{address}"
            for reference in extract_references(cell.formula):
                canonical = canonical_reference(reference, sheet_name)
                if canonical is not None:
                    index[canonical].add(target)
    return index


def _direct_impact(workbook: WorkbookFact, sheet_name: str, address: str) -> tuple[str, ...]:
    key = canonical_reference(address, sheet_name)
    if key is None:
        return ()
    return tuple(sorted(_dependency_index(workbook).get(key, set())))


def _compare_cells(
    old_sheet: WorksheetFact, new_sheet: WorksheetFact, new_workbook: WorkbookFact
) -> list[Change]:
    changes: list[Change] = []
    addresses = sorted(set(old_sheet.cells) | set(new_sheet.cells))
    for address in addresses:
        before = old_sheet.cells.get(address)
        after = new_sheet.cells.get(address)
        subject = f"{new_sheet.name}!{address}"
        if before is None:
            risk = RiskLevel.MEDIUM if after and after.formula else RiskLevel.LOW
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
                    _direct_impact(new_workbook, new_sheet.name, address)
                    if after and after.formula
                    else (),
                )
            )
            continue
        if after is None:
            risk = RiskLevel.HIGH if before.formula else RiskLevel.MEDIUM
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
                )
            )
            continue
        if before.formula != after.formula:
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
                        "Formula text changed only in conservative whitespace/function-casing normalization.",
                        _direct_impact(new_workbook, new_sheet.name, address),
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
                        _direct_impact(new_workbook, new_sheet.name, address),
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


def _compare_defined_names(old: WorkbookFact, new: WorkbookFact) -> list[Change]:
    changes: list[Change] = []
    keys = sorted(set(old.defined_names) | set(new.defined_names))
    for key in keys:
        before = old.defined_names.get(key)
        after = new.defined_names.get(key)
        subject = key[0] if key[1] is None else f"{key[0]} (localSheetId={key[1]})"
        if before is None:
            changes.append(
                _make_change(
                    "defined_name_added",
                    subject,
                    None,
                    after.value if after else None,
                    RiskLevel.MEDIUM,
                    "A defined name was added.",
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
                )
            )
    return changes


def compare_workbooks(old: WorkbookFact, new: WorkbookFact) -> tuple[Change, ...]:
    """Return a stable sequence of explainable differences."""

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
        # The part identity permits content comparison even though the display name changed.
        old_sheet = old.sheets[old_name]
        new_sheet = new.sheets[new_name]
        changes.extend(_compare_cells(old_sheet, new_sheet, new))
        changes.extend(_compare_sheet_facts(old_sheet, new_sheet))
    for name in common_names:
        changes.extend(_compare_cells(old.sheets[name], new.sheets[name], new))
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
