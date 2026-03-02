"""Health report aggregator.

Composes the tech_debt, ci_logs, and dependencies analyzers and merges their
output into a single ``HealthReport``.

Important: this module calls analyzer functions directly — it must never
make MCP tool calls or HTTP requests.
"""

from pathlib import Path

from repohealth_mcp.analyzers.ci_logs import diagnose_ci_log
from repohealth_mcp.analyzers.dependencies import analyze_dependencies
from repohealth_mcp.analyzers.tech_debt import scan_tech_debt
from repohealth_mcp.config import settings
from repohealth_mcp.core.errors import RepoHealthError
from repohealth_mcp.core.models import DependencySummary, HealthReport, LogDiagnosis, TechDebtSummary
from repohealth_mcp.core.scoring import (
    compute_overall_score,
    score_ci_health,
    score_dependencies,
    score_tech_debt,
    score_to_status,
)


def build_project_health_report(
    project_path: Path,
    ci_log_path: Path | None = None,
    include_globs: list[str] | None = None,
    exclude_globs: list[str] | None = None,
) -> HealthReport:
    """Run all analyzers and return an aggregated ``HealthReport``.

    Each analyzer is run independently; failures are captured as notes rather
    than raising, so a partial report is returned even when one dimension fails.

    Args:
        project_path: Resolved, validated project root directory.
        ci_log_path:  Optional path to a CI log file.  When ``None``, the CI
            dimension is omitted from the health score.
        include_globs: File globs forwarded to the tech debt scanner.
        exclude_globs: Exclusion globs forwarded to the tech debt scanner.

    Returns:
        A ``HealthReport`` with scores for every available dimension.

    TODO: Add concurrency — run analyzers in parallel with asyncio.gather.
    TODO: Accept a callback / progress hook for long-running projects.
    """
    notes: list[str] = []

    # ── Tech debt ────────────────────────────────────────────────────────────
    tech_debt: TechDebtSummary | None = None
    tech_debt_score: float | None = None
    try:
        tech_debt = scan_tech_debt(
            project_path,
            include_globs=include_globs,
            exclude_globs=exclude_globs,
        )
        tech_debt_score = score_tech_debt(
            tech_debt,
            max_findings=settings.max_debt_findings_before_penalty,
        )
    except RepoHealthError as exc:
        notes.append(f"Tech debt analysis skipped: {exc}")
    except Exception as exc:  # noqa: BLE001
        notes.append(f"Tech debt analysis failed unexpectedly: {exc}")

    # ── CI log ───────────────────────────────────────────────────────────────
    ci_diagnosis: LogDiagnosis | None = None
    ci_score: float | None = None
    if ci_log_path is not None:
        try:
            ci_diagnosis = diagnose_ci_log(ci_log_path)
            ci_score = score_ci_health(ci_diagnosis)
        except RepoHealthError as exc:
            notes.append(f"CI log analysis skipped: {exc}")
        except Exception as exc:  # noqa: BLE001
            notes.append(f"CI log analysis failed unexpectedly: {exc}")

    # ── Dependencies ─────────────────────────────────────────────────────────
    dep_summary: DependencySummary | None = None
    dep_score: float | None = None
    try:
        dep_summary = analyze_dependencies(project_path)
        dep_score = score_dependencies(dep_summary)
    except RepoHealthError as exc:
        notes.append(f"Dependency analysis skipped: {exc}")
    except Exception as exc:  # noqa: BLE001
        notes.append(f"Dependency analysis failed unexpectedly: {exc}")

    # ── Aggregate ────────────────────────────────────────────────────────────
    overall_score = compute_overall_score(
        tech_debt_score=tech_debt_score,
        ci_score=ci_score,
        dep_score=dep_score,
    )
    health_status = score_to_status(
        overall_score,
        threshold_healthy=settings.score_threshold_healthy,
        threshold_warning=settings.score_threshold_warning,
    )

    return HealthReport(
        project_path=str(project_path),
        health_score=overall_score,
        health_status=health_status,
        tech_debt=tech_debt,
        ci_diagnosis=ci_diagnosis,
        dependencies=dep_summary,
        notes=notes,
    )
