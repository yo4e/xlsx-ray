# Contributing to XLSX-Ray

Thank you for helping make workbook changes safer to review.

## Development setup

XLSX-Ray targets Python 3.10+ and uses no runtime third-party dependencies.

```bash
git clone https://github.com/yo4e/xlsx-ray.git
cd xlsx-ray
python -m pip install -e ".[dev]"
python -m pytest -q
ruff check .
python -m build
```

## Contribution principles

Keep v0.1 local-first, read-only, deterministic, and explainable. A contribution should not execute formulas or VBA, follow external links, upload workbook data, or silently change a workbook. New risk rules must state the concrete workbook fact that caused the level; opaque heuristic scores are out of scope.

When adding OOXML coverage, document whether a feature is **supported**, **partially supported**, or **unsupported** in [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md). Prefer an explicit warning to a misleading interpretation.

## Tests and fixtures

Tests are a product asset. Add or update tests for every behavior change. Use the reproducible synthetic fixture builder in `tests/support.py` whenever possible; do not add real or sensitive workbooks. Tests should cover a normal path and, where relevant, malformed/untrusted input handling.

Run the commands above before opening a pull request. CI runs the test suite, static checks, and package build.

## Pull requests

Use a focused title and describe the review impact rather than only the implementation detail. Include:

1. the workbook fact or workflow being improved;
2. the expected risk/reporting behavior;
3. fixture/test coverage;
4. compatibility or limitation updates; and
5. any security implications.

Do not include user workbooks, credentials, external-link targets that contain secrets, or macro payloads in issues or pull requests. See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## Release notes

Add a short entry under the `Unreleased` heading in [CHANGELOG.md](CHANGELOG.md) for user-visible behavior changes. This project follows [Semantic Versioning](https://semver.org/); while v0 is in progress, changes to supported report schemas and risk rules are treated as release-note-worthy compatibility changes.
