FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency metadata first for layer caching
COPY pyproject.toml ./

# Install the package in editable mode with all dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e ".[dev]"

# Copy source
COPY src/ ./src/
COPY tests/ ./tests/
COPY demo_project/ ./demo_project/

# Non-root user for security
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# CLI router handles: serve | smoke
# Default CMD is "serve" so bare `docker run IMAGE` starts the server.
ENTRYPOINT ["python", "-m", "repohealth_mcp.cli"]
CMD ["serve"]
