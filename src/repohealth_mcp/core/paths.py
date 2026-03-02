"""Safe path resolution and allowed-root enforcement.

All filesystem access in analyzers should go through these helpers to prevent
path-traversal issues and ensure the server only touches permitted directories.
"""

from pathlib import Path

from repohealth_mcp.core.errors import InvalidProjectPathError, PathOutsideAllowedRootError


def resolve_project_path(raw_path: str) -> Path:
    """Resolve *raw_path* to an absolute, normalised ``Path``.

    Raises:
        InvalidProjectPathError: If the resolved path does not exist or is not
            a directory.
    """
    path = Path(raw_path).expanduser().resolve()
    if not path.exists():
        raise InvalidProjectPathError(
            f"Project path does not exist: {path}",
            detail=f"Received: {raw_path!r}",
        )
    if not path.is_dir():
        raise InvalidProjectPathError(
            f"Project path is not a directory: {path}",
            detail=f"Received: {raw_path!r}",
        )
    return path


def assert_within_allowed_roots(path: Path, allowed_roots: list[str]) -> None:
    """Raise if *path* is not under at least one of *allowed_roots*.

    Raises:
        PathOutsideAllowedRootError: If no allowed root contains *path*.
    """
    resolved = path.resolve()
    for root in allowed_roots:
        allowed = Path(root).expanduser().resolve()
        try:
            resolved.relative_to(allowed)
            return  # found a valid root
        except ValueError:
            continue

    raise PathOutsideAllowedRootError(
        f"Path {resolved} is outside all allowed roots.",
        detail=f"Allowed roots: {allowed_roots}",
    )


def safe_resolve(raw_path: str, allowed_roots: list[str]) -> Path:
    """Convenience wrapper: resolve and enforce allowed roots in one call.

    Returns the resolved ``Path`` if all checks pass.
    """
    path = resolve_project_path(raw_path)
    assert_within_allowed_roots(path, allowed_roots)
    return path


def relative_to_project(file_path: Path, project_root: Path) -> str:
    """Return *file_path* as a string relative to *project_root*.

    Falls back to the absolute path string if *file_path* is not under the root.
    """
    try:
        return str(file_path.relative_to(project_root))
    except ValueError:
        return str(file_path)
