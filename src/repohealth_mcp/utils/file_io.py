"""File I/O helpers used by the analyzer layer.

All functions are pure I/O utilities with no domain logic.
"""

import fnmatch
from pathlib import Path
from typing import Generator

# Default globs used when callers do not specify their own.
_DEFAULT_INCLUDE = [
    "**/*.py", "**/*.js", "**/*.ts", "**/*.go",
    "**/*.java", "**/*.rb", "**/*.rs", "**/*.cpp", "**/*.c",
]
_DEFAULT_EXCLUDE = [
    "**/node_modules/**", "**/.git/**", "**/__pycache__/**",
    "**/dist/**", "**/build/**", "**/.venv/**", "**/venv/**",
]


def iter_text_files(
    root: Path,
    include_globs: list[str] | None = None,
    exclude_globs: list[str] | None = None,
) -> Generator[tuple[Path, list[str]], None, None]:
    """Yield ``(file_path, lines)`` for every text file under *root* matching the globs.

    Args:
        root: Directory to walk.
        include_globs: Files must match at least one of these patterns.
        exclude_globs: Files matching any of these patterns are skipped.

    Yields:
        A tuple of (absolute path, list of lines without newlines).

    TODO: Use gitignore-aware walking (e.g. pathspec library) instead of
          simple glob matching to respect project exclusion files.
    TODO: Add a max-file-size guard to skip binary/large files gracefully.
    """
    includes = include_globs or _DEFAULT_INCLUDE
    excludes = exclude_globs or _DEFAULT_EXCLUDE

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue

        rel = file_path.relative_to(root).as_posix()

        if any(fnmatch.fnmatch(rel, pat.lstrip("*/")) or fnmatch.fnmatch(rel, pat) for pat in excludes):
            continue

        if not any(fnmatch.fnmatch(rel, pat.lstrip("*/")) or fnmatch.fnmatch(file_path.name, pat.lstrip("*/")) for pat in includes):
            # Also try matching just the filename against the suffix part of the glob.
            if not any(file_path.match(pat) for pat in includes):
                continue

        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        yield file_path, text.splitlines()


def read_text_file(path: Path) -> str:
    """Read and return the text contents of *path*.

    Returns an empty string if the file cannot be read rather than raising,
    so callers can decide how to handle missing content.
    """
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
