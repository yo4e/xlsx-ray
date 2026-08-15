from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from openpyxl import Workbook
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

from tests.support import SheetSpec, WorkbookSpec, write_workbook
from xlsx_ray.cli import main
from xlsx_ray.diff import compare_workbooks
from xlsx_ray.formulas import canonical_reference, extract_references, normalize_formula
from xlsx_ray.inspector import WorkbookInspectionError, inspect_workbook
from xlsx_ray.models import DiffResult

SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
PACKAGE_RELATIONSHIP_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
RELATIONSHIP_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _write_raw_package(path: Path, workbook_xml: str, relationships_xml: str = "") -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", workbook_xml)
        if relationships_xml:
            archive.writestr("xl/_rels/workbook.xml.rels", relationships_xml)


def _workbook_xml(sheets: str = "") -> str:
    return (
        f'<workbook xmlns="{SPREADSHEET_NS}" xmlns:r="{RELATIONSHIP_NS}">'
        f"<sheets>{sheets}</sheets></workbook>"
    )


def _relationships_xml(entries: str) -> str:
    return f'<Relationships xmlns="{PACKAGE_RELATIONSHIP_NS}">{entries}</Relationships>'


def test_formula_normalization_preserves_string_literal_whitespace_and_casing() -> None:
    formula = '=if(A1="sum (b2)  ", sum ( $B$1 : B2 ))'
    assert normalize_formula(formula) == '=IF(A1="sum (b2)  ", SUM ( $B$1 : B2 ))'
    assert normalize_formula("=A1 B1") != normalize_formula("=A1B1")


def test_reference_extraction_ignores_string_literals_and_handles_quoted_sheet_names() -> None:
    formula = "=IF(A1=\"B2 and Z99\",SUM($B$1:B2,'Input Sheet'!$C$3))"
    assert extract_references(formula) == ("A1", "$B$1:B2", "Input Sheet!$C$3")
    assert canonical_reference("$B$1:B2", "Model") == "model!B1:B2"
    assert canonical_reference("Input Sheet!$C$3", "Model") == "input sheet!C3"


def test_formula_impact_matches_absolute_case_and_quoted_sheet_references(tmp_path: Path) -> None:
    old_path, new_path = tmp_path / "old.xlsx", tmp_path / "new.xlsx"
    old = WorkbookSpec(
        sheets=[
            SheetSpec(
                name="Input Sheet", part="xl/worksheets/sheet1.xml", cells={"A1": ("1", "=1", None)}
            ),
            SheetSpec(
                name="Model",
                part="xl/worksheets/sheet2.xml",
                cells={"B1": ("1", "='Input Sheet'!$A$1", None)},
            ),
        ]
    )
    new = WorkbookSpec(
        sheets=[
            SheetSpec(
                name="Input Sheet", part="xl/worksheets/sheet1.xml", cells={"A1": ("2", "=2", None)}
            ),
            SheetSpec(
                name="Model",
                part="xl/worksheets/sheet2.xml",
                cells={"B1": ("2", "='Input Sheet'!$A$1", None)},
            ),
        ]
    )
    write_workbook(old_path, old)
    write_workbook(new_path, new)

    changes = compare_workbooks(inspect_workbook(old_path), inspect_workbook(new_path))
    changed = next(change for change in changes if change.subject == "Input Sheet!A1")
    assert changed.category == "formula_changed"
    assert changed.impact == ("Model!B1",)


def test_reordered_data_validations_do_not_produce_a_diff(tmp_path: Path) -> None:
    old_path, new_path = tmp_path / "old.xlsx", tmp_path / "new.xlsx"
    first = {
        "sqref": "A1",
        "type": "whole",
        "operator": "between",
        "formula1": "1",
        "formula2": "5",
    }
    second = {"sqref": "B1", "type": "list", "formula1": '"yes,no"'}
    write_workbook(
        old_path,
        WorkbookSpec(
            sheets=[
                SheetSpec(
                    name="Input", part="xl/worksheets/sheet1.xml", validations=[first, second]
                )
            ]
        ),
    )
    write_workbook(
        new_path,
        WorkbookSpec(
            sheets=[
                SheetSpec(
                    name="Input", part="xl/worksheets/sheet1.xml", validations=[second, first]
                )
            ]
        ),
    )
    assert compare_workbooks(inspect_workbook(old_path), inspect_workbook(new_path)) == ()


def test_openpyxl_generated_workbook_is_inspected(tmp_path: Path) -> None:
    path = tmp_path / "openpyxl.xlsx"
    workbook = Workbook()
    inputs = workbook.active
    inputs.title = "Inputs"
    inputs["A1"] = 12
    validation = DataValidation(type="whole", operator="between", formula1="1", formula2="100")
    inputs.add_data_validation(validation)
    validation.add(inputs["A1"])
    inputs.protection.sheet = True
    model = workbook.create_sheet("Model")
    model["B2"] = "=Inputs!$A$1*2"
    workbook.defined_names.add(DefinedName("InputLimit", attr_text="Inputs!$A$1"))
    workbook.security.lockStructure = True
    workbook.save(path)

    fact = inspect_workbook(path)
    assert fact.sheets["Inputs"].cells["A1"].value == "12"
    assert fact.sheets["Model"].cells["B2"].formula == "=Inputs!$A$1*2"
    assert fact.defined_names[("InputLimit", None)].value == "Inputs!$A$1"
    assert fact.sheets["Inputs"].data_validations
    assert fact.sheets["Inputs"].protection["sheet"] == "1"
    assert fact.workbook_protection["lockStructure"] == "1"


