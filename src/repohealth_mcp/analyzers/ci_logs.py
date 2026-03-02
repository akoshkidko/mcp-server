"""CI log diagnostic analyzer.

Parses CI/CD log files and surfaces errors, warnings, and failure patterns.
Designed to work on plain-text log dumps from GitHub Actions, GitLab CI,
Jenkins, CircleCI, or any similar system.

This module is a pure Python library — no MCP or HTTP dependencies.
"""

import re
from pathlib import Path

from repohealth_mcp.core.constants import CI_ERROR_PATTERNS, CI_WARNING_PATTERNS
from repohealth_mcp.core.errors import EmptyLogFileError, LogFileNotFoundError
from repohealth_mcp.core.models import LogDiagnosis, LogLine

# Pre-compiled composite patterns for performance.
# re.IGNORECASE applied at compile time — inline (?i) flags are not
# allowed past position 0 when joining multiple sub-patterns.
_ERROR_RE = re.compile("|".join(CI_ERROR_PATTERNS), re.IGNORECASE)
_WARNING_RE = re.compile("|".join(CI_WARNING_PATTERNS), re.IGNORECASE)


def diagnose_ci_log(log_path: Path) -> LogDiagnosis:
    """Parse a CI log file and return a structured diagnosis.

    Args:
        log_path: Resolved, validated path to the log file.

    Returns:
        A ``LogDiagnosis`` with categorised errors, warnings, and counts.

    Raises:
        LogFileNotFoundError: If the file does not exist.
        EmptyLogFileError: If the file is empty.

    TODO: Add structured log format detection (JSON lines, timestamps).
    TODO: Group related error lines into "incidents" for better signal.
    TODO: Extract step/stage names from common CI log formats.
    TODO: Support compressed (.gz) log files.
    """
    if not log_path.exists():
        raise LogFileNotFoundError(
            f"Log file not found: {log_path}",
            detail=str(log_path),
        )

    raw_text = log_path.read_text(encoding="utf-8", errors="replace")

    if not raw_text.strip():
        raise EmptyLogFileError(
            f"Log file is empty: {log_path}",
            detail=str(log_path),
        )

    lines = raw_text.splitlines()
    errors: list[LogLine] = []
    warnings: list[LogLine] = []

    for line_number, line_text in enumerate(lines, start=1):
        stripped = line_text.strip()
        if not stripped:
            continue

        if _ERROR_RE.search(stripped):
            errors.append(
                LogLine(line_number=line_number, content=stripped, category="error")
            )
        elif _WARNING_RE.search(stripped):
            warnings.append(
                LogLine(line_number=line_number, content=stripped, category="warning")
            )

    summary = _build_summary_text(errors, warnings)

    return LogDiagnosis(
        log_path=str(log_path),
        total_lines=len(lines),
        errors=errors,
        warnings=warnings,
        error_count=len(errors),
        warning_count=len(warnings),
        summary=summary,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_summary_text(errors: list[LogLine], warnings: list[LogLine]) -> str:
    """Produce a one-line human-readable summary of the diagnosis.

    TODO: Replace with a smarter summariser once patterns are validated.
    """
    parts: list[str] = []
    if errors:
        parts.append(f"{len(errors)} error(s)")
    if warnings:
        parts.append(f"{len(warnings)} warning(s)")
    if not parts:
        return "No issues detected."
    return "Detected: " + ", ".join(parts) + "."
