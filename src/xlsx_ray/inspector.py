"""Bounded, read-only inspection of selected high-confidence OOXML facts.

The inspector never calculates formulas, executes VBA, opens external links, or
writes workbook bytes. It treats workbooks as untrusted ZIP/XML packages and
rejects malformed structures that would make a review report ambiguous.
"""

from __future__ import annotations

import io
import json
import posixpath
import re
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
MAX_XML_ELEMENTS = 1_000_000
MAX_XML_DEPTH = 256
MAX_XML_TEXT_BYTES = 24 * 1024 * 1024
_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")


class WorkbookInspectionError(ValueError):
    """Raised for malformed, unsupported, or deliberately rejected workbooks."""


def _attribute_key(item: tuple[str, str]) -> str:
    return item[0]


def _canonical_attributes(element: ET.Element) -> dict[str, str]:
    return dict(sorted(element.attrib.items(), key=_attribute_key))


def _canonical_element(element: ET.Element) -> str:
    """Create a stable, compact representation of selected XML elements."""

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
    """Reject archive paths that are ambiguous or unsafe on common extractors."""

    if not name or "\\" in name or name.startswith("/") or _DRIVE_PREFIX.match(name):
        return False
    candidate = name[:-1] if name.endswith("/") else name
    if not candidate:
        return False
    parts = candidate.split("/")
    return all(part not in {"", ".", ".."} for part in parts)


def _relationship_part_name(part_name: str) -> str:
    folder, filename = posixpath.split(part_name)
    return posixpath.join(folder, "_rels", f"{filename}.rels")


def _resolve_internal_target(source_part: str, target: str) -> str | None:
    """Resolve a package-internal relationship only when it remains in ``xl/``."""

    if not target or "\\" in target or _DRIVE_PREFIX.match(target):
        return None
    if target.startswith("/xl/"):
        resolved = target.lstrip("/")
    elif target.startswith("/"):
        return None
    else:
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source_part), target))
    if not resolved.startswith("xl/") or "/../" in f"/{resolved}/":
        return None
    return resolved


def _expected_tag(namespace: str, local_name: str) -> str:
    return f"{{{namespace}}}{local_name}"


class _OOXMLReader:
    """Bounded access wrapper around one OOXML ZIP package."""

    def __init__(self, source: str | Path):
        self.source = Path(source)
        if self.source.suffix.lower() not in {".xlsx", ".xlsm"}:
            raise WorkbookInspectionError("expected an .xlsx or .xlsm workbook")
        if not self.source.is_file():
            raise WorkbookInspectionError(f"workbook does not exist: {self.source}")
        if not zipfile.is_zipfile(self.source):
            raise WorkbookInspectionError("workbook is not a valid ZIP/OOXML package")
        self.archive = zipfile.ZipFile(self.source, "r")
        try:
            self.infos = tuple(self.archive.infolist())
            self.members = {info.filename: info for info in self.infos}
            self._validate_archive()
        except Exception:
            self.archive.close()
            raise

    def close(self) -> None:
        self.archive.close()

    def __enter__(self) -> _OOXMLReader:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _validate_archive(self) -> None:
        if len(self.infos) > MAX_MEMBERS:
            raise WorkbookInspectionError(f"archive has too many members (limit: {MAX_MEMBERS})")
        names = [info.filename for info in self.infos]
        if len(set(names)) != len(names):
            raise WorkbookInspectionError("archive contains duplicate ZIP member names")
        total_size = sum(info.file_size for info in self.infos)
        if total_size > MAX_UNCOMPRESSED_BYTES:
            raise WorkbookInspectionError(
                "archive uncompressed size exceeds the safety limit "
                f"({MAX_UNCOMPRESSED_BYTES // (1024 * 1024)} MiB)"
            )
        for info in self.infos:
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

    def _validate_xml_bytes(self, raw: bytes, name: str) -> None:
        if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
            raise WorkbookInspectionError(f"unsafe XML declaration in: {name}")
        depth = 0
        element_count = 0
        text_bytes = 0
        try:
            for event, element in ET.iterparse(io.BytesIO(raw), events=("start", "end")):
                if event == "start":
                    depth += 1
                    element_count += 1
                    if depth > MAX_XML_DEPTH:
                        raise WorkbookInspectionError(
                            f"XML nesting exceeds the safety limit in: {name}"
                        )
                    if element_count > MAX_XML_ELEMENTS:
                        raise WorkbookInspectionError(
                            f"XML element count exceeds the safety limit in: {name}"
                        )
                else:
                    text_bytes += len((element.text or "").encode("utf-8"))
                    if text_bytes > MAX_XML_TEXT_BYTES:
                        raise WorkbookInspectionError(
                            f"XML text exceeds the safety limit in: {name}"
                        )
                    element.clear()
                    depth -= 1
        except ET.ParseError as exc:
            raise WorkbookInspectionError(f"malformed XML in {name}: {exc}") from exc

    def xml(self, name: str) -> ET.Element:
        raw = self.read_bytes(name)
        self._validate_xml_bytes(raw, name)
        try:
            return ET.fromstring(raw)
        except ET.ParseError as exc:
            raise WorkbookInspectionError(f"malformed XML in {name}: {exc}") from exc


