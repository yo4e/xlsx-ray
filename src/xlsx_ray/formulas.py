"""Conservative formula helpers that never evaluate workbook expressions.

These helpers intentionally do not claim Excel-equivalence or implement a full
formula grammar. They provide stable function-name-casing normalization and
direct A1-reference evidence for review, while explicitly excluding dynamic,
structured, named, 3D, and indirect references.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

_A1_REFERENCE = re.compile(
    r"(?<![A-Za-z0-9_.])"
    r"(?:(?:(?P<quoted_sheet>'(?:[^']|'')+')|(?P<sheet>[A-Za-z_][A-Za-z0-9_.]*))!)?"
    r"(?P<reference>\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?)"
    r"(?![A-Za-z0-9_.])",
    re.IGNORECASE,
)
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")


def _outside_string_segments(formula: str) -> Iterator[str]:
    """Yield formula fragments outside double-quoted Excel string literals.

    Excel represents a literal quote within a string as ``""``. Unclosed
    quotes are treated as the start of an opaque string segment rather than
    attempting to infer intent from malformed formula text.
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
    intersection operator). v0.1 therefore does **not** remove or otherwise
    rewrite whitespace. An equivalent normalized value only proves that formula
    function-name casing changed outside a string literal; it is not a proof of
    general semantic equivalence.
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


def extract_references(formula: str | None) -> tuple[str, ...]:
    """Extract direct A1 references outside Excel string literals.

    This deliberately excludes references inside strings and preserves the
    first-seen textual representation for Markdown evidence. It does not
    resolve named references, structured references, 3D references,
    `INDIRECT`, spilled ranges, or external workbooks.
    """

    if not formula:
        return ()
    references: list[str] = []
    for segment in _outside_string_segments(formula):
        for match in _A1_REFERENCE.finditer(segment):
            sheet = _display_sheet(match)
            reference = match.group("reference")
            text = f"{sheet}!{reference}" if sheet else reference
            if text not in references:
                references.append(text)
    return tuple(references)


def canonical_reference(reference: str, default_sheet: str) -> str | None:
    """Return a case- and absolute-marker-insensitive direct A1 reference key.

    The key is used only to correlate a changed cell with direct formula text.
    External workbook notation is excluded because XLSX-Ray never resolves
    external targets.
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
