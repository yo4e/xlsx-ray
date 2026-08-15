# XLSX-Ray — Initial Product Brief

Status: working draft / research-backed concept  
Date: 2026-08-15

## 1. Problem

Excel workbooks are widely used as operational artifacts, but `.xlsx` / `.xlsm` changes are difficult to review in Git-based workflows. A binary file may change because of a harmless value edit, or because a formula, defined name, external link, validation rule, protection setting, or VBA-bearing workbook state changed in a way that deserves review.

Existing tooling tends to cover only a subset of this problem: cell-oriented comparison, formula-error analysis, VBA extraction, or proprietary/cloud review workflows. The opportunity is to make workbook changes **reviewable as deterministic evidence in local and CI workflows**.

## 2. Product thesis

XLSX-Ray should turn two workbook revisions into a structured, explainable review artifact.

Core question:

> What meaningfully changed in this workbook, and which changes deserve human attention?

The project should remain read-only and deterministic by default. It should not require workbook contents to be sent to a hosted API or LLM.

## 3. Target users

Initial users may include:

- developers who keep `.xlsx` / `.xlsm` assets in Git;
- finance / operations teams reviewing budget, estimate, forecasting, or checklist workbooks;
- auditors and analysts who need an evidence trail for workbook changes;
- maintainers of repositories containing generated or manually edited spreadsheet artifacts;
- teams that want a GitHub Action / pre-commit check for spreadsheet changes.

## 4. Candidate v0.1 scope

Given an old and new workbook, extract and compare high-confidence workbook facts.

Candidate checks / outputs:

1. sheets added / removed / renamed;
2. cell values and formulas changed;
3. formula normalization sufficient to distinguish meaningful reference/formula changes when reliable;
4. defined-name changes;
5. external-link changes;
6. data-validation changes;
7. workbook / worksheet protection changes;
8. VBA presence / removal for `.xlsm` without executing macros;
9. downstream dependency / impact evidence for changed formulas where feasible;
10. deterministic rule-based risk classification such as low / medium / high;
11. Markdown and JSON reports;
12. SARIF and GitHub Action integration if they materially improve review UX;
13. a CI option such as `--fail-on high`.

## 5. Non-goals for v0.1

Do not expand into:

- Excel / LibreOffice replacement;
- full workbook recalculation engine;
- macro execution;
- proving the mathematical correctness of formulas;
- cloud collaboration / document hosting;
- mandatory AI or hosted model inference;
- automatic workbook rewriting or repair;
- exhaustive support for every Excel feature before a useful MVP exists.

## 6. Research basis

An opportunity study completed on 2026-08-15 compared 24 OSS ideas and ranked **Excel workbook structural diff / formula-risk auditing** first, with the strongest GO recommendation.

The research identified the following market gap:

- spreadsheet version-control pain is recurring and often handled with manual workarounds;
- existing projects such as ExceLint, ExcelCompare, and Git XL cover adjacent needs but leave a gap around cross-platform, Git/PR-oriented, workbook-wide semantic risk auditing;
- a local read-only implementation avoids external API cost and sensitive workbook upload;
- the project can naturally distribute as a CLI, package, pre-commit integration, GitHub Action, and eventually editor integrations;
- useful success signals are real CI adoption, compatibility reports, rule / format contributions, and examples where a workbook change would otherwise have been missed — not stars alone.

The original research report also recommended a first implementation sequence centered on stable OOXML structure rather than recalculation: canonical workbook extraction, two-version diff, formula/reference normalization and impact analysis, then Action/SARIF packaging.

## 7. Competitive boundary

The project should not merely become another visual cell diff.

The differentiator should be a **review / audit layer** across workbook structure and operational risk, with output that fits software review workflows.

Any feature that merely duplicates a healthy established OSS tool should be reconsidered, integrated, or left out unless XLSX-Ray adds a clear review-level advantage.

## 8. Validation discipline

Before claiming broad Excel compatibility:

- build synthetic non-sensitive workbook fixtures;
- test `.xlsx` and `.xlsm` separately;
- record unsupported OOXML constructs explicitly;
- prefer `unknown / unsupported` over misleading certainty;
- measure false positives in risk classification;
- do not execute formulas or macros as part of auditing.

## 9. OSS readiness

Before public promotion, the project should have:

- explicit open-source license;
- reproducible tests and fixtures;
- clear install / usage instructions;
- privacy and security notes;
- contribution guidance;
- CI;
- documented limitations;
- versioned releases / changelog convention;
- a preserved copy of the research report that motivated the project.

## 10. Success criterion

A credible early release should let a third party run something conceptually like:

```bash
xlsx-ray diff old.xlsx new.xlsx
xlsx-ray audit workbook.xlsx
```

and receive a concise, explainable report that makes a workbook change materially easier to review than a raw binary diff.
