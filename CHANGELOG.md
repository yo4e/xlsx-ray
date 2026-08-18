# Changelog

All notable changes to XLSX-Ray are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Evidence-only formula impact leads for static A1 range overlap and safely resolved workbook/local defined names.
- Provenance-rich `impact_evidence` records in diff JSON schema `0.2`, while preserving the existing flat `impact` formula-cell list.
- Reproducible fixture-study record and regression coverage for local-name shadowing, quoted sheets, range containment, false-positive prevention, deterministic ordering, and an `openpyxl`-generated defined-name workbook.
- Versioned JSON Schema contracts for diff `0.2` and audit `0.1`, shipped in the Python package and validated against representative model output in CI.
- A `--json-output` CLI option that writes a secondary JSON report from the same inspection result as the primary report.

### Changed

- Markdown diff output now labels direct dependents and new range/name reviewer leads as explicit static evidence rather than a dependency graph.
- Worksheet facts retain OOXML sheet-order `localSheetId` so local names can be resolved only in their active formula-sheet scope.
- The composite GitHub Action now generates Markdown and JSON reports from one workbook diff pass instead of inspecting both workbooks twice.

### Fixed

- Formula normalization now preserves leading and trailing whitespace as well as internal whitespace, matching the documented evidence-only normalization contract.

## [0.1.0] - 2026-08-15

### Added

- Read-only OOXML inspection for worksheet, cell/formula, defined-name, external-link, data-validation, protection, and VBA-presence facts.
- Deterministic `xlsx-ray diff` and `xlsx-ray audit` commands with Markdown and JSON output.
- Explainable low/medium/high review-risk rules and `--fail-on` CI threshold.
- Direct textual formula-dependent evidence for changed formula cells.
- Bounded ZIP/XML input checks and synthetic fixture tests.
- A local composite GitHub Action, Git guidance, architecture/compatibility documentation, contribution guidance, security policy, MIT license, and preserved opportunity research.
- Reproducible adversarial ZIP/XML fixtures and an `openpyxl`-generated workbook compatibility fixture.
- Composite-Action integration coverage, built-distribution metadata validation, and documented release-candidate dry-run steps.
- Node 24-compatible GitHub Actions workflow versions for checkout, Python setup, and artifact upload examples.

### Changed

- Direct formula-impact evidence now excludes string literals and correlates A1 references across absolute markers, casing, and quoted sheet names.
- Function-name casing is the only formula normalization; all whitespace is preserved because Excel whitespace can be meaningful.
- Unresolved, duplicate, external, or unsafe worksheet relationships now fail closed rather than producing a partial workbook report.

### Security

- Reject duplicate/ambiguous ZIP member names, unsafe internal worksheet targets, unexpected XML namespaces, and bounded XML depth/element/text exhaustion patterns.
- The tool never executes macros, evaluates formulas, follows links, or changes inspected workbooks.

[Unreleased]: https://github.com/yo4e/xlsx-ray/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yo4e/xlsx-ray/releases/tag/v0.1.0
