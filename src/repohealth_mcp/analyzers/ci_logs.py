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

# ── Failure-category patterns ─────────────────────────────────────────────────
# Each entry is (category_name, confidence, list_of_patterns_that_must_match).
# All patterns in the list must fire at least once across the log for the
# category to be assigned.

_PYTEST_FAILED_LINE = re.compile(r"FAILED\s+\S+::\S+")
_ASSERTION_LINE = re.compile(r"(?:E\s+assert\b|AssertionError)")
_PYTEST_SHORT_SUMMARY = re.compile(r"\d+ failed")

_BUILD_ERROR = re.compile(r"error TS\d+|SyntaxError:|ModuleNotFoundError:|ImportError:")
_OOM_PATTERN = re.compile(r"Killed|OOMKilled|out of memory", re.IGNORECASE)
_TIMEOUT_PATTERN = re.compile(r"timed?\s*out|DeadlineExceeded", re.IGNORECASE)
_NETWORK_PATTERN = re.compile(r"ECONNREFUSED|ENOTFOUND|connection refused|could not resolve", re.IGNORECASE)


def diagnose_ci_log(log_path: Path) -> LogDiagnosis:
    """Parse a CI log file and return a structured diagnosis.

    Args:
        log_path: Resolved, validated path to the log file.

    Returns:
        A ``LogDiagnosis`` with categorised errors, warnings, counts,
        and a failure-category classification with confidence score.

    Raises:
        LogFileNotFoundError: If the file does not exist.
        EmptyLogFileError: If the file is empty.

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

    category, confidence = _classify_failure(raw_text, errors)
    summary = _build_summary_text(errors, warnings, category)

    return LogDiagnosis(
        log_path=str(log_path),
        total_lines=len(lines),
        errors=errors,
        warnings=warnings,
        error_count=len(errors),
        warning_count=len(warnings),
        summary=summary,
        category=category,
        confidence=confidence,
    )


# ── Failure classification ────────────────────────────────────────────────────

def _classify_failure(full_text: str, errors: list[LogLine]) -> tuple[str, float]:
    """Return (category, confidence) for the most likely failure type.

    Confidence is a heuristic score in [0, 1].  0.0 means no category
    was detected.  Categories are checked in priority order; the first
    match wins.
    """
    # ── Test assertion failure ────────────────────────────────────────────
    has_failed_line = bool(_PYTEST_FAILED_LINE.search(full_text))
    has_assertion = bool(_ASSERTION_LINE.search(full_text))
    has_summary = bool(_PYTEST_SHORT_SUMMARY.search(full_text))

    if has_failed_line and has_assertion:
        # Strong signal: pytest failure line + assertion mismatch
        confidence = 0.95 if has_summary else 0.90
        return "test_assertion_failure", confidence

    if has_failed_line:
        return "test_failure", 0.80

    # ── OOM ──────────────────────────────────────────────────────────────
    if _OOM_PATTERN.search(full_text):
        return "out_of_memory", 0.85

    # ── Timeout ──────────────────────────────────────────────────────────
    if _TIMEOUT_PATTERN.search(full_text):
        return "timeout", 0.80

    # ── Network / DNS ─────────────────────────────────────────────────────
    if _NETWORK_PATTERN.search(full_text):
        return "network_error", 0.80

    # ── Build / import error ──────────────────────────────────────────────
    if _BUILD_ERROR.search(full_text):
        return "build_error", 0.75

    # ── Generic: errors present but pattern unrecognised ─────────────────
    if errors:
        return "generic_failure", 0.50

    return "", 0.0


# ── Summary text ──────────────────────────────────────────────────────────────

def _build_summary_text(
    errors: list[LogLine],
    warnings: list[LogLine],
    category: str,
) -> str:
    parts: list[str] = []
    if category:
        parts.append(f"Category: {category}")
    if errors:
        parts.append(f"{len(errors)} error(s)")
    if warnings:
        parts.append(f"{len(warnings)} warning(s)")
    if not parts:
        return "No issues detected."
    return "Detected: " + ", ".join(parts) + "."
