"""Centralized configuration for RepoHealth MCP.

Settings are read from environment variables (with defaults) via pydantic-settings.
Override any value by setting the corresponding env var, e.g. ``REPOHEALTH_PORT=9000``.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REPOHEALTH_", case_sensitive=False)

    # ── Service identity ────────────────────────────────────────────────────
    service_name: str = "repohealth-mcp"
    version: str = "0.1.0"

    # ── Network ─────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Path security ───────────────────────────────────────────────────────
    # Comma-separated list of filesystem roots the server is allowed to read.
    # Requests for paths outside these roots are rejected.
    allowed_roots: list[str] = ["/workspace"]

    # ── Glob patterns ───────────────────────────────────────────────────────
    default_include_globs: list[str] = [
        "**/*.py",
        "**/*.js",
        "**/*.ts",
        "**/*.go",
        "**/*.java",
        "**/*.rb",
        "**/*.rs",
    ]
    default_exclude_globs: list[str] = [
        "**/node_modules/**",
        "**/.git/**",
        "**/__pycache__/**",
        "**/dist/**",
        "**/build/**",
        "**/.venv/**",
        "**/venv/**",
    ]

    # ── Health score thresholds ─────────────────────────────────────────────
    # Scores are normalised floats in [0.0, 1.0] (higher = healthier).
    score_threshold_healthy: float = 0.8
    score_threshold_warning: float = 0.5
    # Below warning threshold is considered "critical".

    # ── Tech debt ───────────────────────────────────────────────────────────
    max_debt_findings_before_penalty: int = 20


settings = Settings()
