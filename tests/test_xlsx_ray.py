from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from tests.support import SheetSpec, WorkbookSpec, write_workbook
from xlsx_ray.audit import audit_workbook
from xlsx_ray.cli import main
from xlsx_ray.diff import compare_workbooks
from xlsx_ray.inspector import WorkbookInspectionError, inspect_workbook
from xlsx_ray.models import RiskLevel
from xlsx_ray.render import render_diff_markdown


def _old_spec() -> WorkbookSpec:
    return WorkbookSpec(
        sheets=[
            SheetSpec(
                name="Inputs",
                part="xl/worksheets/sheet1.xml",
                cells={"A1": ("10", None, None), "B1": ("approved", None, "inlineStr")},
                validations=[
                    {
                        "sqref": "A1",
                        "type": "whole",
                        "operator": "between",
                        "formula1": "1",
                        "formula2": "100",
                    }
                ],
                protection={"sheet": "1", "objects": "1"},
            ),
            SheetSpec(
                name="Model",
                part="xl/worksheets/sheet2.xml",
                cells={"B2": ("20", "=Inputs!A1*2", None), "C2": ("21", "=B2+1", None)},
            ),
        ],
        defined_names=[("InputLimit", "Inputs!$A$1", None)],
        workbook_protection={"lockStructure": "1"},
    )


def _new_spec() -> WorkbookSpec:
    return WorkbookSpec(
        sheets=[
            SheetSpec(
                name="Assumptions",
                part="xl/worksheets/sheet1.xml",
                cells={"A1": ("12", None, None), "B1": ("approved", None, "inlineStr")},
                validations=[],
                protection={},
            ),
            SheetSpec(
                name="Model",
                part="xl/worksheets/sheet2.xml",
                cells={"B2": ("24", "=Assumptions!A1*2", None), "C2": ("25", "=B2+1", None)},
            ),
            SheetSpec(
                name="Notes",
                part="xl/worksheets/sheet3.xml",
                cells={"A1": ("review", None, "inlineStr")},
            ),
        ],
        defined_names=[("InputLimit", "Assumptions!$A$1", None)],
        workbook_protection={},
        external_links=["https://example.invalid/external.xlsx"],
        has_vba=True,
        charts=True,
    )


def test_diff_captures_workbook_wide_risk_evidence(tmp_path: Path) -> None:
    old_path, new_path = tmp_path / "old.xlsx", tmp_path / "new.xlsm"
    write_workbook(old_path, _old_spec())
    write_workbook(new_path, _new_spec())

    old, new = inspect_workbook(old_path), inspect_workbook(new_path)
    result = compare_workbooks(old, new)
    changes = {change.category: change for change in result}

    assert changes["sheet_renamed"].before == "Inputs"
    assert changes["sheet_renamed"].after == "Assumptions"
    assert changes["formula_changed"].subject == "Model!B2"
    assert changes["formula_changed"].risk is RiskLevel.HIGH
    assert changes["formula_changed"].impact == ("Model!C2",)
    assert changes["data_validation_changed"].risk is RiskLevel.HIGH
    assert changes["worksheet_protection_changed"].risk is RiskLevel.HIGH
    assert changes["workbook_protection_changed"].risk is RiskLevel.HIGH
    assert changes["external_link_added"].risk is RiskLevel.HIGH
    assert changes["vba_presence_changed"].before is False
    assert changes["vba_presence_changed"].after is True
    assert changes["defined_name_changed"].risk is RiskLevel.HIGH
    assert changes["cell_value_changed"].subject == "Assumptions!A1"
    assert "charts are present but not interpreted" in new.unsupported_features


def test_formula_formatting_change_is_low_risk(tmp_path: Path) -> None:
    old_path, new_path = tmp_path / "old.xlsx", tmp_path / "new.xlsx"
    old = WorkbookSpec(
        sheets=[
            SheetSpec(
                name="Model",
                part="xl/worksheets/sheet1.xml",
                cells={"A1": ("2", "=SUM(B1:B2)", None)},
            )
        ]
    )
    new = WorkbookSpec(
        sheets=[
            SheetSpec(
                name="Model",
                part="xl/worksheets/sheet1.xml",
                cells={"A1": ("2", "= sum( B1:B2 )", None)},
            )
        ]
    )
    write_workbook(old_path, old)
    write_workbook(new_path, new)

    changes = compare_workbooks(inspect_workbook(old_path), inspect_workbook(new_path))
    assert len(changes) == 1
    assert changes[0].category == "formula_formatting_changed"
    assert changes[0].risk is RiskLevel.LOW


