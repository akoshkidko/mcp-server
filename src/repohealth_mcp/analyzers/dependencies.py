"""Dependency analyzer.

Inspects known manifest files in a project directory and returns a
structured summary of declared dependencies.

This module is a pure Python library — no MCP or HTTP dependencies.
"""

from pathlib import Path

from repohealth_mcp.core.constants import SUPPORTED_MANIFESTS
from repohealth_mcp.core.errors import NoManifestsFoundError
from repohealth_mcp.core.models import DependencyInfo, DependencySummary


def analyze_dependencies(project_path: Path) -> DependencySummary:
    """Scan *project_path* for dependency manifests and parse their contents.

    Args:
        project_path: Resolved, validated project root directory.

    Returns:
        A ``DependencySummary`` listing discovered manifests and dependencies.

    Raises:
        NoManifestsFoundError: If no recognised manifest files are found.

    TODO: Implement per-manifest parsers (requirements.txt, package.json, etc.).
    TODO: Detect unpinned / wildcard version specifiers.
    TODO: Cross-reference with OSV vulnerability database.
    TODO: Flag transitive dependency issues from lock files.
    """
    manifests_found = _discover_manifests(project_path)

    if not manifests_found:
        raise NoManifestsFoundError(
            f"No dependency manifests found in {project_path}.",
            detail=f"Searched for: {SUPPORTED_MANIFESTS}",
        )

    dependencies: list[DependencyInfo] = []
    notes: list[str] = []

    for manifest_path in manifests_found:
        deps, manifest_notes = _parse_manifest(manifest_path, project_path)
        dependencies.extend(deps)
        notes.extend(manifest_notes)

    unpinned = sum(1 for d in dependencies if _is_unpinned(d.version_spec))
    dev_count = sum(1 for d in dependencies if d.is_dev)

    return DependencySummary(
        project_path=str(project_path),
        manifests_found=[str(m.relative_to(project_path)) for m in manifests_found],
        total=len(dependencies),
        dev_count=dev_count,
        unpinned_count=unpinned,
        dependencies=dependencies,
        notes=notes,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _discover_manifests(project_path: Path) -> list[Path]:
    """Return paths of recognised manifest files directly under *project_path*.

    TODO: Also scan one level deep (e.g. packages in a monorepo).
    """
    found: list[Path] = []
    for name in SUPPORTED_MANIFESTS:
        candidate = project_path / name
        if candidate.is_file():
            found.append(candidate)
    return found


def _parse_manifest(
    manifest_path: Path,
    project_root: Path,  # noqa: ARG001 — reserved for relative path reporting
) -> tuple[list[DependencyInfo], list[str]]:
    """Parse a single manifest file and return (dependencies, notes).

    TODO: Route to a dedicated parser based on manifest_path.name.
    Currently returns a stub so the pipeline is functional end-to-end.
    """
    notes = [f"Parsing not yet implemented for {manifest_path.name} — results are stubs."]
    return [], notes


def _is_unpinned(version_spec: str) -> bool:
    """Return True if *version_spec* looks like it doesn't pin to a specific version.

    TODO: Handle all PEP 440 / semver / npm specifier formats properly.
    """
    if not version_spec or version_spec in ("*", "latest", ""):
        return True
    # A rough heuristic: pinned specs usually contain == or a full semver.
    return "==" not in version_spec and "@" not in version_spec
