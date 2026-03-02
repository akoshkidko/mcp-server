"""Tests for the CI log diagnostic analyzer."""

import textwrap
from pathlib import Path

import pytest

from repohealth_mcp.analyzers.ci_logs import diagnose_ci_log
from repohealth_mcp.core.errors import EmptyLogFileError, LogFileNotFoundError
from repohealth_mcp.core.models import LogDiagnosis


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def log_with_errors(tmp_path: Path) -> Path:
    log = tmp_path / "ci.log"
    log.write_text(
        textwrap.dedent("""\
            [INFO] Starting build...
            [INFO] Running tests...
            [ERROR] Test suite failed: 3 assertions failed
            [WARNING] Deprecated API usage in module foo
            [ERROR] Build exited with exit code 1
        """)
    )
    return log


@pytest.fixture()
def clean_log(tmp_path: Path) -> Path:
    log = tmp_path / "clean.log"
    log.write_text(
        textwrap.dedent("""\
            [INFO] Starting build...
            [INFO] All tests passed.
            [INFO] Build complete.
        """)
    )
    return log


@pytest.fixture()
def empty_log(tmp_path: Path) -> Path:
    log = tmp_path / "empty.log"
    log.write_text("   \n  \n")
    return log


# ── Import smoke ──────────────────────────────────────────────────────────────

def test_module_importable() -> None:
    import repohealth_mcp.analyzers.ci_logs  # noqa: F401


# ── Basic behaviour ───────────────────────────────────────────────────────────

def test_returns_log_diagnosis_type(log_with_errors: Path) -> None:
    result = diagnose_ci_log(log_with_errors)
    assert isinstance(result, LogDiagnosis)


def test_detects_errors(log_with_errors: Path) -> None:
    result = diagnose_ci_log(log_with_errors)
    assert result.error_count >= 2


def test_detects_warnings(log_with_errors: Path) -> None:
    result = diagnose_ci_log(log_with_errors)
    assert result.warning_count >= 1


def test_clean_log_has_no_errors(clean_log: Path) -> None:
    result = diagnose_ci_log(clean_log)
    assert result.error_count == 0
    assert result.warning_count == 0


def test_total_lines_counted(log_with_errors: Path) -> None:
    result = diagnose_ci_log(log_with_errors)
    assert result.total_lines == 5


def test_summary_not_empty(log_with_errors: Path) -> None:
    result = diagnose_ci_log(log_with_errors)
    assert result.summary


# ── Error conditions ──────────────────────────────────────────────────────────

def test_raises_for_missing_file(tmp_path: Path) -> None:
    with pytest.raises(LogFileNotFoundError):
        diagnose_ci_log(tmp_path / "nonexistent.log")


def test_raises_for_empty_file(empty_log: Path) -> None:
    with pytest.raises(EmptyLogFileError):
        diagnose_ci_log(empty_log)


# ── TODO: future tests ────────────────────────────────────────────────────────
# TODO: test ANSI-stripped log content
# TODO: test JSON-lines log format once structured parsing is implemented
# TODO: test large log file performance
