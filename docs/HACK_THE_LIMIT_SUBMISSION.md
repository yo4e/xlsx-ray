# Hack The Limit submission package

Checked against the official Hack The Limit Devpost pages on 2026-08-24.

- Overview / submission requirements: https://hack-the-limit-1.devpost.com/
- Rules: https://hack-the-limit-1.devpost.com/rules
- Repository: https://github.com/yo4e/xlsx-ray

## Important organizer-page inconsistencies

Devpost currently displays **Aug 29, 2026 at 11:45 PM PDT** as the deadline in the hackathon header and overview, while the Rules body still contains **July 29, 2026 at 9:00 PM PDT**. Treat this as an organizer-page inconsistency and submit well before the currently displayed Aug 29 deadline.

The overview also says participants must be students and above the legal age of majority in their country of residence, while the Rules body says the event is open to high-school and college students. Eligibility must be confirmed by the entrant; this repository document does not attempt to resolve that inconsistency.

## Submission status

The software itself is submission-ready. XLSX-Ray already has:

- a working local, read-only CLI for `.xlsx` and `.xlsm`;
- deterministic Markdown and JSON reports;
- versioned JSON Schema output contracts;
- explainable low / medium / high risk classification;
- evidence-only formula impact leads for direct A1 references, static range overlap, and safely resolved static defined names;
- a composite GitHub Action with CI threshold support;
- a public `v0.1.0` GitHub release;
- synthetic demo workbook generation;
- tests, packaging, security, architecture, compatibility, release, and contribution documentation.

The main remaining submission work is presentation: at least one required project file (screenshot, video, or equivalent), plus a concise Devpost description and demo flow.

## Recommended title and one-line pitch

**Project title:** XLSX-Ray

**One-line pitch:** Turn opaque Excel binary changes into reviewable, explainable software artifacts for Git and CI.

Alternative short hook for thumbnails, captions, or the first line of a demo:

> Git says your Excel file changed. XLSX-Ray tells you what changed — and why it matters.

## Ready-to-paste Devpost description

### Problem Statement

Excel workbooks are everywhere in finance, operations, research, planning, and internal tooling, but they remain awkward software artifacts. Put an `.xlsx` file in Git and a pull request usually cannot tell a reviewer whether the change was a harmless input edit, a rewritten formula, a removed validation rule, a new external link, a protection change, or the introduction of a macro-bearing workbook.

That makes spreadsheet review depend on opening files manually and visually inspecting them — a fragile process for files that may contain business-critical logic.

### Solution Overview

XLSX-Ray is a local, read-only command-line tool and GitHub Action that turns workbook changes into deterministic, reviewable evidence.

It inspects selected OOXML facts directly from `.xlsx` and `.xlsm` packages and produces Markdown for humans and versioned JSON for automation. It does not calculate formulas, execute VBA, follow external links, upload workbook contents, or modify the workbook.

Instead of treating an Excel file as an opaque binary blob, XLSX-Ray makes supported structural and risk-relevant changes visible in the same review workflow teams already use for code.

### Key Features

- **Workbook-aware diff:** reports worksheet, cell value, formula, defined-name, external-link, validation, protection, and VBA-package changes.
- **Explainable risk levels:** fixed low / medium / high rules make CI decisions understandable rather than opaque.
- **Formula impact evidence:** conservatively surfaces reviewer leads from direct A1 references, static range overlap, and scope-safe static defined names without pretending to be a full Excel calculation engine.
- **GitHub Action:** can write a workbook review into the GitHub Job Summary and fail CI when supported high-risk changes are detected.
- **Human + machine output:** Markdown reports for review and stable, versioned JSON Schema-backed output for automation.
- **Local-first safety boundary:** no hosted service, no required API, no formula execution, no macro execution, no workbook mutation.

### Technologies Used

- Python 3.10+
- Standard-library ZIP and XML inspection for OOXML packages
- `pytest` for regression and adversarial tests
- `ruff` for linting / formatting
- JSON Schema Draft 2020-12 for machine-readable output contracts
- GitHub Actions composite action for CI integration
- `openpyxl` in development fixtures to validate representative third-party-produced workbooks

XLSX-Ray intentionally has no runtime dependencies beyond Python 3.10+.

### Target Users

- engineering teams that keep operational or analytical Excel workbooks in Git;
- finance, operations, research, and data teams whose spreadsheets contain review-worthy logic;
- maintainers who want CI checks around workbook changes without uploading sensitive files to a hosted service;
- developers building spreadsheet-aware review or compliance workflows.

### What Makes It Different

Many spreadsheet comparison tools focus on visual or cell-by-cell differences. XLSX-Ray is designed around **software review evidence**: deterministic package facts, explainable risk, CI behavior, and conservative impact leads.

The product boundary is deliberate. XLSX-Ray does not claim to reproduce Excel, evaluate formulas, prove semantic equivalence, parse macro behavior, or build a complete dependency graph. When it cannot support a claim reliably, it prefers an explicit limitation over a guess.

### Current Status

`v0.1.0` is publicly released on GitHub. The repository includes a reusable GitHub Action, synthetic demo workbooks, versioned JSON schemas, adversarial parser tests, compatibility and security documentation, and an implementation review that records the project's reliability boundaries.

PyPI publication is still pending and is not required to run the tool; it can be installed from the repository or GitHub release artifacts.

## Suggested short description

