"""Evidence-only named-reference and static range-overlap regression tests."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.workbook.defined_name import DefinedName

from tests.support import SheetSpec, WorkbookSpec, write_workbook
from xlsx_ray.diff import compare_workbooks
from xlsx_ray.inspector import inspect_workbook
from xlsx_ray.render import render_diff_markdown


def _changes(old_path: Path, new_path: Path):
    return compare_workbooks(inspect_workbook(old_path), inspect_workbook(new_path))


def _change(changes, subject: str):
    return next(change for change in changes if change.subject == subject)


def test_changed_cell_reports_static_range_and_defined_name_leads(tmp_path: Path) -> None:
    old_path, new_path = tmp_path / "old.xlsx", tmp_path / "new.xlsx"
    shared_sheets = [
        SheetSpec(
            name="Input Sheet",
            part="xl/worksheets/sheet1.xml",
            cells={"B7": ("1", "=1", None)},
        ),
        SheetSpec(
            name="Model",
            part="xl/worksheets/sheet2.xml",
            cells={
                "C1": ("1", "=SUM('Input Sheet'!$B$2:$B$10)", None),
                "C2": ("1", "=input_band", None),
                "C3": ("1", '="input_band and B7 are literal text"', None),
                "C4": ("1", "=SUM('Input Sheet'!$B$11:$B$20)", None),
            },
        ),
    ]
    names = [("Input_Band", "'Input Sheet'!$B$2:$B$10", None)]
    write_workbook(old_path, WorkbookSpec(sheets=shared_sheets, defined_names=names))
    shared_sheets[0].cells["B7"] = ("2", "=2", None)
    write_workbook(new_path, WorkbookSpec(sheets=shared_sheets, defined_names=names))

    changed = _change(_changes(old_path, new_path), "Input Sheet!B7")
    assert changed.impact == ("Model!C1", "Model!C2")
    assert [
        (item.formula_cell, item.kind, item.reference, item.resolved_range)
        for item in changed.impact_evidence
    ] == [
        (
            "Model!C1",
            "range_overlap",
            "'Input Sheet'!$B$2:$B$10",
            "Input Sheet!$B$2:$B$10",
        ),
        ("Model!C2", "defined_name", "Input_Band", "Input Sheet!$B$2:$B$10"),
    ]
    assert all("review evidence only" in item.reason for item in changed.impact_evidence)


def test_local_name_shadows_workbook_name_only_on_its_own_sheet(tmp_path: Path) -> None:
    old_path, new_path = tmp_path / "old.xlsx", tmp_path / "new.xlsx"
    base = WorkbookSpec(
        sheets=[
            SheetSpec(
                name="Inputs",
                part="xl/worksheets/sheet1.xml",
                cells={"A1": ("1", "=1", None), "B1": ("1", "=quota", None)},
            ),
            SheetSpec(
                name="Shared",
                part="xl/worksheets/sheet2.xml",
                cells={"A1": ("1", "=1", None)},
            ),
            SheetSpec(
                name="Model",
                part="xl/worksheets/sheet3.xml",
                cells={"B1": ("1", "=Quota", None)},
            ),
        ],
        defined_names=[
            ("Quota", "'Shared'!$A$1", None),
            ("Quota", "'Inputs'!$A$1", "0"),
        ],
    )
    write_workbook(old_path, base)
    base.sheets[0].cells["A1"] = ("2", "=2", None)
    write_workbook(new_path, base)

    changed = _change(_changes(old_path, new_path), "Inputs!A1")
    assert changed.impact == ("Inputs!B1",)
    assert changed.impact_evidence[0].kind == "defined_name"
    assert changed.impact_evidence[0].formula_cell == "Inputs!B1"
    assert changed.impact_evidence[0].resolved_range == "Inputs!$A$1"


def test_changed_defined_name_reports_users_before_and_after_target_change(tmp_path: Path) -> None:
    old_path, new_path = tmp_path / "old.xlsx", tmp_path / "new.xlsx"
    sheets = [
        SheetSpec(
            name="Inputs",
            part="xl/worksheets/sheet1.xml",
            cells={"A1": ("1", "=1", None), "A2": ("2", "=2", None)},
        ),
        SheetSpec(
            name="Model",
            part="xl/worksheets/sheet2.xml",
            cells={"B1": ("1", "=LIMIT", None), "B2": ("1", '=INDIRECT("Limit")', None)},
        ),
    ]
    write_workbook(
        old_path,
        WorkbookSpec(sheets=sheets, defined_names=[("Limit", "'Inputs'!$A$1", None)]),
    )
    write_workbook(
        new_path,
        WorkbookSpec(sheets=sheets, defined_names=[("Limit", "'Inputs'!$A$2", None)]),
    )

    changed = _change(_changes(old_path, new_path), "Limit")
    assert changed.category == "defined_name_changed"
    assert changed.impact == ("Model!B1",)
    assert [item.resolved_range for item in changed.impact_evidence] == [
        "Inputs!$A$1",
        "Inputs!$A$2",
    ]
    assert all(item.formula_cell == "Model!B1" for item in changed.impact_evidence)


def test_cross_sheet_range_overlap_is_inclusive_but_nonoverlap_is_not_reported(
    tmp_path: Path,
) -> None:
    old_path, new_path = tmp_path / "old.xlsx", tmp_path / "new.xlsx"
    sheets = [
        SheetSpec(
            name="Data Sheet",
            part="xl/worksheets/sheet1.xml",
            cells={"C4": ("1", "=1", None)},
        ),
        SheetSpec(
            name="Model",
            part="xl/worksheets/sheet2.xml",
            cells={
                "A1": ("1", "=SUM('Data Sheet'!$C$2:$C$4)", None),
                "A2": ("1", "=SUM('Data Sheet'!$C$5:$C$8)", None),
                "A3": ("1", "=SUM('Data Sheet'!$B$4:$B$8)", None),
            },
        ),
    ]
    write_workbook(old_path, WorkbookSpec(sheets=sheets))
    sheets[0].cells["C4"] = ("2", "=2", None)
    write_workbook(new_path, WorkbookSpec(sheets=sheets))

    changed = _change(_changes(old_path, new_path), "Data Sheet!C4")
    assert changed.impact == ("Model!A1",)
    evidence = changed.impact_evidence[0]
    assert evidence.kind == "range_overlap"
    assert evidence.resolved_range == "Data Sheet!$C$2:$C$4"


def test_unsupported_constructs_and_name_like_literals_do_not_create_leads(tmp_path: Path) -> None:
    old_path, new_path = tmp_path / "old.xlsx", tmp_path / "new.xlsx"
    sheets = [
        SheetSpec(
            name="Inputs",
            part="xl/worksheets/sheet1.xml",
            cells={"A1": ("1", "=1", None)},
        ),
        SheetSpec(
            name="Model",
            part="xl/worksheets/sheet2.xml",
            cells={
                "A1": ("1", '=INDIRECT("A1")', None),
                "A2": ("1", "=Table1[Amount]", None),
                "A3": ("1", "=Inputs:Model!A1", None),
                "A4": ("1", "=Inputs!A1#", None),
                "A5": ("1", '="Limit and Inputs!A1 are literal text"', None),
                "A6": ("1", "=DynamicLimit", None),
                "A7": ("1", "=INDIRECT(A1)", None),
            },
        ),
    ]
    names = [("DynamicLimit", "OFFSET('Inputs'!$A$1,0,0,1,1)", None)]
    write_workbook(old_path, WorkbookSpec(sheets=sheets, defined_names=names))
    sheets[0].cells["A1"] = ("2", "=2", None)
    write_workbook(new_path, WorkbookSpec(sheets=sheets, defined_names=names))

    changed = _change(_changes(old_path, new_path), "Inputs!A1")
    assert changed.impact == ()
    assert changed.impact_evidence == ()


def test_named_reference_evidence_is_stable_in_json_and_markdown(tmp_path: Path) -> None:
    old_path, new_path = tmp_path / "old.xlsx", tmp_path / "new.xlsx"
    sheets = [
        SheetSpec(
            name="Inputs",
            part="xl/worksheets/sheet1.xml",
            cells={"A1": ("1", "=1", None)},
        ),
        SheetSpec(
            name="Model",
            part="xl/worksheets/sheet2.xml",
            cells={"B1": ("1", "=Limit", None)},
        ),
    ]
    names = [("Limit", "'Inputs'!$A$1", None), ("Unused", "'Inputs'!$A$2", None)]
    write_workbook(old_path, WorkbookSpec(sheets=sheets, defined_names=names))
    sheets[0].cells["A1"] = ("2", "=2", None)
    write_workbook(new_path, WorkbookSpec(sheets=sheets, defined_names=list(reversed(names))))

    first = _changes(old_path, new_path)
    second = _changes(old_path, new_path)
    assert [change.to_dict() for change in first] == [change.to_dict() for change in second]
    changed = _change(first, "Inputs!A1")
    payload = {
        "schema_version": "0.2",
        "changes": [change.to_dict() for change in first],
    }
    assert payload["changes"][0]["impact_evidence"] or any(
        change.to_dict()["impact_evidence"] for change in first
    )
    markdown = render_diff_markdown(
        type(
            "Result",
            (),
            {
                "old_source": "old.xlsx",
                "new_source": "new.xlsx",
                "changes": first,
                "warnings": (),
                "highest_risk": None,
            },
        )()
    )
    assert "Formula impact leads" in markdown
    assert "evidence-only review hints" in markdown
    assert changed.impact == ("Model!B1",)


def _write_openpyxl_workbook(path: Path, input_formula: str) -> None:
    workbook = Workbook()
    inputs = workbook.active
    inputs.title = "Inputs"
    inputs["A1"] = input_formula
    model = workbook.create_sheet("Model")
    model["B1"] = "=SUM(InputBand)"
    workbook.defined_names.add(DefinedName("InputBand", attr_text="'Inputs'!$A$1:$A$3"))
    workbook.save(path)


def test_openpyxl_generated_defined_name_fixture_reports_impact(tmp_path: Path) -> None:
    old_path, new_path = tmp_path / "old-openpyxl.xlsx", tmp_path / "new-openpyxl.xlsx"
    _write_openpyxl_workbook(old_path, "=1")
    _write_openpyxl_workbook(new_path, "=2")

    changed = _change(_changes(old_path, new_path), "Inputs!A1")
    assert changed.impact == ("Model!B1",)
    assert changed.impact_evidence[0].kind == "defined_name"
    assert changed.impact_evidence[0].resolved_range == "Inputs!$A$1:$A$3"
