"""Tech debt analyzer.

Scans source files in a project directory for debt-marker annotations
(TODO, FIXME, HACK, etc.) and returns structured findings.

This module is a pure Python library — it has no MCP or HTTP dependencies
and can be exercised directly in unit tests.
"""

import re
from pathlib import Path

from repohealth_mcp.core.constants import DEBT_MARKER_SEVERITY, DEBT_MARKERS, Severity
from repohealth_mcp.core.models import TechDebtFinding, TechDebtSummary
from repohealth_mcp.core.paths import relative_to_project
from repohealth_mcp.utils.file_io import iter_text_files

# Pre-compiled pattern that matches any debt marker as a whole word.
_DEBT_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(m) for m in DEBT_MARKERS) + r")\b",
    re.IGNORECASE,
)


def scan_tech_debt(
    project_path: Path,
    include_globs: list[str] | None = None,
    exclude_globs: list[str] | None = None,
    severity_filter: Severity | None = None,
) -> TechDebtSummary:
    """Scan *project_path* for tech debt annotations.

    Args:
        project_path: Resolved, validated project root directory.
        include_globs: Glob patterns selecting files to scan.
            Defaults to common source file extensions.
        exclude_globs: Glob patterns for files/dirs to skip.
        severity_filter: When set, only findings at this severity or higher
            are included in the results.

    Returns:
        A ``TechDebtSummary`` describing all findings.

    TODO: Implement multi-line annotation capture (e.g. block comments).
    TODO: Respect .gitignore exclusions.
    TODO: Add support for custom marker sets via config.
    """
    findings: list[TechDebtFinding] = []
    scanned_files = 0

    for file_path, lines in iter_text_files(project_path, include_globs, exclude_globs):
        scanned_files += 1
        for line_number, line_text in enumerate(lines, start=1):
            match = _DEBT_PATTERN.search(line_text)
            if not match:
                continue

            marker = match.group(1).upper()
            severity = DEBT_MARKER_SEVERITY.get(marker, Severity.INFO)

            if severity_filter and _severity_rank(severity) < _severity_rank(severity_filter):
                continue

            findings.append(
                TechDebtFinding(
                    file=relative_to_project(file_path, project_path),
                    line=line_number,
                    marker=marker,
                    severity=severity,
                    text=line_text.strip(),
                )
            )

    return _build_summary(str(project_path), findings, scanned_files)


# ── Helpers ───────────────────────────────────────────────────────────────────

_SEVERITY_RANK: dict[Severity, int] = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


def _severity_rank(severity: Severity) -> int:
    return _SEVERITY_RANK.get(severity, 0)


def _build_summary(
    project_path: str,
    findings: list[TechDebtFinding],
    scanned_files: int,
) -> TechDebtSummary:
    by_severity: dict[str, int] = {}
    by_marker: dict[str, int] = {}

    for f in findings:
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
        by_marker[f.marker] = by_marker.get(f.marker, 0) + 1

    return TechDebtSummary(
        project_path=project_path,
        total_findings=len(findings),
        by_severity=by_severity,
        by_marker=by_marker,
        findings=findings,
        scanned_files=scanned_files,
    )
