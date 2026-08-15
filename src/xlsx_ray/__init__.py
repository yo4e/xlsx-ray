"""XLSX-Ray: deterministic, read-only workbook structural diffing."""

from .audit import audit_workbook
from .diff import compare_workbooks
from .inspector import WorkbookInspectionError, inspect_workbook

__all__ = ["WorkbookInspectionError", "audit_workbook", "compare_workbooks", "inspect_workbook"]
__version__ = "0.1.0"
