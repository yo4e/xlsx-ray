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

XLSX-Ray parses untrusted OOXML packages with bounded, read-only ZIP/XML inspection. It rejects duplicate or ambiguous ZIP member names, unsafe archive paths, member-count and aggregate-uncompressed-size breaches, suspicious per-member compression ratios, oversize XML parts, malformed or unexpected-namespace XML, excessive XML depth/element/text counts, unsafe internal worksheet relationship targets, and XML declarations containing `DOCTYPE` / `ENTITY`.

These checks are tested defense in depth, not a sandbox or a guarantee that any hostile workbook is harmless. The tool parses XML twice for bounded validation and interpretation, and it does not isolate CPU, process memory, or the Python runtime from a malicious file. Run untrusted input in an environment appropriate to your threat model.

The project intentionally does not execute VBA, evaluate formulas, invoke Excel/LibreOffice, follow external links, upload workbook contents, or mutate files. A detected VBA project, formula, or external link is treated as data only.
