from __future__ import annotations

import json
from pathlib import Path

from tests.support import SheetSpec, WorkbookSpec, write_workbook
from xlsx_ray.cli import main


def test_diff_writes_markdown_and_json_from_one_cli_run(tmp_path: Path) -> None:
    old_path = tmp_path / "old.xlsx"
    new_path = tmp_path / "new.xlsx"
    markdown_path = tmp_path / "reports" / "xlsx-ray.md"
    json_path = tmp_path / "reports" / "xlsx-ray.json"
    write_workbook(
        old_path,
        WorkbookSpec(
            sheets=[
                SheetSpec(
                    name="Model",
                    part="xl/worksheets/sheet1.xml",
                    cells={"A1": ("1", "=1", None)},
                )
            ]
        ),
    )
    write_workbook(
        new_path,
        WorkbookSpec(
            sheets=[
                SheetSpec(
                    name="Model",
                    part="xl/worksheets/sheet1.xml",
                    cells={"A1": ("2", "=2", None)},
                )
            ]
        ),
    )

    code = main(
        [
            "diff",
            str(old_path),
            str(new_path),
            "--output",
            str(markdown_path),
            "--json-output",
            str(json_path),
            "--fail-on",
            "high",
        ]
    )

    assert code == 1
    assert "# XLSX-Ray workbook diff" in markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "0.2"
    assert payload["summary"]["highest_risk"] == "high"


def test_audit_can_write_secondary_json_report(tmp_path: Path) -> None:
    workbook_path = tmp_path / "book.xlsx"
    markdown_path = tmp_path / "audit.md"
    json_path = tmp_path / "audit.json"
    write_workbook(
        workbook_path,
        WorkbookSpec(sheets=[SheetSpec(name="Sheet1", part="xl/worksheets/sheet1.xml")]),
    )

    code = main(
        [
            "audit",
            str(workbook_path),
            "--output",
            str(markdown_path),
            "--json-output",
            str(json_path),
        ]
    )

    assert code == 0
    assert "# XLSX-Ray workbook audit" in markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "0.1"


def test_composite_action_runs_diff_once() -> None:
    manifest = (Path(__file__).parents[1] / "action.yml").read_text(encoding="utf-8")
    assert manifest.count("xlsx-ray diff") == 1
    assert "--json-output" in manifest
