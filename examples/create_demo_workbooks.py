"""Create non-sensitive demo workbooks for README examples.

Run from the repository root:
    python examples/create_demo_workbooks.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SUPPORT_PATH = Path(__file__).parents[1] / "tests" / "support.py"
_SUPPORT_SPEC = importlib.util.spec_from_file_location("xlsx_ray_fixture_support", _SUPPORT_PATH)
if _SUPPORT_SPEC is None or _SUPPORT_SPEC.loader is None:
    raise RuntimeError(f"could not load fixture support: {_SUPPORT_PATH}")
_SUPPORT_MODULE = importlib.util.module_from_spec(_SUPPORT_SPEC)
sys.modules[_SUPPORT_SPEC.name] = _SUPPORT_MODULE
_SUPPORT_SPEC.loader.exec_module(_SUPPORT_MODULE)
SheetSpec = _SUPPORT_MODULE.SheetSpec
WorkbookSpec = _SUPPORT_MODULE.WorkbookSpec
write_workbook = _SUPPORT_MODULE.write_workbook

OUTPUT_DIRECTORY = Path(__file__).parent / "generated"


def main() -> None:
    before = WorkbookSpec(
        sheets=[
            SheetSpec(
                name="Inputs",
                part="xl/worksheets/sheet1.xml",
                cells={"A1": ("10", None, None)},
                validations=[
                    {
                        "sqref": "A1",
                        "type": "whole",
                        "operator": "between",
                        "formula1": "1",
                        "formula2": "100",
                    }
                ],
                protection={"sheet": "1"},
            ),
            SheetSpec(
                name="Model",
                part="xl/worksheets/sheet2.xml",
                cells={
                    "B2": ("20", "=Inputs!A1*2", None),
                    "C2": ("11", "=InputLimit+1", None),
                },
            ),
        ],
        defined_names=[("InputLimit", "Inputs!$A$1", None)],
        workbook_protection={"lockStructure": "1"},
    )
    after = WorkbookSpec(
        sheets=[
            SheetSpec(
                name="Assumptions",
                part="xl/worksheets/sheet1.xml",
                cells={"A1": ("12", None, None)},
                validations=[],
            ),
            SheetSpec(
                name="Model",
                part="xl/worksheets/sheet2.xml",
                cells={
                    "B2": ("24", "=Assumptions!A1*2", None),
                    "C2": ("13", "=InputLimit+1", None),
                },
            ),
        ],
        defined_names=[("InputLimit", "Assumptions!$A$1", None)],
        external_links=["https://example.invalid/external.xlsx"],
        has_vba=True,
    )
    write_workbook(OUTPUT_DIRECTORY / "before.xlsx", before)
    write_workbook(OUTPUT_DIRECTORY / "after.xlsm", after)
    print(f"Wrote {OUTPUT_DIRECTORY / 'before.xlsx'}")
    print(f"Wrote {OUTPUT_DIRECTORY / 'after.xlsm'}")


if __name__ == "__main__":
    main()
