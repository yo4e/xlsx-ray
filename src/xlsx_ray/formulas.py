"""Conservative helpers for static formula review evidence.

The module never evaluates formulas or attempts Excel-equivalent parsing. It
recognizes only static A1 cells/ranges and unqualified name tokens outside
Excel string literals. Dynamic, structured, 3D, spilled, external-workbook,
and indirect constructs are deliberately excluded from evidence.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass

_A1_REFERENCE = re.compile(
    r"(?<![A-Za-z0-9_.])"
    r"(?:(?:(?P<quoted_sheet>'(?:[^']|'')+')|(?P<sheet>[A-Za-z_][A-Za-z0-9_.]*))!)?"
    r"(?P<reference>\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?)"
    r"(?![A-Za-z0-9_.])",
    re.IGNORECASE,
)
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")
_CELL = re.compile(r"(?P<column>[A-Z]{1,3})(?P<row>\d+)", re.IGNORECASE)
_NON_NAME_IDENTIFIERS = {"false", "true"}
_DYNAMIC_FUNCTION = re.compile(r"(?<![A-Za-z0-9_.])(INDIRECT|OFFSET)\s*\(", re.IGNORECASE)
_THREE_D_REFERENCE = re.compile(
    r"(?:'(?:[^']|'')+'|[A-Za-z_][A-Za-z0-9_.]*):(?:'(?:[^']|'')+'|[A-Za-z_][A-Za-z0-9_.]*)!",
    re.IGNORECASE,
)
_STRUCTURED_REFERENCE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*\[[^\]]+\]", re.IGNORECASE)


@dataclass(frozen=True)
class StaticRangeReference:
    """A direct, non-dynamic A1 cell or single-area range from formula text."""

    sheet: str | None
    reference: str
    source_text: str
    start_column: int
    start_row: int
    end_column: int
    end_row: int

    def with_default_sheet(self, sheet: str) -> StaticRangeReference:
        """Bind an unqualified formula reference to its formula worksheet."""

        if self.sheet is not None:
            return self
        return StaticRangeReference(
            sheet=sheet,
            reference=self.reference,
            source_text=self.source_text,
            start_column=self.start_column,
            start_row=self.start_row,
            end_column=self.end_column,
            end_row=self.end_row,
        )

    @property
    def resolved_range(self) -> str | None:
        return f"{self.sheet}!{self.reference}" if self.sheet is not None else None

    @property
    def is_single_cell(self) -> bool:
        return self.start_column == self.end_column and self.start_row == self.end_row

    def contains(self, sheet: str, address: str) -> bool:
        """Return static point-in-range containment with Excel-style case folding."""

        if self.sheet is None or self.sheet.casefold() != sheet.casefold():
            return False
        cell = _parse_cell(address)
        if cell is None:
            return False
        column, row = cell
        return (
            self.start_column <= column <= self.end_column and self.start_row <= row <= self.end_row
        )


def _outside_string_segments(formula: str) -> Iterator[str]:
    """Yield fragments outside double-quoted Excel string literals.

    Excel represents a literal quote within a string as ``""``. An unclosed
    quote begins an opaque fragment rather than causing the parser to infer
    intent from malformed formula text.
    """

    start = 0
    index = 0
    while index < len(formula):
        if formula[index] != '"':
            index += 1
            continue
        if start < index:
            yield formula[start:index]
        index += 1
        while index < len(formula):
            if formula[index] != '"':
                index += 1
                continue
            if index + 1 < len(formula) and formula[index + 1] == '"':
                index += 2
                continue
            index += 1
            break
        start = index
    if start < len(formula):
        yield formula[start:]


def normalize_formula(formula: str | None) -> str | None:
    """Normalize only function-name casing while preserving all whitespace.

    Excel whitespace can be semantically meaningful (for example, as a range
    intersection operator). The result is therefore not proof of semantic
    equivalence; it only identifies function-name-casing-only text changes.
    """

    if formula is None:
        return None
    formula = formula.strip()
    if not formula:
        return formula

    normalized: list[str] = []
    index = 0
    while index < len(formula):
        char = formula[index]
        if char == '"':
            string_start = index
            index += 1
            while index < len(formula):
                if formula[index] != '"':
                    index += 1
                    continue
                if index + 1 < len(formula) and formula[index + 1] == '"':
                    index += 2
                    continue
                index += 1
                break
            normalized.append(formula[string_start:index])
            continue
        identifier = _IDENTIFIER.match(formula, index)
        if identifier:
            token = identifier.group(0)
            next_index = identifier.end()
            while next_index < len(formula) and formula[next_index].isspace():
                next_index += 1
            normalized.append(
                token.upper() if next_index < len(formula) and formula[next_index] == "(" else token
            )
            index = identifier.end()
            continue
        normalized.append(char)
        index += 1
    return "".join(normalized)


def _display_sheet(match: re.Match[str]) -> str | None:
    quoted = match.group("quoted_sheet")
    if quoted is not None:
        return quoted[1:-1].replace("''", "'")
    return match.group("sheet")


def _column_index(column: str) -> int:
    value = 0
    for char in column.upper():
        value = value * 26 + ord(char) - ord("A") + 1
    return value


def _parse_cell(cell: str) -> tuple[int, int] | None:
    match = _CELL.fullmatch(cell.replace("$", ""))
    if match is None:
        return None
    return _column_index(match.group("column")), int(match.group("row"))


def _range_from_match(match: re.Match[str]) -> StaticRangeReference | None:
    reference = match.group("reference")
    endpoints = reference.split(":")
    start = _parse_cell(endpoints[0])
    end = _parse_cell(endpoints[-1])
    if start is None or end is None:
        return None
    return StaticRangeReference(
        sheet=_display_sheet(match),
        reference=reference,
        source_text=match.group(0),
        start_column=min(start[0], end[0]),
        start_row=min(start[1], end[1]),
        end_column=max(start[0], end[0]),
        end_row=max(start[1], end[1]),
    )


def _is_supported_match_context(segment: str, match: re.Match[str]) -> bool:
    """Reject A1-looking text that is part of excluded Excel constructs."""

    before = segment[match.start() - 1] if match.start() else ""
    after = segment[match.end()] if match.end() < len(segment) else ""
    # A preceding `[`/`]` marks external-workbook text; `:` marks a 3D sheet
    # reference that would otherwise expose only its terminal sheet. A trailing
    # `[` is a structured reference and `#` is spilled-range syntax.
    return before not in ("[", "]", ":") and after not in ("[", "#")


def has_unsupported_reference_construct(formula: str | None) -> bool:
    """Return whether a formula contains syntax excluded from impact evidence.

    If a formula mixes a supported-looking token with dynamic or context-dependent
    syntax, XLSX-Ray emits no impact lead from that formula. This intentionally
    favors false negatives over a partially interpreted reviewer claim.
    """

    if not formula:
        return False
    for segment in _outside_string_segments(formula):
        if (
            _DYNAMIC_FUNCTION.search(segment)
            or _THREE_D_REFERENCE.search(segment)
            or _STRUCTURED_REFERENCE.search(segment)
            or "#" in segment
            or "[" in segment
        ):
            return True
    return False


def extract_static_references(formula: str | None) -> tuple[StaticRangeReference, ...]:
    """Extract supported direct A1 cells/ranges outside string literals.

    The result preserves first-seen formula spelling for review provenance. It
    intentionally omits external workbooks, 3D references, structured
    references, and spilled ranges rather than partially interpreting them.
    """

    if not formula:
        return ()
    references: list[StaticRangeReference] = []
    for segment in _outside_string_segments(formula):
        for match in _A1_REFERENCE.finditer(segment):
            if not _is_supported_match_context(segment, match):
                continue
            reference = _range_from_match(match)
            if reference is not None and reference not in references:
                references.append(reference)
    return tuple(references)


def extract_references(formula: str | None) -> tuple[str, ...]:
    """Return direct A1 references in the legacy human-readable form."""

    return tuple(
        reference.resolved_range if reference.sheet is not None else reference.reference
        for reference in extract_static_references(formula)
    )


def parse_static_range(expression: str) -> StaticRangeReference | None:
    """Parse one entire, explicitly sheet-qualified static A1 expression.

    Defined-name expressions without an explicit sheet are deliberately not
    resolved because relative-name context is not safely inferable here.
    """

    candidate = expression.strip()
    if candidate.startswith("="):
        candidate = candidate[1:].strip()
    references = extract_static_references(candidate)
    if len(references) != 1:
        return None
    reference = references[0]
    if reference.sheet is None or reference.source_text != candidate:
        return None
    return reference


def extract_name_tokens(formula: str | None) -> tuple[str, ...]:
    """Extract candidate defined-name tokens outside literals and known syntax.

    Token recognition is intentionally narrower than Excel's full name grammar.
    Functions, A1 references, sheet qualifiers, 3D/structured syntax, and
    external-workbook notation are excluded to prevent unsupported certainty.
    """

    if not formula:
        return ()
    names: list[str] = []
    for segment in _outside_string_segments(formula):
        static_spans = [
            (match.start(), match.end())
            for match in _A1_REFERENCE.finditer(segment)
            if _is_supported_match_context(segment, match)
        ]
        for match in _IDENTIFIER.finditer(segment):
            token = match.group(0)
            before = segment[match.start() - 1] if match.start() else ""
            after = segment[match.end()] if match.end() < len(segment) else ""
            next_index = match.end()
            while next_index < len(segment) and segment[next_index].isspace():
                next_index += 1
            overlaps_reference = any(
                match.start() < reference_end and match.end() > reference_start
                for reference_start, reference_end in static_spans
            )
            if (
                overlaps_reference
                or token.casefold() in _NON_NAME_IDENTIFIERS
                or before in ("[", "!")
                or after in ("!", "[", ":")
                or (next_index < len(segment) and segment[next_index] == "(")
            ):
                continue
            if token not in names:
                names.append(token)
    return tuple(names)


def canonical_reference(reference: str, default_sheet: str) -> str | None:
    """Return a case- and absolute-marker-insensitive direct A1 key.

    This accepts the legacy human-readable representation emitted by
    :func:`extract_references`, including an unquoted display sheet name with
    spaces. External-workbook notation is excluded because XLSX-Ray never
    resolves external targets.
    """

    if "!" in reference:
        sheet, address = reference.rsplit("!", 1)
    else:
        sheet, address = default_sheet, reference
    if "[" in sheet or "]" in sheet:
        return None
    address = address.replace("$", "").upper()
    if not re.fullmatch(r"[A-Z]{1,3}\d+(?::[A-Z]{1,3}\d+)?", address):
        return None
    return f"{sheet.casefold()}!{address}"
