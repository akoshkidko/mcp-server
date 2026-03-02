"""Tests for the dependency analyzer."""

from pathlib import Path

import pytest

from repohealth_mcp.analyzers.dependencies import analyze_dependencies
from repohealth_mcp.core.errors import NoManifestsFoundError
from repohealth_mcp.core.models import DependencySummary


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def project_with_manifests(tmp_path: Path) -> Path:
    (tmp_path / "requirements.txt").write_text("fastapi==0.110.0\nuvicorn>=0.29.0\n")
    (tmp_path / "package.json").write_text('{"dependencies": {"lodash": "^4.17.21"}}\n')
    return tmp_path


@pytest.fixture()
def project_without_manifests(tmp_path: Path) -> Path:
    (tmp_path / "README.md").write_text("# My Project\n")
    return tmp_path


# ── Import smoke ──────────────────────────────────────────────────────────────

def test_module_importable() -> None:
    import repohealth_mcp.analyzers.dependencies  # noqa: F401


# ── Basic behaviour ───────────────────────────────────────────────────────────

def test_returns_dependency_summary(project_with_manifests: Path) -> None:
    result = analyze_dependencies(project_with_manifests)
    assert isinstance(result, DependencySummary)


def test_manifests_found(project_with_manifests: Path) -> None:
    result = analyze_dependencies(project_with_manifests)
    manifest_names = result.manifests_found
    assert "requirements.txt" in manifest_names
    assert "package.json" in manifest_names


def test_project_path_recorded(project_with_manifests: Path) -> None:
    result = analyze_dependencies(project_with_manifests)
    assert result.project_path == str(project_with_manifests)


# ── Error conditions ──────────────────────────────────────────────────────────

def test_raises_when_no_manifests(project_without_manifests: Path) -> None:
    with pytest.raises(NoManifestsFoundError):
        analyze_dependencies(project_without_manifests)


# ── TODO: future tests (add once parsers are implemented) ────────────────────
# TODO: test requirements.txt parsing returns correct DependencyInfo entries
# TODO: test package.json parsing
# TODO: test pinned vs unpinned version detection
# TODO: test monorepo sub-package discovery
