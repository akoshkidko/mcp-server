"""Dependency analyzer.

Inspects known manifest files in a project directory and returns a
structured summary of declared dependencies including version risks
and license information.

This module is a pure Python library — no MCP or HTTP dependencies.
"""

import json
import re
from pathlib import Path

from repohealth_mcp.core.constants import SUPPORTED_MANIFESTS
from repohealth_mcp.core.errors import NoManifestsFoundError
from repohealth_mcp.core.models import DependencyInfo, DependencySummary


def analyze_dependencies(project_path: Path) -> DependencySummary:
    """Scan *project_path* for dependency manifests and parse their contents.

    Args:
        project_path: Resolved, validated project root directory.

    Returns:
        A ``DependencySummary`` listing discovered manifests and dependencies,
        with version-risk flags and license information where available.

    Raises:
        NoManifestsFoundError: If no recognised manifest files are found.

    TODO: Cross-reference with OSV vulnerability database.
    TODO: Flag transitive dependency issues from lock files.
    TODO: Scan one level deep for monorepo sub-packages.
    """
    manifests_found = _discover_manifests(project_path)

    if not manifests_found:
        raise NoManifestsFoundError(
            f"No dependency manifests found in {project_path}.",
            detail=f"Searched for: {SUPPORTED_MANIFESTS}",
        )

    # Load optional license metadata file.
    license_db = _load_license_db(project_path)

    dependencies: list[DependencyInfo] = []
    notes: list[str] = []

    for manifest_path in manifests_found:
        deps, manifest_notes = _parse_manifest(manifest_path, project_path, license_db)
        dependencies.extend(deps)
        notes.extend(manifest_notes)

    # Annotate licenses for deps where the license_db has data.
    for dep in dependencies:
        if not dep.license and dep.name in license_db:
            dep.license = license_db[dep.name]

    unpinned = sum(1 for d in dependencies if _is_unpinned(d.version_spec))
    dev_count = sum(1 for d in dependencies if d.is_dev)
    version_risk_count = sum(1 for d in dependencies if d.risk_flags)
    unknown_license_count = sum(
        1 for d in dependencies
        if not d.license or d.license.lower() in ("unknown", "")
    )

    return DependencySummary(
        project_path=str(project_path),
        manifests_found=[str(m.relative_to(project_path)) for m in manifests_found],
        total=len(dependencies),
        dev_count=dev_count,
        unpinned_count=unpinned,
        version_risk_count=version_risk_count,
        unknown_license_count=unknown_license_count,
        dependencies=dependencies,
        notes=notes,
    )


# ── Manifest discovery ────────────────────────────────────────────────────────

def _discover_manifests(project_path: Path) -> list[Path]:
    found: list[Path] = []
    for name in SUPPORTED_MANIFESTS:
        candidate = project_path / name
        if candidate.is_file():
            found.append(candidate)
    return found


# ── License DB ────────────────────────────────────────────────────────────────

