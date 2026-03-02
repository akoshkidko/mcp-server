"""Custom exception hierarchy for RepoHealth MCP.

All domain errors extend ``RepoHealthError`` so callers can catch the base
class when they don't need to distinguish between specific failure modes.
"""


class RepoHealthError(Exception):
    """Base class for all RepoHealth domain errors."""

    def __init__(self, message: str, *, detail: str | None = None) -> None:
        super().__init__(message)
        self.detail = detail or message


# ── Path / access errors ─────────────────────────────────────────────────────

class InvalidProjectPathError(RepoHealthError):
    """Raised when the given project path does not exist or is not a directory."""


class PathOutsideAllowedRootError(RepoHealthError):
    """Raised when a resolved path falls outside every allowed filesystem root."""


# ── Log analysis errors ──────────────────────────────────────────────────────

class LogFileNotFoundError(RepoHealthError):
    """Raised when the specified CI log file cannot be located."""


class EmptyLogFileError(RepoHealthError):
    """Raised when a log file exists but contains no content."""


# ── Dependency analysis errors ───────────────────────────────────────────────

class NoManifestsFoundError(RepoHealthError):
    """Raised when no recognised dependency manifests are found in the project."""
