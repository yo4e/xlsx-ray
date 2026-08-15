"""Conservative helpers for comparing Excel formulas without evaluating them.

The normalizer intentionally does not claim Excel-equivalence. It only removes
whitespace outside string literals and normalizes function-name casing, which
is sufficient to avoid noisy diffs from common formatting-only edits.
"""

from __future__ import annotations

import re

_CELL_REFERENCE = re.compile(
    r"(?:(?:'(?P<quoted_sheet>(?:[^']|'')+)')|(?P<sheet>[A-Za-z_][A-Za-z0-9_. ]*))?!?"
    r"(?P<reference>\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?)"
)
_FUNCTION_NAME = re.compile(r"\b([A-Za-z_][A-Za-z0-9_.]*)\s*\(")


def normalize_formula(formula: str | None) -> str | None:
    """Return a deterministic, conservative formatting-normalized formula.

    Only whitespace outside Excel string literals and function-name casing are
    changed. Relative references, string literal contents, and all operators
    remain untouched; therefore the result must not be read as a proof of
    semantic equivalence.
    """

    if formula is None:
        return None
    formula = formula.strip()
    if not formula:
        return formula

    current: list[str] = []
    in_string = False
    index = 0
    while index < len(formula):
        char = formula[index]
        if char == '"':
            current.append(char)
            if in_string and index + 1 < len(formula) and formula[index + 1] == '"':
                current.append('"')
                index += 2
                continue
            in_string = not in_string
        elif char.isspace() and not in_string:
            pass
        else:
            current.append(char)
        index += 1
    compact = "".join(current)

    def uppercase_function(match: re.Match[str]) -> str:
        return f"{match.group(1).upper()}("

    return _FUNCTION_NAME.sub(uppercase_function, compact)


def extract_references(formula: str | None) -> tuple[str, ...]:
    """Extract human-readable A1 references for lightweight impact evidence.

    This is intentionally incomplete: structured references, 3D references,
    spilled ranges, names, and `INDIRECT` targets are not resolved. Consumers
    must treat results as evidence of direct textual dependencies only.
    """

    if not formula:
        return ()
    references: list[str] = []
    for match in _CELL_REFERENCE.finditer(formula):
        sheet = match.group("quoted_sheet") or match.group("sheet")
        reference = match.group("reference")
        text = f"{sheet}!{reference}" if sheet else reference
        if text not in references:
            references.append(text)
    return tuple(references)
