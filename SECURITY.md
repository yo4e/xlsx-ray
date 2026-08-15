# Security Policy

## Supported versions

Until a stable release exists, the default branch and the latest tagged release receive security fixes on a best-effort basis.

## Reporting a vulnerability

Please do **not** open a public issue for a suspected vulnerability. Report it privately through the repository owner's GitHub contact channel, including:

- a description of the issue and expected impact;
- the XLSX-Ray version or commit;
- minimal, synthetic reproduction steps where possible; and
- whether the workbook must contain a specific OOXML package feature.

Do not send real workbooks, personal data, credentials, or active macro payloads unless the maintainer explicitly establishes a secure transfer method.

## Security boundary

XLSX-Ray parses untrusted OOXML packages with bounded, read-only ZIP/XML inspection. It rejects common unsafe conditions such as unsafe archive paths, size-limit breaches, suspicious compression ratios, malformed XML, and XML declarations containing `DOCTYPE` / `ENTITY`.

These checks are defense in depth, not a sandbox or a guarantee that any hostile workbook is harmless. Run untrusted input in an environment appropriate to your threat model.

The project intentionally does not execute VBA, evaluate formulas, invoke Excel/LibreOffice, follow external links, upload workbook contents, or mutate files. A detected VBA project, formula, or external link is treated as data only.
