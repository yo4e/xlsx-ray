# Git Integration

XLSX-Ray is optimized for a **two-revision review command**, while Git's `textconv` is a convenient way to get broad textual changes in `git diff`. Use both when useful; neither is a substitute for human review.

## CI-oriented diff

In a shell, extract the baseline workbook from a Git revision into a temporary file and compare it with the checked-out version.

```bash
base_ref="origin/main"
workbook="models/budget.xlsx"
temp_dir="$(mktemp -d)"

git show "${base_ref}:${workbook}" > "${temp_dir}/before.xlsx"
xlsx-ray diff "${temp_dir}/before.xlsx" "${workbook}" --fail-on high
```

This approach avoids any repository write operation. Do not use it for untrusted repository histories without applying your normal checkout and CI isolation policy.

## Optional `.gitattributes` textconv

A textconv can expose a broad textual rendering to `git diff`. XLSX-Ray intentionally does not install or configure Git on a user's behalf. An optional project-level configuration can look like this:

```gitattributes
*.xlsx diff=xlsxray
*.xlsm diff=xlsxray
```

Then configure the local Git repository manually after deciding which representation is appropriate for your team:

```bash
git config diff.xlsxray.textconv 'xlsx-ray audit --format markdown'
git config diff.xlsxray.cachetextconv true
```

The `audit` command is a conservative starting point, but it is a single-workbook report rather than a complete line-oriented rendering. For rich pull-request review, prefer an explicit `xlsx-ray diff old.xlsx new.xlsx` command or the GitHub Action.

## Pre-commit pattern

If a repository has a stable baseline workbook, a local hook can fail only on high-risk changes:

```bash
xlsx-ray diff .xlsx-ray/baseline.xlsx models/budget.xlsx --fail-on high
```

Store baseline selection and policy in repository documentation. XLSX-Ray does not automatically choose a Git baseline because the correct comparison point is team-specific.

## What not to automate

Do not use XLSX-Ray output to automatically accept, repair, recalculate, or execute workbook content. In particular, a detected macro or external link is review evidence, not permission to run it.
