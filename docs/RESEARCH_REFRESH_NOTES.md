# Competitive Research Refresh — 2026-08-15

## Purpose

This note refreshes the direct-competitor check required before XLSX-Ray v0.1 implementation. It supplements the in-repository opportunity research rather than replacing it.

## Findings

| Project | Current scope observed | Status / limitation relevant to XLSX-Ray | Consequence for XLSX-Ray |
|---|---|---|---|
| [bitterjug/excel-diff](https://github.com/bitterjug/excel-diff) | Ruby textconv that renders `.xlsx` as text for `git diff`; can hide formulas or calculated values. | Last visible commit is from 2016, no tests, no releases, and the README frames it as a textconv utility rather than a structured review/audit tool. | Preserve optional textconv guidance, but do not treat a textual rendering as a sufficient audit report. |
| [yarhamjohn/excel-compare](https://github.com/yarhamjohn/excel-compare) | Current C# CLI for cell values/formulas, row/column and sheet additions/removals; reports JSON/CSV/HTML and can write an annotated workbook. | It explicitly focuses on cells/formulas and excludes styles, charts, pivot tables, and formatting. It has no releases and does not claim defined-name, external-link, validation, protection, VBA-presence, formula-impact, or explainable risk support. | XLSX-Ray must not compete only on cell-diff output. Its v0.1 differentiator remains a read-only, deterministic workbook-wide evidence and risk layer for Git/CI. |
| [ExceLint](https://github.com/ExceLint/ExceLint) | Excel add-in for formula-error detection. | The original research recorded that it is archived, with its final release in 2019. It is not a cross-platform Git/CI diff workflow. | Do not build a formula-error detector; report concrete changes and lightweight dependency impact instead. |
| [ExcelCompare](https://github.com/na-ka-na/ExcelCompare) | CLI/API for workbook diffs. | The original research recorded a 2015 release series, a 2022 final commit, open portability/diff/format issues, and no declared license. | Provide modern packaging, clear licensing, fixtures, JSON/Markdown reports, and explicit support boundaries. |
| [Git XL](https://github.com/xltrail/git-xl) | Git-oriented VBA diff workflow. | The original research recorded older release activity and current installation/dependency issues. It is chiefly VBA/Git integration rather than a workbook-wide risk audit. | Treat VBA as a safe presence/absence fact; never execute or attempt a semantic macro review in v0.1. |

## Decision: GO, with a narrow boundary

The direct landscape contains active and useful cell-diff tools, but no strong active project was found that combines a cross-platform local CLI with deterministic **workbook-wide structural facts**, explainable **risk-oriented review evidence**, and a local/Git/CI-first workflow.

XLSX-Ray should therefore proceed only with this narrow product boundary:

1. Inspect workbooks read-only; never calculate formulas, execute VBA, follow external links, or mutate files.
2. Report canonical facts that are high confidence: sheets, cells/formulas, defined names, external links, data validations, protection, and VBA package presence.
3. Use explainable rules, not opaque or model-based scoring.
4. Emit human-reviewable Markdown and machine-readable JSON; use a fail threshold for CI.
5. Be explicit about facts that are unavailable or unsupported.

## Sources

- [Excel Textconv repository](https://github.com/bitterjug/excel-diff), inspected 2026-08-15.
- [Excel Compare repository](https://github.com/yarhamjohn/excel-compare), inspected 2026-08-15.
- [ExceLint repository](https://github.com/ExceLint/ExceLint).
- [ExcelCompare repository](https://github.com/na-ka-na/ExcelCompare).
- [Git XL repository](https://github.com/xltrail/git-xl).