def test_defined_name_and_sheet_removal_are_high_risk(tmp_path: Path) -> None:
    old_path, new_path = tmp_path / "old.xlsx", tmp_path / "new.xlsx"
    write_workbook(
        old_path,
        WorkbookSpec(
            sheets=[SheetSpec(name="Important", part="xl/worksheets/sheet1.xml")],
            defined_names=[("Threshold", "Important!$A$1", None)],
        ),
    )
    write_workbook(new_path, WorkbookSpec(sheets=[]))

    changes = {
        change.category: change
        for change in compare_workbooks(inspect_workbook(old_path), inspect_workbook(new_path))
    }
    assert changes["sheet_removed"].risk is RiskLevel.HIGH
    assert changes["defined_name_removed"].risk is RiskLevel.HIGH


def test_audit_is_presence_based_and_never_executes_vba(tmp_path: Path) -> None:
    path = tmp_path / "macro.xlsm"
    write_workbook(
        path,
        WorkbookSpec(
            sheets=[SheetSpec(name="Sheet1", part="xl/worksheets/sheet1.xml")],
            has_vba=True,
            external_links=["https://example.invalid/external.xlsx"],
        ),
    )
    audit = audit_workbook(inspect_workbook(path))
    categories = {finding.category for finding in audit.findings}
    assert {
        "vba_present",
        "external_link_present",
        "workbook_protection_absent",
        "worksheet_protection_absent",
    } <= categories
    assert audit.highest_risk is RiskLevel.HIGH


def test_cli_json_and_fail_threshold(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    old_path, new_path = tmp_path / "old.xlsx", tmp_path / "new.xlsm"
    write_workbook(old_path, _old_spec())
    write_workbook(new_path, _new_spec())

    code = main(["diff", str(old_path), str(new_path), "--format", "json", "--fail-on", "high"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 1
    assert payload["summary"]["highest_risk"] == "high"
    assert any(change["category"] == "vba_presence_changed" for change in payload["changes"])


def test_cli_output_file_and_markdown(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "audit.xlsx"
    output = tmp_path / "reports" / "audit.md"
    write_workbook(
        path, WorkbookSpec(sheets=[SheetSpec(name="Sheet1", part="xl/worksheets/sheet1.xml")])
    )

    code = main(["audit", str(path), "--output", str(output)])
    assert code == 0
    assert capsys.readouterr().out == ""
    text = output.read_text(encoding="utf-8")
    assert "# XLSX-Ray workbook audit" in text
    assert "worksheet_protection_absent" in text


def test_malformed_xml_is_reported_safely(tmp_path: Path) -> None:
    path = tmp_path / "broken.xlsx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", "<workbook>")
    with pytest.raises(WorkbookInspectionError, match="malformed XML"):
        inspect_workbook(path)


def test_zip_path_traversal_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "unsafe.xlsx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", "<workbook/>")
        archive.writestr("../unsafe.xml", "not used")
    with pytest.raises(WorkbookInspectionError, match="unsafe ZIP member"):
        inspect_workbook(path)


def test_xml_entity_declaration_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "entity.xlsx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr(
            "xl/workbook.xml",
            "<!DOCTYPE workbook [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><workbook/>",
        )
    with pytest.raises(WorkbookInspectionError, match="unsafe XML"):
        inspect_workbook(path)


def test_markdown_is_review_focused_and_deterministic(tmp_path: Path) -> None:
    old_path, new_path = tmp_path / "old.xlsx", tmp_path / "new.xlsx"
    write_workbook(old_path, _old_spec())
    write_workbook(new_path, _new_spec())
    old, new = inspect_workbook(old_path), inspect_workbook(new_path)
    from xlsx_ray.models import DiffResult

    result = DiffResult(
        old.source,
        new.source,
        compare_workbooks(old, new),
        warnings=tuple(sorted(set(old.warnings + new.warnings))),
    )
    markdown = render_diff_markdown(result)
    assert "# XLSX-Ray workbook diff" in markdown
    assert "`formula_changed`" in markdown
    assert "Direct formula dependents" in markdown
    assert "does not calculate formulas" in markdown


def test_unchanged_formula_ignores_cached_value_delta(tmp_path: Path) -> None:
    old_path, new_path = tmp_path / "old.xlsx", tmp_path / "new.xlsx"
    old = WorkbookSpec(
        sheets=[
            SheetSpec(
                name="Model",
                part="xl/worksheets/sheet1.xml",
                cells={"A1": ("2", "=1+1", None)},
            )
        ]
    )
    new = WorkbookSpec(
        sheets=[
            SheetSpec(
                name="Model",
                part="xl/worksheets/sheet1.xml",
                cells={"A1": ("999", "=1+1", None)},
            )
        ]
    )
    write_workbook(old_path, old)
    write_workbook(new_path, new)

    assert compare_workbooks(inspect_workbook(old_path), inspect_workbook(new_path)) == ()


def test_action_manifest_exposes_local_read_only_report_workflow() -> None:
    manifest = (Path(__file__).parents[1] / "action.yml").read_text(encoding="utf-8")
    assert "using: composite" in manifest
    assert "xlsx-ray diff" in manifest
    assert "GITHUB_STEP_SUMMARY" in manifest
    assert "markdown-report" in manifest
    assert "json-report" in manifest
