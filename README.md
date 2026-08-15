# XLSX-Ray

**Make Excel workbook changes reviewable.**

XLSX-Ray is an experimental open-source tool for deterministic, read-only structural diffing and risk auditing of `.xlsx` / `.xlsm` workbooks.

The project starts from a simple problem: Git can tell you that a workbook binary changed, but reviewers usually cannot see whether the meaningful change was a harmless value edit, a formula rewrite, a removed validation rule, a new external link, an unlocked sheet, or a macro-bearing workbook.

The intended direction is a local CLI and GitHub Action that turns workbook changes into reviewable Markdown / JSON / SARIF-style evidence without uploading workbook contents to an external service.

## Initial product thesis

The first useful version should focus on deterministic workbook facts rather than trying to become an Excel clone or an AI spreadsheet assistant.

Candidate v0.1 scope:

- sheet additions / removals;
- cell value and formula changes;
- normalized formula comparison where technically reliable;
- defined-name changes;
- external-link changes;
- data-validation changes;
- worksheet / workbook protection changes;
- presence or removal of VBA content for `.xlsm`;
- simple downstream-impact evidence for formula changes;
- rule-based risk levels suitable for CI;
- Markdown and JSON output, with SARIF / GitHub Action integration when practical.

Explicit non-goals for the first version include full Excel recalculation, macro execution, proving mathematical correctness of formulas, replacing Excel/LibreOffice, cloud collaboration, and mandatory LLM/API usage.

## Project status

Research / implementation bootstrap. See `docs/PROJECT_BRIEF.md` and `docs/MANUS_BRIEF.md`.
