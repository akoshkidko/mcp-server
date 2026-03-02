FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Copy package metadata AND sources before pip so the non-editable install
# can resolve and embed the package in a single reproducible step.
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/

# Install runtime dependencies only — no editable mode, no dev extras.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Demo fixtures at /demo_project — path used in DEMO.md and allowed_roots config.
COPY demo_project/ /demo_project/

# Non-root user; own both the app tree and the demo fixtures.
RUN useradd --create-home appuser \
    && chown -R appuser /app /demo_project

USER appuser

EXPOSE 8000

# httpx is a declared runtime dependency, so this one-liner is always available.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# CLI router: bare `docker run IMAGE` → serve; explicit subcommands also work.
ENTRYPOINT ["python", "-m", "repohealth_mcp.cli"]
CMD ["serve"]
