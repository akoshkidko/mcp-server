"""Shared Pydantic v2 models for RepoHealth MCP requests, responses, and domain objects.

Keep models focused on data shape — no business logic here.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from repohealth_mcp.core.constants import HealthStatus, Severity


# ── Error envelope ────────────────────────────────────────────────────────────

class ToolError(BaseModel):
    """Returned by MCP tools when an error prevents normal output."""

    error: str
    detail: str | None = None
    tool: str | None = None


# ── Tech debt models ──────────────────────────────────────────────────────────

class TechDebtFinding(BaseModel):
    """A single tech-debt annotation found in source code."""

    file: str = Field(description="Path relative to the project root.")
    line: int = Field(description="1-based line number of the annotation.")
    marker: str = Field(description="The debt marker keyword, e.g. TODO or FIXME.")
    severity: Severity = Severity.LOW
    text: str = Field(default="", description="The raw annotation text.")


class TechDebtSummary(BaseModel):
    """Aggregated tech-debt scan results for a project."""

    project_path: str
    total_findings: int = 0
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_marker: dict[str, int] = Field(default_factory=dict)
    findings: list[TechDebtFinding] = Field(default_factory=list)
    scanned_files: int = 0


# ── CI log models ─────────────────────────────────────────────────────────────

class LogLine(BaseModel):
    """A single matched line from a CI log."""

    line_number: int
    content: str
    category: str = Field(description="'error' | 'warning' | 'info'")


class LogDiagnosis(BaseModel):
    """Diagnosis result for a CI log file."""

    log_path: str
    total_lines: int = 0
    errors: list[LogLine] = Field(default_factory=list)
    warnings: list[LogLine] = Field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    summary: str = ""


# ── Dependency models ─────────────────────────────────────────────────────────

class DependencyInfo(BaseModel):
    """Information about a single declared dependency."""

    name: str
    version_spec: str = Field(default="", description="Version specifier as declared.")
    manifest_file: str = Field(description="Source manifest filename.")
    is_dev: bool = False
    notes: list[str] = Field(default_factory=list)


class DependencySummary(BaseModel):
    """Aggregated dependency analysis for a project."""

    project_path: str
    manifests_found: list[str] = Field(default_factory=list)
    total: int = 0
    dev_count: int = 0
    unpinned_count: int = 0
    dependencies: list[DependencyInfo] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


# ── Health report model ───────────────────────────────────────────────────────

class HealthReport(BaseModel):
    """Top-level aggregated health report for a project."""

    project_path: str
    health_score: float = Field(
        ge=0.0, le=1.0, description="Normalised score; 1.0 = perfectly healthy."
    )
    health_status: HealthStatus = HealthStatus.UNKNOWN
    tech_debt: TechDebtSummary | None = None
    ci_diagnosis: LogDiagnosis | None = None
    dependencies: DependencySummary | None = None
    notes: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
