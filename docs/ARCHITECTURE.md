# XLSX-Ray v0.1 Architecture

## Design goal

XLSX-Ray turns selected, deterministic facts from two OOXML workbooks into a review artifact. It does not attempt to calculate spreadsheet results or interpret every Excel feature. The architecture deliberately prioritizes **explainability, bounded parsing, and reproducible output** over feature breadth.

```text
.xlsx / .xlsm ZIP package
        │
        ▼
Bounded read-only OOXML inspector
        │
        ├── WorkbookFact (canonical facts)
        │     ├── worksheets and cells/formulas
        │     ├── defined names
        │     ├── external-link targets
        │     ├── validation and protection facts
        │     └── VBA package presence
        ▼
Deterministic diff / audit rules
        │
        ├── Change / AuditFinding with a reason and risk level
        ├── direct textual formula-dependent evidence
        ▼
Markdown or JSON report
        │
        └── local CLI / GitHub Action / CI threshold
```

## Canonical model

The inspector parses only relevant OOXML parts using Python's standard-library `zipfile` and `xml.etree.ElementTree`. It builds a `WorkbookFact` model whose fields are sorted before comparison and rendering. The relevant package parts are:

| Fact | OOXML source | v0.1 treatment |
|---|---|---|
| Worksheets and cells | `xl/workbook.xml`, `xl/worksheets/*.xml` | Supported. Sheet rename is recognized only when a removed and added sheet retain the same worksheet part path. |
| Formula text | `<f>` in worksheet cells | Supported as text only. Only function-name casing outside string literals is normalized; all whitespace is preserved because Excel whitespace can be meaningful. |
| Defined names | `xl/workbook.xml` | Supported. Added, removed, and changed references are compared. |
| External links | `xl/workbook.xml.rels`, `xl/externalLinks/*` relationships | Supported as targets only. Targets are never opened. |
| Data validation | `<dataValidations>` | Supported as a canonical XML fact. Rule semantics are not evaluated. |
| Workbook/worksheet protection | `<workbookProtection>`, `<sheetProtection>` | Supported as attributes. Protection is a review fact, not a claim of cryptographic security. |
| VBA | `xl/vbaProject.bin` package member | Supported only as presence/absence. The binary is never executed or interpreted. |
| Charts, pivot tables, slicers, threaded comments | package member presence | Reported as unsupported presence warnings where detected. |

## Diff and risk rules

Risk is not a black-box score. Each change is assigned a fixed level and textual reason.

| Change | Risk | Rationale |
|---|---:|---|
| Formula changed; formula cell removed | High | Changes model logic. XLSX-Ray does not calculate formulas, so a reviewer must inspect the change. |
| Sheet removed; defined name removed/changed | High | Can invalidate references, dependent formulas, or documented workbook semantics. |
| Data-validation rule removed/replaced | High | Weakens an input control. |
| Workbook/worksheet protection removed | High | Removes a governance control; not a cryptographic-security claim. |
| External link introduced; VBA presence changed | High | Introduces external dependency or executable macro payload. Neither is opened/executed. |
| Formula cell added; defined name added; worksheet protection changed | Medium | Adds logic or changes a review-relevant control. |
| Sheet renamed; external link removed | Medium | May affect consumers and should be reviewed. |
| Non-formula cell value changed; sheet added; formatting-only formula text change | Low | Useful evidence, but normally lower review urgency. |

### Formula impact evidence

For each changed cell or supported defined-name fact, XLSX-Ray can report static **review leads** with an `impact_evidence` record. The record identifies the flagged formula cell, evidence kind, original formula/name spelling, statically resolved range where applicable, and explicit evidence-only wording. The legacy flat `impact` formula-cell list remains available for compatibility; diff JSON schema `0.2` adds the provenance-rich records deliberately.

Direct A1 references exclude string literals and correlate case-insensitively while ignoring `$` absolute markers; quoted sheet names are supported. A static A1 range emits `range_overlap` only when the changed cell falls inside its inclusive row/column bounds on the matching sheet. A defined-name lead is emitted only if an unqualified formula token resolves unambiguously in the formula cell's active local-sheet scope first, then workbook scope, and that definition is exactly one explicitly sheet-qualified static A1 cell/range. Local names on another sheet do not participate.

This is **static review evidence**, not an Excel dependency engine. XLSX-Ray does not resolve relative names, multi-area or formula-defined names, structured references, 3D references, `INDIRECT`, dynamic arrays/spill syntax, external-workbook names, or formulas on a sheet that was renamed with unrewritten cross-sheet references. Unsupported syntax is intentionally omitted rather than partially interpreted.

## Safety boundary

XLSX-Ray treats every workbook as untrusted data. v0.1 rejects duplicate or ambiguous ZIP member names, unsafe paths, too many members, excessive aggregate uncompressed size, suspicious per-member compression ratio, oversize XML parts, malformed or unexpected-namespace XML, overly deep XML, XML with excessive element/text counts, unsafe internal worksheet relationship targets, and XML declarations containing `DOCTYPE` / `ENTITY`. These checks are bounded parser mitigations, not a sandbox or proof that every hostile input is safe.

The tool never:

- executes VBA or any other macro content;
- evaluates formulas;
- starts Excel/LibreOffice;
- follows external links;
- writes, repairs, or alters the inspected workbook;
- uploads workbook data; or
- requires an AI model or hosted API.

## Compatibility and limitations

See [COMPATIBILITY.md](COMPATIBILITY.md) for the supported-feature matrix and limitations. XLSX-Ray is tested with both synthetic `.xlsx`/`.xlsm` package fixtures and an `openpyxl`-generated workbook; this is not a claim of complete Excel feature compatibility.