def _relationships(reader: _OOXMLReader, source_part: str) -> dict[str, dict[str, str]]:
    rel_part = _relationship_part_name(source_part)
    if not reader.has(rel_part):
        return {}
    root = reader.xml(rel_part)
    if root.tag != _expected_tag(PACKAGE_RELATIONSHIP_NS, "Relationships"):
        raise WorkbookInspectionError(f"unexpected relationships namespace in: {rel_part}")
    relationships: dict[str, dict[str, str]] = {}
    for element in root.findall("pr:Relationship", NS):
        relationship_id = element.get("Id")
        target = element.get("Target")
        if relationship_id and target:
            if relationship_id in relationships:
                raise WorkbookInspectionError(f"duplicate relationship Id in: {rel_part}")
            relationships[relationship_id] = _canonical_attributes(element)
    return relationships


def _shared_strings(reader: _OOXMLReader) -> list[str]:
    if not reader.has("xl/sharedStrings.xml"):
        return []
    root = reader.xml("xl/sharedStrings.xml")
    if root.tag != _expected_tag(SPREADSHEET_NS, "sst"):
        raise WorkbookInspectionError("unexpected shared-strings namespace")
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
    reader: _OOXMLReader, name: str, part_name: str, shared_strings: list[str]
) -> WorksheetFact:
    root = reader.xml(part_name)
    if root.tag != _expected_tag(SPREADSHEET_NS, "worksheet"):
        raise WorkbookInspectionError(f"unexpected worksheet namespace in: {part_name}")
    cells: dict[str, CellFact] = {}
    for cell in root.findall(".//x:sheetData/x:row/x:c", NS):
        address = cell.get("r")
        if not address:
            continue
        if address in cells:
            raise WorkbookInspectionError(
                f"duplicate cell address in worksheet '{name}': {address}"
            )
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
    reader: _OOXMLReader, workbook_rels: dict[str, dict[str, str]], warnings: list[str]
) -> tuple[str, ...]:
    targets: set[str] = set()
    for relationship in workbook_rels.values():
        relationship_type = relationship.get("Type", "")
        target = relationship.get("Target", "")
        if relationship.get("TargetMode") == "External":
            targets.add(target)
        if relationship_type.endswith("/externalLink"):
            part_name = _resolve_internal_target("xl/workbook.xml", target)
            if part_name is None:
                warnings.append(f"unsafe external-link relationship target was skipped: {target}")
                continue
            if not reader.has(part_name):
                warnings.append(f"external-link relationship part is missing: {part_name}")
                continue
            for link_relationship in _relationships(reader, part_name).values():
                if link_relationship.get("TargetMode") == "External":
                    targets.add(link_relationship.get("Target", ""))
    return tuple(sorted(target for target in targets if target))


def inspect_workbook(source: str | Path) -> WorkbookFact:
    """Inspect one workbook using bounded, read-only OOXML parsing.

    Supported facts are intentionally limited to the documented v0.1 surface.
    Charts, pivot tables, conditional-format semantics, threaded comments, and
    drawing details are presence-only unsupported-feature warnings.
    """

    with _OOXMLReader(source) as reader:
        warnings: list[str] = []
        workbook = reader.xml("xl/workbook.xml")
        if workbook.tag != _expected_tag(SPREADSHEET_NS, "workbook"):
            raise WorkbookInspectionError("unexpected workbook namespace")
        shared_strings = _shared_strings(reader)
        workbook_rels = _relationships(reader, "xl/workbook.xml")
        sheets: dict[str, WorksheetFact] = {}
        for sheet in workbook.findall("x:sheets/x:sheet", NS):
            name = sheet.get("name")
            relation_id = sheet.get(f"{{{RELATIONSHIP_NS}}}id")
            relation = workbook_rels.get(relation_id or "")
            if not name or relation is None:
                raise WorkbookInspectionError(
                    f"could not resolve worksheet relationship for sheet: {name or '<unnamed>'}"
                )
            if name in sheets:
                raise WorkbookInspectionError(f"workbook contains duplicate sheet name: {name}")
            if relation.get("TargetMode") == "External":
                raise WorkbookInspectionError(f"worksheet relationship is external: {name}")
            part_name = _resolve_internal_target("xl/workbook.xml", relation["Target"])
            if part_name is None:
                raise WorkbookInspectionError(
                    f"unsafe worksheet relationship target for sheet: {name}"
                )
            sheets[name] = _worksheet_fact(reader, name, part_name, shared_strings)

        defined_names: dict[tuple[str, str | None], DefinedNameFact] = {}
        for node in workbook.findall("x:definedNames/x:definedName", NS):
            name = node.get("name")
            if not name:
                continue
            local_sheet_id = node.get("localSheetId")
            key = (name, local_sheet_id)
            if key in defined_names:
                raise WorkbookInspectionError(f"workbook contains duplicate defined name: {name}")
            defined_names[key] = DefinedNameFact(
                name=name, value=(node.text or "").strip(), local_sheet_id=local_sheet_id
            )

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
            external_links=_external_link_targets(reader, workbook_rels, warnings),
            workbook_protection=_canonical_attributes(workbook_protection)
            if workbook_protection is not None
            else {},
            has_vba=reader.has("xl/vbaProject.bin"),
            unsupported_features=tuple(sorted(unsupported)),
            warnings=tuple(sorted(warnings)),
        )
