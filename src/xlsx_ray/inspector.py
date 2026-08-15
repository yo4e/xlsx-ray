"""Safe, read-only inspection of the high-confidence OOXML facts used by v0.1.

This module does not evaluate formulas, execute VBA, open external links, or
write workbook bytes. It parses only selected XML parts of an OOXML ZIP package.
"""

from __future__ import annotations

import json
import posixpath
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .formulas import normalize_formula
from .models import CellFact, DefinedNameFact, WorkbookFact, WorksheetFact

SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RELATIONSHIP_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_RELATIONSHIP_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

NS = {"x": SPREADSHEET_NS, "r": RELATIONSHIP_NS, "pr": PACKAGE_RELATIONSHIP_NS}

MAX_MEMBERS = 4_096
MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_COMPRESSION_RATIO = 1_000
MAX_XML_PART_BYTES = 25 * 1024 * 1024


class WorkbookInspectionError(ValueError):
    """Raised for unsupported, malformed, or deliberately rejected workbooks."""


def _attribute_key(item: tuple[str, str]) -> str:
    return item[0]


def _canonical_attributes(element: ET.Element) -> dict[str, str]:
    return dict(sorted(element.attrib.items(), key=_attribute_key))


def _canonical_element(element: ET.Element) -> str:
    """Create a stable, small representation of selected XML elements."""

    payload = {
        "tag": element.tag.rsplit("}", 1)[-1],
        "attributes": _canonical_attributes(element),
        "children": [
            {
                "tag": child.tag.rsplit("}", 1)[-1],
                "attributes": _canonical_attributes(child),
                "text": (child.text or "").strip(),
            }
            for child in element
        ],
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _safe_member_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    return not normalized.startswith("/") and ".." not in normalized.split("/")


def _relationship_part_name(part_name: str) -> str:
    folder, filename = posixpath.split(part_name)
    return posixpath.join(folder, "_rels", f"{filename}.rels")


def _resolve_target(source_part: str, target: str) -> str:
    return posixpath.normpath(posixpath.join(posixpath.dirname(source_part), target))


class _OOXMLReader:
    """Bounded access wrapper around a ZIP package."""

    def __init__(self, source: str | Path):
        self.source = Path(source)
        if self.source.suffix.lower() not in {".xlsx", ".xlsm"}:
            raise WorkbookInspectionError("expected an .xlsx or .xlsm workbook")
        if not self.source.is_file():
            raise WorkbookInspectionError(f"workbook does not exist: {self.source}")
        if not zipfile.is_zipfile(self.source):
            raise WorkbookInspectionError("workbook is not a valid ZIP/OOXML package")
        self.archive = zipfile.ZipFile(self.source, "r")
        self.members = {info.filename: info for info in self.archive.infolist()}
        self._validate_archive()

    def close(self) -> None:
        self.archive.close()

    def __enter__(self) -> _OOXMLReader:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _validate_archive(self) -> None:
        infos = list(self.members.values())
        if len(infos) > MAX_MEMBERS:
            raise WorkbookInspectionError(f"archive has too many members (limit: {MAX_MEMBERS})")
        total_size = sum(info.file_size for info in infos)
        if total_size > MAX_UNCOMPRESSED_BYTES:
            raise WorkbookInspectionError(
                "archive uncompressed size exceeds the safety limit "
                f"({MAX_UNCOMPRESSED_BYTES // (1024 * 1024)} MiB)"
            )
        for info in infos:
            if not _safe_member_name(info.filename):
                raise WorkbookInspectionError(f"unsafe ZIP member path: {info.filename}")
            if info.file_size > 1024 * 1024 and info.compress_size > 0:
                ratio = info.file_size / info.compress_size
                if ratio > MAX_COMPRESSION_RATIO:
                    raise WorkbookInspectionError(
                        f"suspicious ZIP compression ratio for: {info.filename}"
                    )
        for required in ("[Content_Types].xml", "xl/workbook.xml"):
            if required not in self.members:
                raise WorkbookInspectionError(f"OOXML package is missing required part: {required}")

    def has(self, name: str) -> bool:
        return name in self.members

    def read_bytes(self, name: str) -> bytes:
        info = self.members.get(name)
        if info is None:
            raise WorkbookInspectionError(f"OOXML package is missing referenced part: {name}")
        if info.file_size > MAX_XML_PART_BYTES:
            raise WorkbookInspectionError(f"OOXML part exceeds XML safety limit: {name}")
        return self.archive.read(name)

    def xml(self, name: str) -> ET.Element:
        raw = self.read_bytes(name)
        if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
            raise WorkbookInspectionError(f"unsafe XML declaration in: {name}")
        try:
            return ET.fromstring(raw)
        except ET.ParseError as exc:
            raise WorkbookInspectionError(f"malformed XML in {name}: {exc}") from exc


def _relationships(reader: _OOXMLReader, source_part: str) -> dict[str, dict[str, str]]:
    rel_part = _relationship_part_name(source_part)
    if not reader.has(rel_part):
        return {}
    root = reader.xml(rel_part)
    relationships: dict[str, dict[str, str]] = {}
    for element in root.findall("pr:Relationship", NS):
        relationship_id = element.get("Id")
        target = element.get("Target")
        if relationship_id and target:
            relationships[relationship_id] = _canonical_attributes(element)
    return relationships


def _shared_strings(reader: _OOXMLReader) -> list[str]:
    if not reader.has("xl/sharedStrings.xml"):
        return []
    root = reader.xml("xl/sharedStrings.xml")
    values: list[str] = []
    for si in root.findall("x:si", NS):
        values.append("".join(node.text or "" for node in si.iterfind(".//x:t", NS)))
    return values


def _cell_value(
    cell: ET.Element, shared_strings: list[str]
) -> tuple[str | None, str | None, str | None]:
    formula_node = cell.find("x:f", NS)
    value_node = cell.find("x:v", NS)
    inline_node = cell.find("x:is", NS)
    data_type = cell.get("t")
    formula = f"={formula_node.text or ''}" if formula_node is not None else None
    if inline_node is not None:
        value = "".join(node.text or "" for node in inline_node.iterfind(".//x:t", NS))
    elif value_node is None:
        value = None
    elif data_type == "s":
        try:
            value = shared_strings[int(value_node.text or "")]
        except (ValueError, IndexError):
            value = value_node.text
    else:
        value = value_node.text
    return value, formula, data_type


def _worksheet_fact(
    reader: _OOXMLReader,
    name: str,
    part_name: str,
    shared_strings: list[str],
    warnings: list[str],
) -> WorksheetFact:
    root = reader.xml(part_name)
    cells: dict[str, CellFact] = {}
    for cell in root.findall(".//x:sheetData/x:row/x:c", NS):
        address = cell.get("r")
        if not address:
            continue
        value, formula, data_type = _cell_value(cell, shared_strings)
        cells[address] = CellFact(
            address=address,
            value=value,
            formula=formula,
            formula_normalized=normalize_formula(formula),
            data_type=data_type,
        )

    validation_nodes = root.findall(".//x:dataValidations/x:dataValidation", NS)
    validations = tuple(sorted(_canonical_element(node) for node in validation_nodes))
    protection = root.find("x:sheetProtection", NS)
    protection_facts = _canonical_attributes(protection) if protection is not None else {}
    return WorksheetFact(
        name=name,
        part_name=part_name,
        cells=dict(sorted(cells.items())),
        data_validations=validations,
        protection=protection_facts,
    )


def _external_link_targets(
    reader: _OOXMLReader, workbook_rels: dict[str, dict[str, str]]
) -> tuple[str, ...]:
    targets: set[str] = set()
    for relationship in workbook_rels.values():
        relationship_type = relationship.get("Type", "")
        target = relationship.get("Target", "")
        if relationship.get("TargetMode") == "External":
            targets.add(target)
        if relationship_type.endswith("/externalLink"):
            part_name = _resolve_target("xl/workbook.xml", target)
            if not reader.has(part_name):
                continue
            for link_relationship in _relationships(reader, part_name).values():
                if link_relationship.get("TargetMode") == "External":
                    targets.add(link_relationship.get("Target", ""))
    return tuple(sorted(target for target in targets if target))


def inspect_workbook(source: str | Path) -> WorkbookFact:
    """Inspect one workbook using bounded, read-only OOXML parsing.

    Supported facts are intentionally limited to v0.1. Charts, pivot tables,
    conditional formatting semantics, threaded comments, and most drawing
    details are reported only as presence-based unsupported feature warnings.
    """

    with _OOXMLReader(source) as reader:
        warnings: list[str] = []
        workbook = reader.xml("xl/workbook.xml")
        shared_strings = _shared_strings(reader)
        workbook_rels = _relationships(reader, "xl/workbook.xml")
        sheets: dict[str, WorksheetFact] = {}
        for sheet in workbook.findall("x:sheets/x:sheet", NS):
            name = sheet.get("name")
            relation_id = sheet.get(f"{{{RELATIONSHIP_NS}}}id")
            relation = workbook_rels.get(relation_id or "")
            if not name or relation is None:
                warnings.append(
                    f"could not resolve worksheet relationship for sheet: {name or '<unnamed>'}"
                )
                continue
            if relation.get("TargetMode") == "External":
                warnings.append(f"worksheet relationship is external and was skipped: {name}")
                continue
            part_name = _resolve_target("xl/workbook.xml", relation["Target"])
            try:
                sheets[name] = _worksheet_fact(reader, name, part_name, shared_strings, warnings)
            except WorkbookInspectionError as exc:
                warnings.append(f"could not inspect worksheet '{name}': {exc}")

        defined_names: dict[tuple[str, str | None], DefinedNameFact] = {}
        for node in workbook.findall("x:definedNames/x:definedName", NS):
            name = node.get("name")
            if not name:
                continue
            local_sheet_id = node.get("localSheetId")
            fact = DefinedNameFact(
                name=name, value=(node.text or "").strip(), local_sheet_id=local_sheet_id
            )
            defined_names[(name, local_sheet_id)] = fact

        workbook_protection = workbook.find("x:workbookProtection", NS)
        unsupported: list[str] = []
        feature_prefixes = {
            "xl/charts/": "charts are present but not interpreted",
            "xl/pivotTables/": "pivot tables are present but not interpreted",
            "xl/slicers/": "slicers are present but not interpreted",
            "xl/threadedComments/": "threaded comments are present but not interpreted",
        }
        for prefix, message in feature_prefixes.items():
            if any(member.startswith(prefix) for member in reader.members):
                unsupported.append(message)

        return WorkbookFact(
            source=str(Path(source)),
            sheets=dict(sorted(sheets.items())),
            defined_names=dict(sorted(defined_names.items())),
            external_links=_external_link_targets(reader, workbook_rels),
            workbook_protection=_canonical_attributes(workbook_protection)
            if workbook_protection is not None
            else {},
            has_vba=reader.has("xl/vbaProject.bin"),
            unsupported_features=tuple(sorted(unsupported)),
            warnings=tuple(sorted(warnings)),
        )
