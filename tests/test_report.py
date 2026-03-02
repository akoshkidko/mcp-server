"""Tests for the project health report aggregator."""

import textwrap
from pathlib import Path

import pytest

from repohealth_mcp.analyzers.report import build_project_health_report
from repohealth_mcp.core.constants import HealthStatus
from repohealth_mcp.core.models import HealthReport


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def minimal_project(tmp_path: Path) -> Path:
    """A project with a Python file and a requirements.txt."""
    (tmp_path / "main.py").write_text("# TODO: implement me\n")
    (tmp_path / "requirements.txt").write_text("fastapi==0.110.0\n")
    return tmp_path


@pytest.fixture()
def project_with_log(tmp_path: Path) -> tuple[Path, Path]:
    """Project + a CI log containing errors."""
    (tmp_path / "main.py").write_text("def run(): pass\n")
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n")
    log = tmp_path / "ci.log"
    log.write_text(
        textwrap.dedent("""\
            [INFO] Build started
            [ERROR] Test failed
        """)
    )
    return tmp_path, log


# ── Import smoke ──────────────────────────────────────────────────────────────

def test_module_importable() -> None:
    import repohealth_mcp.analyzers.report  # noqa: F401


# ── Basic report generation ───────────────────────────────────────────────────

def test_returns_health_report(minimal_project: Path) -> None:
    result = build_project_health_report(minimal_project)
    assert isinstance(result, HealthReport)


def test_score_in_valid_range(minimal_project: Path) -> None:
    result = build_project_health_report(minimal_project)
    assert 0.0 <= result.health_score <= 1.0


def test_health_status_is_valid_enum(minimal_project: Path) -> None:
    result = build_project_health_report(minimal_project)
    assert result.health_status in HealthStatus


def test_project_path_recorded(minimal_project: Path) -> None:
    result = build_project_health_report(minimal_project)
    assert result.project_path == str(minimal_project)


def test_tech_debt_populated(minimal_project: Path) -> None:
    result = build_project_health_report(minimal_project)
    # tech_debt should be present even if finding count is 0
    assert result.tech_debt is not None


def test_ci_diagnosis_none_when_not_provided(minimal_project: Path) -> None:
    result = build_project_health_report(minimal_project)
    assert result.ci_diagnosis is None


def test_ci_diagnosis_populated_when_log_provided(project_with_log: tuple[Path, Path]) -> None:
    project, log = project_with_log
    result = build_project_health_report(project, ci_log_path=log)
    assert result.ci_diagnosis is not None
    assert result.ci_diagnosis.error_count >= 1


def test_generated_at_is_set(minimal_project: Path) -> None:
    result = build_project_health_report(minimal_project)
    assert result.generated_at is not None


def test_to_dict_is_json_serialisable(minimal_project: Path) -> None:
    import json
    result = build_project_health_report(minimal_project)
    dumped = json.dumps(result.to_dict())
    assert dumped  # non-empty


# ── Partial failure resilience ────────────────────────────────────────────────

def test_missing_log_file_adds_note_not_raises(minimal_project: Path) -> None:
    """If the CI log path is invalid, the report still completes with a note."""
    bad_log = minimal_project / "nonexistent.log"
    result = build_project_health_report(minimal_project, ci_log_path=bad_log)
    assert result.ci_diagnosis is None
    assert any("CI log" in note for note in result.notes)


# ── TODO: future tests ────────────────────────────────────────────────────────
# TODO: test that a project with many FIXME/BUG markers gets a lower score
# TODO: test threshold boundary: score exactly at warning/healthy boundary
# TODO: test concurrent analyzer execution once async is added
