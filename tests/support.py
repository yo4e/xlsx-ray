"""Minimal reproducible OOXML fixture builder used only by tests and examples."""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape


@dataclass
class SheetSpec:
    name: str
    part: str
    cells: dict[str, tuple[str | None, str | None, str | None]] = field(default_factory=dict)
    validations: list[dict[str, str]] = field(default_factory=list)
    protection: dict[str, str] = field(default_factory=dict)


@dataclass
class WorkbookSpec:
    sheets: list[SheetSpec]
    defined_names: list[tuple[str, str, str | None]] = field(default_factory=list)
    workbook_protection: dict[str, str] = field(default_factory=dict)
    external_links: list[str] = field(default_factory=list)
    has_vba: bool = False
    charts: bool = False


def _attrs(attrs: dict[str, str]) -> str:
    escaped = {'"': "&quot;", "'": "&apos;"}
    return "".join(
        f' {key}="{escape(value, entities=escaped)}"' for key, value in sorted(attrs.items())
    )


def _worksheet_xml(spec: SheetSpec) -> str:
    rows: dict[int, list[tuple[str, tuple[str | None, str | None, str | None]]]] = {}
    for address, cell in spec.cells.items():
        number = int("".join(char for char in address if char.isdigit()))
        rows.setdefault(number, []).append((address, cell))
    rendered_rows = []
    for number in sorted(rows):
        rendered_cells = []
        for address, (value, formula, data_type) in sorted(rows[number]):
            attributes = {"r": address}
            if data_type:
                attributes["t"] = data_type
            content = ""
            if formula is not None:
                content += f"<f>{escape(formula.lstrip('='))}</f>"
            if data_type == "inlineStr":
                content += f"<is><t>{escape(value or '')}</t></is>"
            elif value is not None:
                content += f"<v>{escape(value)}</v>"
            rendered_cells.append(f"<c{_attrs(attributes)}>{content}</c>")
        rendered_rows.append(f'<row r="{number}">{"".join(rendered_cells)}</row>')
    validations = ""
    if spec.validations:
        entries = "".join(f"<dataValidation{_attrs(item)}/>" for item in spec.validations)
        validations = (
            f'<dataValidations count="{len(spec.validations)}">{entries}</dataValidations>'
        )
    protection = f"<sheetProtection{_attrs(spec.protection)}/>" if spec.protection else ""
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(rendered_rows)}</sheetData>{validations}{protection}</worksheet>"
    )


def write_workbook(path: Path, spec: WorkbookSpec) -> None:
    """Write a tiny valid OOXML package with controlled facts for a test."""

    content_types = [
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
    ]
    for sheet in spec.sheets:
        content_types.append(
            f'<Override PartName="/{sheet.part}" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    if spec.has_vba:
        content_types.append(
            '<Override PartName="/xl/vbaProject.bin" ContentType="application/vnd.ms-office.vbaProject"/>'
        )
    if spec.charts:
        content_types.append(
            '<Override PartName="/xl/charts/chart1.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.chart+xml"/>'
        )

    sheet_entries = []
    relationships = []
    for index, sheet in enumerate(spec.sheets, start=1):
        sheet_entries.append(
            f'<sheet name="{escape(sheet.name)}" sheetId="{index}" r:id="rId{index}"/>'
        )
        relationships.append(
            f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="{sheet.part.removeprefix("xl/")}"/>'
        )
    external_relationship_ids: list[tuple[str, str]] = []
    for index, target in enumerate(spec.external_links, start=len(spec.sheets) + 1):
        relationships.append(
            f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/externalLink" Target="externalLinks/externalLink{index}.xml"/>'
        )
        external_relationship_ids.append((f"xl/externalLinks/externalLink{index}.xml", target))
    defined_names = ""
    if spec.defined_names:
        nodes = []
        for name, value, local_id in spec.defined_names:
            attrs = f' name="{escape(name)}"'
            if local_id is not None:
                attrs += f' localSheetId="{escape(local_id)}"'
            nodes.append(f"<definedName{attrs}>{escape(value)}</definedName>")
        defined_names = f"<definedNames>{''.join(nodes)}</definedNames>"
    workbook_protection = (
        f"<workbookProtection{_attrs(spec.workbook_protection)}/>"
        if spec.workbook_protection
        else ""
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"{workbook_protection}<sheets>{''.join(sheet_entries)}</sheets>{defined_names}</workbook>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{''.join(relationships)}</Relationships>"
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            f"{''.join(content_types)}</Types>",
        )
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        for sheet in spec.sheets:
            archive.writestr(sheet.part, _worksheet_xml(sheet))
        for part_name, target in external_relationship_ids:
            archive.writestr(
                part_name,
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<externalLink xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>',
            )
            relationship_part = (
                part_name.rsplit("/", 1)[0] + "/_rels/" + part_name.rsplit("/", 1)[1] + ".rels"
            )
            archive.writestr(
                relationship_part,
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                f'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/externalLinkPath" Target="{escape(target)}" TargetMode="External"/>'
                "</Relationships>",
            )
        if spec.has_vba:
            archive.writestr("xl/vbaProject.bin", b"synthetic-test-vba-bytes")
        if spec.charts:
            archive.writestr(
                "xl/charts/chart1.xml",
                '<chartSpace xmlns="http://schemas.openxmlformats.org/drawingml/2006/chart"/>',
            )
