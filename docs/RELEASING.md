# Releasing XLSX-Ray

This project does not publish packages or create tags automatically. Publication requires maintainer-owned PyPI and GitHub release authority.

## Pre-release checks

From a clean checkout, run:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
ruff check .
ruff format --check .
rm -rf dist build src/*.egg-info
python -m build
```

Inspect the generated files:

```bash
python -m zipfile -l dist/*.whl
python -m twine check dist/*
```

## Version and changelog

1. Update `version` in `pyproject.toml`.
2. Move the `Unreleased` entries in `CHANGELOG.md` into a dated version section.
3. Update the comparison links in `CHANGELOG.md`.
4. Commit the release preparation and tag the same commit as `vX.Y.Z`.

## Publishing to PyPI

After configuring maintainer credentials or PyPI Trusted Publishing, upload the checked distribution files:

```bash
python -m twine upload dist/*
```

Do not upload a build from a dirty checkout. Never place PyPI tokens in the repository, workflow files, or issue comments.

## GitHub Action tags

Once a stable release tag exists, publish a GitHub Release and maintain a major-version tag for the composite Action:

```bash
git tag -a v0.1.0 -m "XLSX-Ray v0.1.0"
git push origin v0.1.0
# Update a floating v0 tag only after deciding the compatibility policy.
git tag -fa v0 -m "XLSX-Ray v0 action tag"
git push origin v0 --force
```

Consumers should pin an immutable release tag or commit SHA when they require strict supply-chain reproducibility. The floating `v0` tag is only a convenience policy and should not move across incompatible behavior changes without clear release notes.
