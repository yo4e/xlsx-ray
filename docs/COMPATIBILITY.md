# Compatibility and Limitations

## Supported in v0.1

| Workbook fact | `.xlsx` | `.xlsm` | Notes |
|---|---:|---:|---|
| Workbook and worksheet discovery | Yes | Yes | Unresolved, duplicate, external, or unsafe worksheet relationships are rejected rather than guessed. Standard relative and `/xl/...` internal targets are supported. |
| Sheet add/remove | Yes | Yes | High risk for removal; low risk for addition. |
| Sheet rename | Yes | Yes | Reported only when the OOXML worksheet part path is retained and the mapping is unambiguous. |
| Cell values | Yes | Yes | Text, inline string, shared string, and raw stored values are compared. Display formatting is not calculated. |
| Formula text | Yes | Yes | Formula text is compared; results are never recalculated. Only function-name casing outside string literals is normalized, and all whitespace is preserved. |
| Formula impact evidence | Yes | Yes | Direct A1, static A1 range overlap, and safely resolved static defined-name leads are reported as deterministic review evidence only. |
| Defined names | Yes | Yes | Workbook- and local-sheet-scoped names are compared as text references. |
| External links | Yes | Yes | Relationship targets are compared but never opened. |
| Data-validation facts | Yes | Yes | Canonical rule XML is compared; validation logic is not evaluated. |
| Workbook/worksheet protection facts | Yes | Yes | Attributes are compared; this is not a claim that protection is strong security. |
| VBA presence | N/A | Yes | Only `xl/vbaProject.bin` presence is reported. Macro code is never executed or parsed. |
| Markdown / JSON reports | Yes | Yes | Deterministic ordering is used for supported facts. Diff JSON schema `0.2` adds provenance-rich `impact_evidence` while retaining `impact`. |
| `--fail-on` CI threshold | Yes | Yes | Fails on a supported change/finding at or above the supplied level. |

## Known limitations

| Area | v0.1 behavior |
|---|---|
| Formula semantics | XLSX-Ray does not calculate formulas or prove equivalence. It normalizes only function-name casing outside string literals; it preserves whitespace because whitespace can be meaningful in Excel. |
| Formula references | Direct A1 references outside string literals are indexed as review evidence; absolute markers, casing, and quoted sheet names are normalized for correlation. Static A1 range overlap is supported only for an inclusive range on the matching sheet. Workbook/local defined names are supported only when active scope resolves unambiguously and the entire definition is one explicitly sheet-qualified static A1 cell/range. Local scope shadows workbook scope only for that local sheet. Relative names, multi-area/formula-defined names, structured references, 3D references, `INDIRECT`, spill ranges, external workbooks, and indirect dependencies are not resolved. |
| Cached formula values | Cached values for an unchanged formula are ignored, because v0.1 does not calculate formula results. |
| Styles and formatting | Cell styles, conditional formatting semantics, drawing/layout changes, row heights, and column widths are not a supported semantic diff surface. |
| Charts / pivot tables / slicers | Presence may be reported as unsupported. Their definitions and outputs are not compared. |
| Unsupported OOXML parts | XLSX-Ray favors an explicit warning over an unsupported certainty claim. A missing warning does not prove no unsupported construct exists. |
| Encryption / password-protected packages | Not supported. Standard ZIP/OOXML package access is required. |
| Legacy `.xls` / binary Excel | Not supported. Convert to `.xlsx` or `.xlsm` first. |
| Non-OOXML files | Rejected. |
| Security isolation | Duplicate/ambiguous ZIP names, size/member limits, compression ratio, XML namespace/DOCTYPE/entity/depth/element/text limits, and unsafe internal targets are rejected. These parser mitigations are not a substitute for operating-system sandboxing. |

## Why the scope is narrow

The project is a review and audit layer, not an Excel replacement. Limiting v0.1 to high-confidence, explainable facts reduces false certainty and makes its output suitable for local, Git, and CI workflows.
