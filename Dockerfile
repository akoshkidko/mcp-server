FROM python:3.12-slim

WORKDIR /app

# ── Dependencies ─────────────────────────────────────────────────────────────
# Copy package metadata AND sources together before installing so that a normal
# (non-editable) install can build and embed the package in one step.
COPY pyproject.toml ./
COPY src/ ./src/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# ── Demo fixtures ────────────────────────────────────────────────────────────
# Copied to /demo_project — the path used throughout DEMO.md and allowed by
# the default REPOHEALTH_ALLOWED_ROOTS (/demo_project is included by default).
COPY demo_project/ /demo_project/

# ── Non-root user ────────────────────────────────────────────────────────────
RUN useradd --create-home appuser \
    && chown -R appuser /app \
    && chmod -R o+rX /demo_project

USER appuser

EXPOSE 8000

# httpx is a runtime dependency so this one-liner is always available.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# CLI router: `serve` starts uvicorn, `smoke` runs smoke checks.
# Bare `docker run IMAGE` defaults to serve via CMD.
ENTRYPOINT ["python", "-m", "repohealth_mcp.cli"]
CMD ["serve"]
