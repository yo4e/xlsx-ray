# Releasing XLSX-Ray

This project does not publish packages, create tags, move the floating `v0` Action tag, or create GitHub Releases automatically. Those steps require maintainer-owned PyPI/GitHub authority and an intentional public-release decision.

## Release-candidate dry run

Start from a clean checkout on the candidate commit. The development extra includes the realistic fixture generator and metadata checker.

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
ruff check .
ruff format --check .
rm -rf dist build src/*.egg-info
python -m build
python -m twine check dist/*
```

Inspect both artifacts and run the README flow from the built wheel in a clean virtual environment:

```bash
python -m zipfile -l dist/*.whl
tar -tzf dist/*.tar.gz | grep -E '/(README.md|LICENSE|action.yml|tests/support.py)$'

python -m venv /tmp/xlsx-ray-release-test
/tmp/xlsx-ray-release-test/bin/pip install dist/xlsx_ray-*.whl
python examples/create_demo_workbooks.py
set +e
/tmp/xlsx-ray-release-test/bin/xlsx-ray diff \
  examples/generated/before.xlsx examples/generated/after.xlsm --fail-on high
status=$?
set -e
test "$status" -eq 1
/tmp/xlsx-ray-release-test/bin/xlsx-ray audit examples/generated/after.xlsm --format json
```

The expected threshold exit status is `1`: the command must still write its report. An invalid workbook must instead return CLI status `2`.

The repository CI also runs the composite Action against generated non-sensitive workbooks in report-only mode. Verify that all CI jobs, including **Exercise composite Action**, are green before release.

## Version and changelog

1. Confirm that `version` in `pyproject.toml`, the dated `[0.1.0]` section in `CHANGELOG.md`, and the release notes describe the same behavior.
2. Move any `Unreleased` entries into a dated version section.
3. Update comparison links in `CHANGELOG.md`.
4. Commit release preparation and repeat the dry run from that commit.

## Publication-only owner actions

After an explicit decision to publish, configure PyPI Trusted Publishing or maintainer credentials, upload the already-checked files, and create the GitHub release/tag:

```bash
python -m twine upload dist/*
git tag -a v0.1.0 -m "XLSX-Ray v0.1.0"
git push origin v0.1.0
```

Create release notes from the corresponding `CHANGELOG.md` section. Never put PyPI tokens in the repository, workflow files, issue comments, or logs.

## GitHub Action tags

Only after deciding the major-version compatibility policy, maintain a floating Action tag:

```bash
git tag -fa v0 -m "XLSX-Ray v0 Action tag"
git push origin v0 --force
```

Consumers needing strict supply-chain reproducibility should pin an immutable release tag or commit SHA. The floating `v0` tag is a convenience policy and must not move across incompatible behavior changes without clear release notes.

## Recommended repository settings

The current repository does not require a protection-setting change to run CI. Before a public release, the owner should enable branch protection or rulesets for `main` that require the **CI / Test**, **CI / Build and validate distribution**, and **CI / Exercise composite Action** checks, prevent force pushes, and require pull requests. These settings are intentionally not changed automatically because they affect the owner's repository-wide workflow.