def test_duplicate_zip_member_names_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.xlsx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        with pytest.warns(UserWarning, match="Duplicate name"):
            archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", _workbook_xml())
    with pytest.raises(WorkbookInspectionError, match="duplicate ZIP member"):
        inspect_workbook(path)


@pytest.mark.parametrize(
    "member", ["xl\\unsafe.xml", "C:unsafe.xml", "/absolute.xml", "folder//empty.xml"]
)
def test_ambiguous_zip_member_names_are_rejected(tmp_path: Path, member: str) -> None:
    path = tmp_path / "unsafe.xlsx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", _workbook_xml())
        archive.writestr(member, "unused")
    with pytest.raises(WorkbookInspectionError, match="unsafe ZIP member"):
        inspect_workbook(path)


def test_unsafe_worksheet_relationship_target_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "unsafe-target.xlsx"
    sheets = '<sheet name="Inputs" sheetId="1" r:id="rId1"/>'
    relationships = _relationships_xml(
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="../../outside.xml"/>'
    )
    _write_raw_package(path, _workbook_xml(sheets), relationships)
    with pytest.raises(WorkbookInspectionError, match="unsafe worksheet relationship target"):
        inspect_workbook(path)


def test_unresolved_worksheet_relationship_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "missing-relationship.xlsx"
    _write_raw_package(path, _workbook_xml('<sheet name="Inputs" sheetId="1" r:id="missing"/>'))
    with pytest.raises(WorkbookInspectionError, match="could not resolve worksheet relationship"):
        inspect_workbook(path)


def test_unexpected_workbook_namespace_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "namespace.xlsx"
    _write_raw_package(path, '<workbook xmlns="https://example.invalid/not-ooxml"/>')
    with pytest.raises(WorkbookInspectionError, match="unexpected workbook namespace"):
        inspect_workbook(path)


def test_deep_xml_is_rejected_before_interpretation(tmp_path: Path) -> None:
    path = tmp_path / "deep.xlsx"
    deep = "<nested>" * 300 + "</nested>" * 300
    _write_raw_package(path, f'<workbook xmlns="{SPREADSHEET_NS}">{deep}</workbook>')
    with pytest.raises(WorkbookInspectionError, match="XML nesting exceeds"):
        inspect_workbook(path)


def test_suspicious_compression_ratio_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "compressed.xlsx"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", _workbook_xml())
        archive.writestr("xl/repetitive.bin", b"0" * (2 * 1024 * 1024))
    with pytest.raises(WorkbookInspectionError, match="compression ratio"):
        inspect_workbook(path)


def test_repeat_diff_json_is_deterministic(tmp_path: Path) -> None:
    old_path, new_path = tmp_path / "old.xlsx", tmp_path / "new.xlsx"
    write_workbook(
        old_path,
        WorkbookSpec(
            sheets=[
                SheetSpec(
                    name="Input", part="xl/worksheets/sheet1.xml", cells={"A1": ("1", None, None)}
                )
            ]
        ),
    )
    write_workbook(
        new_path,
        WorkbookSpec(
            sheets=[
                SheetSpec(
                    name="Input", part="xl/worksheets/sheet1.xml", cells={"A1": ("2", None, None)}
                )
            ]
        ),
    )

    first_old, first_new = inspect_workbook(old_path), inspect_workbook(new_path)
    second_old, second_new = inspect_workbook(old_path), inspect_workbook(new_path)
    first = DiffResult(first_old.source, first_new.source, compare_workbooks(first_old, first_new))
    second = DiffResult(
        second_old.source, second_new.source, compare_workbooks(second_old, second_new)
    )
    assert json.dumps(first.to_dict(), sort_keys=True) == json.dumps(
        second.to_dict(), sort_keys=True
    )


def test_cli_paths_with_spaces_and_inspection_failure_exit_codes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    directory = tmp_path / "nested path"
    directory.mkdir()
    clean = directory / "book name.xlsx"
    write_workbook(
        clean, WorkbookSpec(sheets=[SheetSpec(name="Input", part="xl/worksheets/sheet1.xml")])
    )
    assert main(["audit", str(clean), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["source"] == str(clean)

    invalid = directory / "not a workbook.xlsx"
    invalid.write_text("not a zip", encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main(["audit", str(invalid)])
    assert error.value.code == 2


def test_safe_zip_directory_entry_is_allowed(tmp_path: Path) -> None:
    path = tmp_path / "directory-entry.xlsx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", _workbook_xml())
        archive.writestr("xl/media/", b"")
    assert inspect_workbook(path).sheets == {}
