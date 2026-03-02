"""Health scoring logic for RepoHealth MCP.

Scores are normalised floats in [0.0, 1.0] where 1.0 = perfectly healthy.
Each dimension (tech debt, CI health, dependency health) produces a
sub-score; the final score is a weighted average of those.
"""

from repohealth_mcp.core.constants import HealthStatus
from repohealth_mcp.core.models import DependencySummary, LogDiagnosis, TechDebtSummary


# ── Sub-scorers ───────────────────────────────────────────────────────────────

def score_tech_debt(summary: TechDebtSummary, max_findings: int = 20) -> float:
    """Return a [0, 1] score based on tech debt findings.

    The score degrades linearly as findings approach *max_findings*, then
    is clamped at 0.0 for projects with excessive debt.

    TODO: factor in severity weighting (FIXME/BUG should penalise harder than TODO).
    TODO: normalise by lines-of-code for large projects.
    """
    if summary.total_findings == 0:
        return 1.0
    penalty = min(summary.total_findings / max_findings, 1.0)
    return round(1.0 - penalty, 4)


def score_ci_health(diagnosis: LogDiagnosis) -> float:
    """Return a [0, 1] score based on CI log errors and warnings.

    TODO: weight errors more heavily than warnings.
    TODO: distinguish fatal from non-fatal patterns.
    """
    if diagnosis.total_lines == 0:
        return 1.0
    issue_count = diagnosis.error_count + diagnosis.warning_count * 0.5
    penalty = min(issue_count / 50, 1.0)
    return round(1.0 - penalty, 4)


def score_dependencies(summary: DependencySummary) -> float:
    """Return a [0, 1] score based on dependency health.

    TODO: integrate with a vulnerability database (e.g. OSV, GitHub Advisory).
    TODO: penalise heavily unpinned production dependencies.
    """
    if summary.total == 0:
        return 1.0
    unpinned_ratio = summary.unpinned_count / summary.total
    return round(1.0 - unpinned_ratio * 0.8, 4)


# ── Aggregator ────────────────────────────────────────────────────────────────

# Dimension weights must sum to 1.0
_WEIGHTS: dict[str, float] = {
    "tech_debt": 0.35,
    "ci": 0.35,
    "dependencies": 0.30,
}


def compute_overall_score(
    tech_debt_score: float | None = None,
    ci_score: float | None = None,
    dep_score: float | None = None,
) -> float:
    """Compute a weighted overall health score from available sub-scores.

    Dimensions with no data (``None``) are excluded and remaining weights
    are redistributed proportionally.
    """
    available: dict[str, float] = {}
    if tech_debt_score is not None:
        available["tech_debt"] = tech_debt_score
    if ci_score is not None:
        available["ci"] = ci_score
    if dep_score is not None:
        available["dependencies"] = dep_score

    if not available:
        return 0.0

    total_weight = sum(_WEIGHTS[k] for k in available)
    weighted_sum = sum(_WEIGHTS[k] * v for k, v in available.items())
    return round(weighted_sum / total_weight, 4)


def score_to_status(
    score: float,
    threshold_healthy: float = 0.8,
    threshold_warning: float = 0.5,
) -> HealthStatus:
    """Map a numeric score to a ``HealthStatus`` enum value."""
    if score >= threshold_healthy:
        return HealthStatus.HEALTHY
    if score >= threshold_warning:
        return HealthStatus.NEEDS_ATTENTION
    return HealthStatus.CRITICAL