def _load_license_db(project_path: Path) -> dict[str, str]:
    """Load metadata/licenses.json if it exists, else return empty dict."""
    candidate = project_path / "metadata" / "licenses.json"
    if not candidate.is_file():
        return {}
    try:
        return json.loads(candidate.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


# ── Per-manifest parsers ──────────────────────────────────────────────────────

def _parse_manifest(
    manifest_path: Path,
    project_root: Path,
    license_db: dict[str, str],
) -> tuple[list[DependencyInfo], list[str]]:
    """Route to the appropriate parser based on filename."""
    name = manifest_path.name

    if name == "requirements.txt":
        return _parse_requirements_txt(manifest_path, license_db)
    if name == "package.json":
        return _parse_package_json(manifest_path, license_db)
    if name == "pyproject.toml":
        return _parse_pyproject_toml(manifest_path, license_db)

    # Unknown manifest type — record as a note, return no deps.
    return [], [f"No parser for {name} yet — skipped."]


# ── requirements.txt ──────────────────────────────────────────────────────────

_REQ_LINE = re.compile(r"^\s*([A-Za-z0-9_\-\.]+)\s*([^#\s]*)?")


def _parse_requirements_txt(
    path: Path, license_db: dict[str, str]
) -> tuple[list[DependencyInfo], list[str]]:
    deps: list[DependencyInfo] = []
    notes: list[str] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue

        m = _REQ_LINE.match(line)
        if not m:
            continue

        pkg_name = m.group(1)
        version_spec = (m.group(2) or "").strip()
        risk_flags = _version_risk_flags(version_spec, ecosystem="pip")

        deps.append(
            DependencyInfo(
                name=pkg_name,
                version_spec=version_spec,
                manifest_file=path.name,
                is_dev=False,
                license=license_db.get(pkg_name, ""),
                risk_flags=risk_flags,
            )
        )

    return deps, notes


# ── package.json ──────────────────────────────────────────────────────────────

def _parse_package_json(
    path: Path, license_db: dict[str, str]
) -> tuple[list[DependencyInfo], list[str]]:
    deps: list[DependencyInfo] = []
    notes: list[str] = []

    try:
        data: dict = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [], [f"Could not parse {path.name}: {exc}"]

    prod_deps: dict = data.get("dependencies", {})
    dev_deps: dict = data.get("devDependencies", {})

    for pkg_name, version_spec in prod_deps.items():
        risk_flags = _version_risk_flags(str(version_spec), ecosystem="npm")
        deps.append(
            DependencyInfo(
                name=pkg_name,
                version_spec=str(version_spec),
                manifest_file=path.name,
                is_dev=False,
                license=license_db.get(pkg_name, ""),
                risk_flags=risk_flags,
            )
        )

    for pkg_name, version_spec in dev_deps.items():
        risk_flags = _version_risk_flags(str(version_spec), ecosystem="npm")
        deps.append(
            DependencyInfo(
                name=pkg_name,
                version_spec=str(version_spec),
                manifest_file=path.name,
                is_dev=True,
                license=license_db.get(pkg_name, ""),
                risk_flags=risk_flags,
            )
        )

    return deps, notes


# ── pyproject.toml (minimal) ──────────────────────────────────────────────────

_TOML_DEP_LINE = re.compile(r"""["']?([A-Za-z0-9_\-\.]+)\s*([><=!~^][^"',\s]*)?""")


def _parse_pyproject_toml(
    path: Path, license_db: dict[str, str]
) -> tuple[list[DependencyInfo], list[str]]:
    """Very lightweight TOML dependency extractor (no external TOML library)."""
    deps: list[DependencyInfo] = []
    notes: list[str] = []
    in_deps = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if line in ('[project.dependencies]', 'dependencies = ['):
            in_deps = True
            continue
        if line.startswith('[') and in_deps:
            in_deps = False

        if not in_deps:
            # Check for inline array: dependencies = ["pkg>=1.0", ...]
            if "dependencies" in line and "=" in line:
                # Pull strings from the line
                for match in re.finditer(r'"([^"]+)"', line):
                    dep_str = match.group(1)
                    m = _TOML_DEP_LINE.match(dep_str)
                    if m and m.group(1):
                        name = m.group(1)
                        spec = m.group(2) or ""
                        risk_flags = _version_risk_flags(spec, ecosystem="pip")
                        deps.append(
                            DependencyInfo(
                                name=name,
                                version_spec=spec,
                                manifest_file=path.name,
                                is_dev=False,
                                license=license_db.get(name, ""),
                                risk_flags=risk_flags,
                            )
                        )
        else:
            # Inside multi-line array
            for match in re.finditer(r'"([^"]+)"', line):
                dep_str = match.group(1)
                m = _TOML_DEP_LINE.match(dep_str)
                if m and m.group(1):
                    name = m.group(1)
                    spec = m.group(2) or ""
                    risk_flags = _version_risk_flags(spec, ecosystem="pip")
                    deps.append(
                        DependencyInfo(
                            name=name,
                            version_spec=spec,
                            manifest_file=path.name,
                            is_dev=False,
                            license=license_db.get(name, ""),
                            risk_flags=risk_flags,
                        )
                    )

    if not deps:
        notes.append(f"No dependencies extracted from {path.name} (complex TOML not fully parsed).")

    return deps, notes


# ── Version risk helpers ──────────────────────────────────────────────────────

def _version_risk_flags(version_spec: str, ecosystem: str = "pip") -> list[str]:
    """Return a list of risk labels for a version specifier."""
    flags: list[str] = []
    spec = version_spec.strip()

    if not spec:
        flags.append("unpinned")
        return flags

    if spec in ("*", "latest", "x"):
        flags.append("wildcard")
        return flags

    if ecosystem == "npm":
        if spec.startswith("^"):
            flags.append("wide_range")
        elif spec.startswith("~"):
            flags.append("patch_range")
        elif not re.match(r"^\d", spec):
            flags.append("unpinned")
    else:  # pip
        if "==" not in spec:
            flags.append("unpinned")

    return flags


def _is_unpinned(version_spec: str) -> bool:
    """Return True if the version spec does not pin to an exact version."""
    if not version_spec or version_spec in ("*", "latest", ""):
        return True
    return "==" not in version_spec and not re.match(r"^\d+\.\d+", version_spec)
