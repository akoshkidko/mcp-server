"""Shared constants and enumerations for the RepoHealth MCP domain."""

from enum import Enum


# ── Tech debt markers ────────────────────────────────────────────────────────

class DebtMarker(str, Enum):
    TODO = "TODO"
    FIXME = "FIXME"
    HACK = "HACK"
    XXX = "XXX"
    BUG = "BUG"
    NOQA = "NOQA"
    DEPRECATED = "DEPRECATED"


# Ordered from most to least severe for display purposes.
DEBT_MARKERS: list[str] = [m.value for m in DebtMarker]


# ── Severity ─────────────────────────────────────────────────────────────────

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# Maps individual debt markers to a default severity level.
DEBT_MARKER_SEVERITY: dict[str, Severity] = {
    DebtMarker.BUG: Severity.CRITICAL,
    DebtMarker.FIXME: Severity.HIGH,
    DebtMarker.HACK: Severity.HIGH,
    DebtMarker.XXX: Severity.MEDIUM,
    DebtMarker.TODO: Severity.LOW,
    DebtMarker.DEPRECATED: Severity.MEDIUM,
    DebtMarker.NOQA: Severity.INFO,
}


# ── Health status ─────────────────────────────────────────────────────────────

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


# ── Dependency manifest filenames ────────────────────────────────────────────

SUPPORTED_MANIFESTS: list[str] = [
    "requirements.txt",
    "requirements-dev.txt",
    "Pipfile",
    "Pipfile.lock",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "go.mod",
    "go.sum",
    "Cargo.toml",
    "Cargo.lock",
    "Gemfile",
    "Gemfile.lock",
    "composer.json",
    "composer.lock",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
]


# ── CI log patterns ──────────────────────────────────────────────────────────

CI_ERROR_PATTERNS: list[str] = [
    r"\berror\b",
    r"\bfailed\b",
    r"\bfailure\b",
    r"\bexception\b",
    r"\bcritical\b",
    r"exit code [1-9]",
]

CI_WARNING_PATTERNS: list[str] = [
    r"\bwarning\b",
    r"\bwarn\b",
    r"\bdeprecated\b",
    r"\bskipped\b",
]
