"""Tests for the tech debt analyzer."""

import textwrap
from pathlib import Path

import pytest

from repohealth_mcp.analyzers.tech_debt import scan_tech_debt
from repohealth_mcp.core.constants import Severity
from repohealth_mcp.core.models import TechDebtSummary


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def simple_project(tmp_path: Path) -> Path:
    """A minimal project with a few debt markers."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text(
        textwrap.dedent("""\
            def add(a, b):
                # TODO: add type hints
                return a + b

            def hack_workaround():
                # HACK: remove after upstream fix
                pass

            def broken():
                # FIXME: this crashes on empty input
                pass
        """)
    )
    return tmp_path


@pytest.fixture()
def clean_project(tmp_path: Path) -> Path:
    """A project with no debt markers."""
    (tmp_path / "clean.py").write_text("def greet(name: str) -> str:\n    return f'Hello {name}'\n")
    return tmp_path


# ── Import smoke ──────────────────────────────────────────────────────────────

def test_module_importable() -> None:
    """Ensure the tech_debt module can be imported without errors."""
    import repohealth_mcp.analyzers.tech_debt  # noqa: F401


# ── Basic scanning ────────────────────────────────────────────────────────────

def test_scan_returns_summary_type(simple_project: Path) -> None:
    result = scan_tech_debt(simple_project)
    assert isinstance(result, TechDebtSummary)


def test_scan_finds_expected_findings(simple_project: Path) -> None:
    result = scan_tech_debt(simple_project)
    assert result.total_findings == 3  # TODO, HACK, FIXME


def test_scan_clean_project_has_zero_findings(clean_project: Path) -> None:
    result = scan_tech_debt(clean_project)
    assert result.total_findings == 0


def test_scan_by_marker_counts(simple_project: Path) -> None:
    result = scan_tech_debt(simple_project)
    assert result.by_marker.get("TODO", 0) == 1
    assert result.by_marker.get("HACK", 0) == 1
    assert result.by_marker.get("FIXME", 0) == 1


def test_scan_severity_populated(simple_project: Path) -> None:
    result = scan_tech_debt(simple_project)
    assert result.by_severity  # should be non-empty


def test_scan_scanned_files_count(simple_project: Path) -> None:
    result = scan_tech_debt(simple_project)
    assert result.scanned_files >= 1


# ── Severity filtering ────────────────────────────────────────────────────────

def test_severity_filter_excludes_low(simple_project: Path) -> None:
    """When filtering for HIGH+, TODO (LOW) should be excluded."""
    result = scan_tech_debt(simple_project, severity_filter=Severity.HIGH)
    markers = {f.marker for f in result.findings}
    assert "TODO" not in markers


def test_severity_filter_includes_fixme(simple_project: Path) -> None:
    result = scan_tech_debt(simple_project, severity_filter=Severity.HIGH)
    markers = {f.marker for f in result.findings}
    assert "FIXME" in markers


# ── Custom globs ──────────────────────────────────────────────────────────────

def test_include_globs_filters_file_types(tmp_path: Path) -> None:
    """Only .txt files included — no .py findings expected."""
    (tmp_path / "notes.txt").write_text("# TODO: write something\n")
    (tmp_path / "main.py").write_text("# FIXME: fix this\n")

    result = scan_tech_debt(tmp_path, include_globs=["**/*.txt"])
    file_names = {f.file for f in result.findings}
    assert all(".txt" in name for name in file_names)


# ── TODO: future tests ────────────────────────────────────────────────────────
# TODO: test multi-line annotation capture once implemented
# TODO: test .gitignore exclusion once implemented
# TODO: test large file with many markers for performance