XLSX-Ray makes Excel changes reviewable in Git. It compares `.xlsx` / `.xlsm` workbooks and reports risk-relevant structural changes — formulas, validation, external links, protection, defined names, VBA package presence, and conservative formula-impact evidence — as deterministic Markdown and JSON. It is local-first, read-only, CI-friendly, and never evaluates formulas or executes macros.

## Judging-criteria positioning

Hack The Limit currently weights judging as follows:

| Criterion | Weight | XLSX-Ray evidence to emphasize |
|---|---:|---|
| Execution & Build Quality | 30% | Working CLI and Action, release packaging, CI, deterministic reports, schema contracts, regression/adversarial tests. |
| Originality | 25% | Treating Excel workbooks as reviewable software artifacts rather than merely visual spreadsheets. |
| Value & Impact | 20% | Real-world spreadsheet logic is business-critical but poorly represented in normal Git review. |
| User Experience | 15% | One command / one Action step, Markdown Job Summary, clear risk levels, no hosted setup. |
| Presentation Quality | 10% | A crisp before/after demo should show the difference between “binary file changed” and actionable workbook evidence. |

Do not spend the final submission pass adding speculative features merely to increase scope. The highest-value remaining work is making the existing capability immediately legible to judges.

## Required project-file plan

Devpost requires at least one screenshot, video, or file showing project functionality or design.

Recommended minimum submission set:

1. **Hero screenshot** — Git or GitHub can only show an opaque workbook change, while XLSX-Ray shows a structured report with a high-risk formula or validation change.
2. **45–60 second demo video or GIF** — generate the included synthetic workbooks, run `xlsx-ray diff`, show the report, then show the same workflow through the GitHub Action if practical.
3. **Repository link** — https://github.com/yo4e/xlsx-ray

A single excellent screenshot satisfies the mandatory project-file requirement; a short video materially improves the Presentation and UX story.

## Demo capture brief

This is the part best suited to a local coding / screen-recording environment such as Codex plus a human capture pass.

### Goal

Communicate the entire value proposition in under one minute without explaining OOXML internals.

### Recommended sequence

**0–7 seconds — The problem**

Show a Git diff / PR context where an Excel workbook is effectively opaque. On-screen line:

> `budget.xlsx changed` is not a useful code review.

**7–18 seconds — Create a safe demo**

Run:

```bash
python examples/create_demo_workbooks.py
```

Briefly show `examples/generated/before.xlsx` and `examples/generated/after.xlsm`.

**18–35 seconds — Run XLSX-Ray**

Run:

```bash
xlsx-ray diff examples/generated/before.xlsx examples/generated/after.xlsm
```

Hold long enough for the viewer to read the highest-risk rows. Favor a terminal size that keeps the report legible at 1080p.

**35–48 seconds — CI behavior**

Run:

```bash
xlsx-ray diff examples/generated/before.xlsx examples/generated/after.xlsm --fail-on high
```

Show that the report is still produced and the command exits `1` because a supported high-risk change exists.

**48–60 seconds — The boundary / close**

Show the repository README or GitHub Action example with one closing line:

> Local. Read-only. Deterministic. No formula or macro execution.

### Capture requirements

- Use generated, non-sensitive workbooks only.
- Do not imply that XLSX-Ray calculates formulas or proves downstream results.
- Do not describe macro-package presence detection as malware analysis.
- Keep terminal text large enough to read on Devpost's embedded player.
- Avoid long installation footage; judges need the product behavior, not package-manager scrolling.
- If showing the GitHub Action, use a successful real run or a deliberately documented `--fail-on high` run rather than a mock UI.

## Hero screenshot composition

Preferred image content:

- left/top: a minimal cue that Git only sees an Excel binary change;
- center: `xlsx-ray diff before.xlsx after.xlsm`;
- main visual: the Markdown or terminal report, with `Highest risk: high` and 2–4 representative findings visible;
- small footer/tagline: “Review Excel changes like software changes.”

Avoid marketing-heavy graphics that hide the actual tool output. The judging criteria reward build quality, UX, and presentation; the product itself should be the visual proof.

## Submission checklist

- [ ] Confirm entrant eligibility against the current Devpost page and organizer rules.
- [ ] Re-check the Devpost deadline immediately before submission because the overview and Rules body currently disagree.
- [ ] Use `XLSX-Ray` as the project title.
- [ ] Paste and lightly personalize the Devpost description above.
- [ ] Add the GitHub repository link.
- [ ] Add all team members and roles, or mark the submission as solo.
- [ ] Upload at least one project file; the hero screenshot is the minimum.
- [ ] Preferably add the 45–60 second demo video / GIF.
- [ ] Verify every screenshot/video claim against the current `main` behavior.
- [ ] Confirm demo assets contain only generated, non-sensitive workbooks.
- [ ] Do a final pass for readable text at Devpost thumbnail / embedded-player sizes.

## Work split

### Good fit for this repository/documentation pass

- Devpost submission copy;
- judging-criteria positioning;
- README clarity improvements;
- submission checklist;
- demo script and claims guardrails.

### Good fit for Codex / local execution

- run the repository from a clean environment and capture the exact demo output;
- if needed, add a deterministic `examples/demo.sh` convenience script without changing product behavior;
- generate a clean terminal recording / GIF or provide the exact commands and outputs for human screen capture;
- optionally prepare a GitHub Action demo PR/run that can be screenshotted;
- check that all demo commands still pass on the final submission commit.

Avoid asking Codex to invent new product features unless the capture pass discovers a genuine demo-blocking bug.