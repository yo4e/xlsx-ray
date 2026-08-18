"""Command-line interface for XLSX-Ray."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from .audit import audit_workbook
from .diff import compare_workbooks
from .inspector import WorkbookInspectionError, inspect_workbook
from .models import AuditResult, DiffResult, RiskLevel
from .render import json_output, render_audit_markdown, render_diff_markdown

VERSION = "0.1.0"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xlsx-ray",
        description="Deterministic, read-only structural diffs and risk audits for Excel workbooks.",
    )
    parser.add_argument("--version", action="version", version=f"xlsx-ray {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    diff = subparsers.add_parser("diff", help="compare two .xlsx/.xlsm workbooks")
    diff.add_argument("old", help="baseline .xlsx or .xlsm workbook")
    diff.add_argument("new", help="changed .xlsx or .xlsm workbook")
    diff.add_argument("--format", choices=("markdown", "json"), default="markdown")
    diff.add_argument("--output", type=Path, help="write the report to a file instead of stdout")
    diff.add_argument(
        "--json-output",
        type=Path,
        help="also write the same inspection result as JSON without re-reading the workbooks",
    )
    diff.add_argument(
        "--fail-on",
        choices=tuple(level.label for level in RiskLevel),
        help="exit with status 1 when a change at or above this risk is found",
    )

    audit = subparsers.add_parser("audit", help="audit one .xlsx/.xlsm workbook")
    audit.add_argument("workbook", help="workbook to inspect")
    audit.add_argument("--format", choices=("markdown", "json"), default="markdown")
    audit.add_argument("--output", type=Path, help="write the report to a file instead of stdout")
    audit.add_argument(
        "--json-output",
        type=Path,
        help="also write the same inspection result as JSON without re-reading the workbook",
    )
    audit.add_argument(
        "--fail-on",
        choices=tuple(level.label for level in RiskLevel),
        help="exit with status 1 when a finding at or above this risk is found",
    )
    return parser


def _write(text: str, destination: Path | None) -> None:
    if destination is None:
        sys.stdout.write(text)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def _should_fail(result: DiffResult | AuditResult, fail_on: str | None) -> bool:
    if fail_on is None or result.highest_risk is None:
        return False
    return result.highest_risk >= RiskLevel.parse(fail_on)


def _diff(args: argparse.Namespace) -> DiffResult:
    old = inspect_workbook(args.old)
    new = inspect_workbook(args.new)
    warnings = tuple(sorted(set(old.warnings + new.warnings)))
    return DiffResult(
        old_source=old.source,
        new_source=new.source,
        changes=compare_workbooks(old, new),
        warnings=warnings,
    )


def _audit(args: argparse.Namespace) -> AuditResult:
    return audit_workbook(inspect_workbook(args.workbook))


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    handlers: dict[str, Callable[[argparse.Namespace], DiffResult | AuditResult]] = {
        "diff": _diff,
        "audit": _audit,
    }
    try:
        result = handlers[args.command](args)
    except WorkbookInspectionError as exc:
        parser.error(str(exc))
        return 2

    if (
        args.format == "markdown"
        and args.output is not None
        and args.json_output is not None
        and args.output == args.json_output
    ):
        parser.error("--output and --json-output must be different paths for Markdown output")

    json_report = json_output(result.to_dict())
    if isinstance(result, DiffResult):
        output = json_report if args.format == "json" else render_diff_markdown(result)
    else:
        output = json_report if args.format == "json" else render_audit_markdown(result)
    _write(output, args.output)
    if args.json_output is not None and not (
        args.format == "json" and args.output == args.json_output
    ):
        _write(json_report, args.json_output)
    return 1 if _should_fail(result, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
