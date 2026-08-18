# XLSX-Ray

**Turn opaque Excel binary changes into reviewable software artifacts.**

XLSX-Ray is a local, read-only CLI that compares `.xlsx` and `.xlsm` workbooks and emits deterministic evidence for code review and CI. It is built for teams that keep Excel workbooks in Git and need to distinguish an ordinary input edit from a formula rewrite, removed validation rule, new external link, protection change, defined-name change, or macro-bearing workbook.

> XLSX-Ray does **not** calculate formulas, execute VBA, open external links, upload files, or modify workbooks.

## What v0.1 reports

| Review fact | What XLSX-Ray does |
|---|---|
| Worksheets | Finds additions, removals, and high-confidence renames. |
| Cells and formulas | Reports value/formula changes; recognizes function-name casing-only formula edits, while preserving all whitespace. |
| Defined names | Finds added, removed, and changed references. |
| External links | Finds introduced and removed external link targets without following them. |
| Data validation | Compares validation-rule facts and highlights removal/replacement. |
| Protection | Compares workbook and worksheet protection attributes. |
| VBA | Detects only whether `xl/vbaProject.bin` is present; never executes or parses macros. |
| Formula impact | Lists deterministic review leads from direct A1 cells, static A1 range overlap, and safely resolved static defined names. |
| Risk | Applies fixed, explainable `low`, `medium`, and `high` rules suitable for CI. |

For the exact support matrix and limitations, read [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md). For the design and safety boundary, read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Install

XLSX-Ray has no runtime dependencies beyond Python 3.10+.

```bash
python -m pip install xlsx-ray
```

Until the first PyPI publication, clone the repository and install from the checkout instead:

```bash
git clone https://github.com/yo4e/xlsx-ray.git
cd xlsx-ray
python -m pip install .
```

## Quick start

```bash
xlsx-ray diff before.xlsx after.xlsx
xlsx-ray diff before.xlsx after.xlsx --format json
xlsx-ray diff before.xlsx after.xlsx --fail-on high
xlsx-ray diff before.xlsx after.xlsx --output report.md --json-output report.json
xlsx-ray audit workbook.xlsm
```

The default is Markdown intended for pull-request summaries. JSON is stable and machine-readable; the current diff schema version is `0.2`, which adds provenance-rich `impact_evidence` while retaining the legacy flat `impact` formula-cell list. The audit schema remains `0.1`. `--json-output` writes a secondary JSON report from the same in-memory inspection result, so callers that need both formats do not have to read and compare the workbook twice.

Versioned JSON Schema files ship with the package at `xlsx_ray/schemas/diff-0.2.schema.json` and `xlsx_ray/schemas/audit-0.1.schema.json` (source paths: `src/xlsx_ray/schemas/`). Machine consumers should check `schema_version` and validate against the matching schema instead of assuming an unversioned shape. XLSX-Ray does not currently emit SARIF.

```text
# XLSX-Ray workbook diff

- Before: `before.xlsx`
- After: `after.xlsx`
- Changes: 3
- Highest risk: `high`

| Risk | Category | Subject | Why it matters |
| --- | --- | --- | --- |
| `high` | `formula_changed` | `Model!B2` | A formula changed; formula results are not calculated by XLSX-Ray. |
| `high` | `data_validation_changed` | `Inputs` | A data-validation rule was removed or replaced. |
| `low` | `cell_value_changed` | `Inputs!A1` | A non-formula cell value changed. |
```

Generate synthetic, non-sensitive sample workbooks locally and try the command:

```bash
python examples/create_demo_workbooks.py
xlsx-ray diff examples/generated/before.xlsx examples/generated/after.xlsm --fail-on high
```

`--fail-on high` exits `1` when a high-risk supported change is present; this is useful as a CI gate. An inspection failure exits `2` with an error message.

## GitHub Actions

Pin the immutable `v0.1.0` release for strict reproducibility, or use the floating `v0` tag for the latest compatible v0 release.

```yaml
name: Review workbook changes
on:
  pull_request:
    paths:
      - "**/*.xlsx"
      - "**/*.xlsm"

permissions:
  contents: read

jobs:
  xlsx-ray:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0
      - name: Materialize the PR-base workbook
        run: |
          mkdir -p .xlsx-ray/base
          git show "${{ github.event.pull_request.base.sha }}:models/budget.xlsx" > .xlsx-ray/base/budget.xlsx
      - uses: yo4e/xlsx-ray@v0
        with:
          old: .xlsx-ray/base/budget.xlsx
          new: models/budget.xlsx
          fail-on: high
```

The action writes an `xlsx-ray.md` report to the GitHub Job Summary and exposes Markdown/JSON report paths as outputs. Both reports are rendered from one workbook-inspection/diff pass. A calling workflow can upload those paths as artifacts. It does not require write permissions or a hosted XLSX-Ray service. See [examples/github-actions/workbook-review.yml](examples/github-actions/workbook-review.yml) for a reusable workflow example.

## Git textconv (optional)

XLSX-Ray complements, rather than replaces, a Git textconv. A textconv can show a broad textual workbook representation, while XLSX-Ray emphasizes structured facts and review risk. See [docs/GIT_INTEGRATION.md](docs/GIT_INTEGRATION.md) for a safe starting point.

## Safety model

The tool uses bounded, read-only ZIP/XML inspection. It rejects duplicate or unsafe member paths, archive/member size limits, suspicious compression ratios, malformed or unexpected-namespace XML, `DOCTYPE`/`ENTITY` declarations, overly deep XML, and unsafe worksheet relationship targets. These checks reduce common parser hazards but are **not** a sandbox. Treat untrusted workbooks according to your environment's security policy.

XLSX-Ray never executes macros, evaluates formulas, starts Excel/LibreOffice, opens external links, uploads workbook contents, or changes the workbook under inspection. Formula impact leads are **static, evidence-only review hints** rather than a complete dependency graph or a claim about calculated outcomes. Supported leads cover direct A1 references, static A1 range overlap, and workbook/local defined names only when the active scope and one sheet-qualified static A1 target can be determined safely.

## Development

```bash
git clone https://github.com/yo4e/xlsx-ray.git
cd xlsx-ray
python -m pip install -e ".[dev]"
python -m pytest -q
ruff check .
python -m build
python -m twine check dist/*
```

The tests generate synthetic OOXML fixtures from code; no production workbook is used. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Why this project exists

XLSX-Ray was created from a public, evidence-backed OSS opportunity study. The complete study, including 24 candidates, rankings, source URLs, and the direct-competitor analysis is preserved at [docs/OPPORTUNITY_RESEARCH_2026-08-15.md](docs/OPPORTUNITY_RESEARCH_2026-08-15.md). The refreshed implementation-time competitor check is in [docs/RESEARCH_REFRESH_NOTES.md](docs/RESEARCH_REFRESH_NOTES.md), and the post-implementation audit/GO decision is in [docs/IMPLEMENTATION_REVIEW_2026-08-15.md](docs/IMPLEMENTATION_REVIEW_2026-08-15.md).

## Project status

**v0.1.0 is released on GitHub.** The supported surface is deliberately narrow. PyPI publication is still pending; until then, install from the repository checkout or the release artifacts. See the [compatibility matrix](docs/COMPATIBILITY.md), [security policy](SECURITY.md), and [changelog](CHANGELOG.md) before adopting it for production controls.

## License

XLSX-Ray is licensed under the [MIT License](LICENSE).
