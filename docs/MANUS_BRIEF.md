# Manus implementation brief — XLSX-Ray

## Mission

Take `yo4e/xlsx-ray` from the current concept stage to the strongest credible, third-party-usable early OSS release that can be completed safely and autonomously.

Work as one large assignment. Avoid stopping after every small technical decision or asking the owner for routine approval. Research, technical validation, implementation, tests, CI, documentation, packaging, and OSS readiness should be treated as one continuous task.

Read first:

- `README.md`
- `docs/PROJECT_BRIEF.md`
- this file

## Preserve the opportunity research

The project originated from the **Open-Source Software Opportunity Research** completed by Manus AI on 2026-08-15.

Before or during implementation, add the complete research result to this repository under `docs/`, preferably as:

`docs/OPPORTUNITY_RESEARCH_2026-08-15.md`

Preserve the original evidence, source URLs, 24-candidate comparison, ranking, top-three deep dive, and final recommendation rather than replacing it with a short summary. If the original accompanying `candidate_ranked.csv`, `sources.md`, or `research_method.md` materials are still available to you, add them under an appropriate `docs/research/` directory as well.

The research's key conclusion was that Excel workbook structural diff / formula-risk auditing was the highest-ranked new OSS opportunity and received a **GO** recommendation. Keep the report as provenance for why this repository exists.

## Product contract

XLSX-Ray is not intended to be merely another visual spreadsheet diff.

Its purpose is to make `.xlsx` / `.xlsm` changes **reviewable and auditable in local / Git / CI workflows** by extracting deterministic workbook facts and identifying changes that deserve human attention.

A useful mental model is:

> Turn an opaque Excel binary change into a reviewable software artifact.

Core runtime should be:

- local-first;
- read-only;
- deterministic;
- safe for untrusted workbooks within reasonable parser limits;
- free of mandatory hosted API / LLM dependencies;
- free of macro execution and arbitrary workbook command execution.

## Phase A — refresh and validate the research

Before committing to architecture, quickly re-check the direct competitor landscape and package / project naming surfaces so that implementation does not blindly reproduce an existing active project.

Investigate at minimum the research's direct / adjacent competitors such as ExceLint, ExcelCompare, Git XL, and any newly discovered workbook semantic-diff or audit tools.

Confirm whether the differentiating gap still exists:

- cross-platform local CLI;
- Git / PR review orientation;
- workbook-wide structural evidence;
- formula / defined-name / external-link / validation / protection / VBA-presence changes;
- deterministic risk-oriented report rather than only cell diff.

If a newly discovered strong active competitor already solves essentially the same problem well, document the finding and make a narrow PIVOT or STOP decision rather than bloating the product.

## Phase B — technical spike and canonical workbook model

Choose the implementation language and libraries based on maintainability and distribution. The opportunity research suggested PyPI as a natural distribution surface, but do not force Python if another stack materially improves OOXML correctness and CLI / Action packaging.

Prefer direct OOXML inspection where library abstractions would hide relevant workbook facts. Reuse well-maintained libraries where they are reliable; do not reimplement ZIP/XML parsing without reason.

Build a canonical read-only workbook representation sufficient to compare two revisions. Explicitly distinguish:

- supported facts;
- partially supported facts;
- unknown / unsupported constructs.

Do not claim certainty where the parser cannot justify it.

## Phase C — useful v0.1 diff

Implement the smallest coherent release that provides meaningful review value.

Target these areas, adjusting only where technical validation shows a better boundary:

1. worksheet additions / removals / renames;
2. changed cell values and formulas;
3. formula normalization / reference comparison where reliable;
4. defined-name changes;
5. external-link changes;
6. data-validation changes;
7. workbook / worksheet protection changes;
8. VBA presence / addition / removal for `.xlsm`, without executing VBA;
9. downstream formula-impact evidence where feasible without building an Excel calculation engine;
10. deterministic rule-based risk classification such as low / medium / high.

The risk system must be explainable. Every elevated finding should say which workbook fact changed and why that category was assigned. Avoid black-box scoring.

A CLI should support a useful workflow conceptually similar to:

```bash
xlsx-ray diff old.xlsx new.xlsx
xlsx-ray audit workbook.xlsx
```

Exact command names may be refined if package / executable naming constraints require it.

Add machine-readable JSON output. Add Markdown suitable for PR summaries. Add SARIF only if it meaningfully improves GitHub review integration.

A CI threshold such as:

```bash
xlsx-ray diff old.xlsx new.xlsx --fail-on high
```

is desirable if it can be defined clearly and tested.

## Phase D — Git and GitHub workflow integration

Make XLSX-Ray useful in repositories that commit Excel workbooks.

Investigate and implement the simplest credible combination of:

