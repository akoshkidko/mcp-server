"""MCP server factory — creates and configures the FastMCP server with all tools.

Responsibilities:
- Build a ``FastMCP`` instance and register the 4 RepoHealth tools.
- Each tool validates its inputs via ``core/paths.py`` and delegates to the
  corresponding analyzer function.  No analysis logic lives here.

The ``create_mcp_server()`` function is consumed by ``app.py``, which handles
ASGI mounting and session-manager lifecycle via FastAPI's lifespan.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from repohealth_mcp.config import settings
from repohealth_mcp.core.paths import assert_within_allowed_roots, safe_resolve

logger = logging.getLogger(__name__)


def create_mcp_server() -> FastMCP:
    """Build a ``FastMCP`` instance with all four RepoHealth tools registered.

    ``streamable_http_path="/"`` means that when this app is mounted at
    ``/mcp`` in FastAPI, the MCP Streamable HTTP endpoint is exactly
    ``/mcp`` — not ``/mcp/mcp``.
    """
    mcp = FastMCP(
        "RepoHealth MCP",
        streamable_http_path="/",
    )

    # ── Tool: scan_tech_debt ─────────────────────────────────────────────────

    @mcp.tool(
        description=(
            "Scan a project directory for tech debt annotations "
            "(TODO, FIXME, HACK, BUG, XXX, DEPRECATED). "
            "Returns a structured summary with per-severity and per-marker counts."
        )
    )
    def scan_tech_debt(
        project_path: str,
        include_globs: list[str] | None = None,
        exclude_globs: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Args:
            project_path: Absolute path to the project root.
            include_globs: File patterns to include (e.g. ["**/*.py"]).
                Defaults to common source extensions when omitted.
            exclude_globs: File patterns to skip (e.g. ["**/node_modules/**"]).
        """
        from repohealth_mcp.analyzers.tech_debt import scan_tech_debt as _analyze

        path = safe_resolve(project_path, settings.allowed_roots)
        result = _analyze(path, include_globs=include_globs, exclude_globs=exclude_globs)
        return result.model_dump(mode="json")

    # ── Tool: diagnose_ci_logs ───────────────────────────────────────────────

    @mcp.tool(
        description=(
            "Parse a CI/CD log file and surface errors, warnings, and failure patterns. "
            "Works with plain-text logs from GitHub Actions, GitLab CI, Jenkins, etc."
        )
    )
    def diagnose_ci_logs(log_path: str) -> dict[str, Any]:
        """
        Args:
            log_path: Absolute path to the CI log file.
        """
        from repohealth_mcp.analyzers.ci_logs import diagnose_ci_log as _analyze

        resolved = Path(log_path).expanduser().resolve()
        assert_within_allowed_roots(resolved, settings.allowed_roots)
        result = _analyze(resolved)
        return result.model_dump(mode="json")

    # ── Tool: analyze_dependencies ───────────────────────────────────────────

    @mcp.tool(
        description=(
            "Inspect dependency manifest files in a project directory "
            "(requirements.txt, package.json, pyproject.toml, Cargo.toml, etc.). "
            "Returns a summary of discovered manifests and declared dependencies."
        )
    )
    def analyze_dependencies(project_path: str) -> dict[str, Any]:
        """
        Args:
            project_path: Absolute path to the project root.
        """
        from repohealth_mcp.analyzers.dependencies import analyze_dependencies as _analyze

        path = safe_resolve(project_path, settings.allowed_roots)
        result = _analyze(path)
        return result.model_dump(mode="json")

    # ── Tool: project_health_report ──────────────────────────────────────────

    @mcp.tool(
        description=(
            "Run all analyses (tech debt, CI logs, dependencies) and return "
            "an aggregated health score in [0, 1] with a status label "
            "(healthy / warning / critical)."
        )
    )
    def project_health_report(
        project_path: str,
        ci_log_path: str | None = None,
    ) -> dict[str, Any]:
        """
        Args:
            project_path: Absolute path to the project root.
            ci_log_path:  Optional absolute path to a CI log file.
                          When omitted the CI dimension is excluded from the score.
        """
        from repohealth_mcp.analyzers.report import build_project_health_report as _analyze

        path = safe_resolve(project_path, settings.allowed_roots)
        log = Path(ci_log_path).expanduser().resolve() if ci_log_path else None
        result = _analyze(path, ci_log_path=log)
        return result.model_dump(mode="json")

    logger.info(
        "FastMCP server '%s' created with tools: %s",
        mcp.name,
        [t.name for t in mcp._tool_manager.list_tools()],
    )
    return mcp