- GitHub Action for workbook changes in pull requests;
- concise Job Summary / annotations when appropriate;
- optional `.gitattributes` textconv / diff-driver guidance if safe and useful;
- optional pre-commit integration guidance.

Do not require broad repository write permissions. Prefer read-only GitHub permissions whenever possible.

Avoid making the Action depend on a hosted XLSX-Ray service.

## Phase E — fixtures and tests

Tests are a core product asset, not an afterthought.

Create non-sensitive synthetic workbook fixtures representing realistic scenarios such as:

- ordinary value change;
- formula change;
- copied formula / relative-reference change;
- sheet rename or deletion;
- defined-name addition / removal;
- external-link introduction;
- data-validation removal;
- protection removal;
- `.xlsx` vs `.xlsm` / VBA-presence change;
- multiple simultaneous changes;
- workbook feature that XLSX-Ray intentionally cannot interpret.

Where possible, generate fixtures reproducibly from code rather than checking in unexplained binary samples. If binary fixtures are required, document their provenance and purpose.

Tests should cover parsing, canonicalization, diff classification, risk rules, CLI output, malformed / adversarial inputs within reasonable limits, and GitHub Action packaging where practical.

## Phase F — security and robustness

Treat workbook files as untrusted input.

At minimum consider:

- ZIP bombs / pathological archive sizes;
- XML entity / parser hazards;
- path traversal in ZIP entries;
- malformed OOXML;
- huge sheets / memory blowups;
- formulas, links, and VBA content as data only;
- never executing macros;
- never launching external links;
- never evaluating formulas just because a workbook contains them.

Document the actual safety boundary; do not overclaim sandboxing.

## Phase G — OSS readiness

Bring the repository to a state where an unrelated developer can understand, install, test, and contribute.

Complete or update as appropriate:

- README with a 30-second explanation;
- installation instructions;
- CLI examples with sample output;
- GitHub Action example;
- architecture / supported-feature documentation;
- limitations / compatibility matrix;
- explicit OSS license (choose a conventional permissive license if appropriate and document the choice);
- `CONTRIBUTING.md`;
- `SECURITY.md`;
- changelog / release-note convention;
- package metadata and versioning;
- CI for lint / test / package build;
- reproducible examples / fixtures;
- research report and research-source materials described above.

If package publication itself requires credentials or owner decisions unavailable to you, prepare the package completely and document the final publication commands instead of stopping earlier.

## Autonomous work rules

Do not ask the owner to approve routine choices such as parser libraries, internal module names, test runners, project layout, formatting tools, CI fixes, or documentation wording.

If an approach fails, diagnose it and try a reasonable alternative before asking for help.

Human involvement should be requested only for genuinely material blockers such as:

- required secrets / credentials;
- paid external services;
- destructive or irreversible operations;
- legal / ownership questions that cannot be reasonably handled by a standard OSS choice;
- a major change in project purpose;
- a decision whose consequences cannot be safely inferred from the current brief.

If such a blocker occurs, do not send a bare question. Report the blocker, options, recommended choice, and what work can continue independently.

## Git workflow

You may use branches / PRs or direct commits as appropriate to the environment and risk level.

Keep intermediate commits as granular as useful internally, but report to the owner in large outcome-oriented chunks rather than narrating every file edit.

If the implementation becomes coherent and CI is green, integrate safely into `main` when permissions allow. Otherwise leave a clean merge-ready PR.

## Feature discipline

Do not try to win by accumulating dozens of weak checks.

Prefer a small set of workbook facts that are:

- deterministic;
- explainable;
- useful in review;
- tested against realistic fixtures;
- unlikely to surprise users with noise.

Do not implement full Excel recalculation, macro execution, cloud collaboration, AI-generated repairs, or automatic workbook mutation simply to make the project look larger.

## Completion criteria

Aim to finish only when an unrelated user can:

1. understand why XLSX-Ray exists;
2. install or run the CLI locally;
3. compare two sample workbooks;
4. understand every reported risk from evidence;
5. use the tool in CI / GitHub Actions if practical;
6. run the test suite;
7. see an explicit license and contribution / security guidance;
8. understand supported and unsupported workbook features;
9. trace the project back to the preserved opportunity research;
10. see a clear GO / PIVOT / STOP conclusion based on what the implementation actually proved.

## Final report

When the task is complete, give one consolidated report rather than incremental chatter. Include:

- what was built;
- what research was preserved / refreshed;
- architecture and distribution choices;
- test and CI status;
- security boundaries;
- major commits / PRs;
- exact instructions for a third party to try it;
- known limitations;
- any remaining credential-only publication step;
- final GO / PIVOT / STOP judgment.

Do not stop at research, scaffolding, or a proof of concept if the remaining work is feasible in the current assignment.