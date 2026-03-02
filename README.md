# RepoHealth MCP

A local Dockerized MCP (Model Context Protocol) server that helps developers quickly triage a problematic repository.

## Tools

| Tool | Description |
|------|-------------|
| `scan_tech_debt` | Scan source files for tech debt markers (TODO, FIXME, HACK, etc.) |
| `diagnose_ci_logs` | Parse CI/CD log files and surface errors, warnings, and failure patterns |
| `analyze_dependencies` | Inspect manifest files for outdated, vulnerable, or missing dependencies |
| `project_health_report` | Aggregate all analyses into a single scored health report |

## Architecture

```
src/repohealth_mcp/
├── cli.py              # CLI router (serve | smoke subcommands)
├── app.py              # FastAPI application factory
├── server.py           # Uvicorn entrypoint
├── smoke.py            # Smoke test runner
├── config.py           # Centralized configuration
├── transport/
│   ├── health.py       # /health HTTP endpoint
│   └── mcp_factory.py  # MCP tool registration layer
├── core/
│   ├── models.py       # Shared Pydantic models
│   ├── errors.py       # Custom exceptions
│   ├── paths.py        # Safe path resolution
│   ├── scoring.py      # Health scoring logic
│   └── constants.py    # Shared constants and enums
├── analyzers/
│   ├── tech_debt.py    # Tech debt scanner
│   ├── ci_logs.py      # CI log diagnostics
│   ├── dependencies.py # Dependency analysis
│   └── report.py       # Health report aggregator
└── utils/
    ├── file_io.py      # File reading helpers
    └── text.py         # Text processing helpers
```

**Design principles:**
- **Thin transport layer** — MCP/HTTP code only adapts inputs and calls analyzers.
- **Independent core** — All analyzers are plain Python functions testable without MCP.
- **Typed models** — Pydantic v2 models for all inputs/outputs.
- **Centralized errors** — Custom exception hierarchy in `core/errors.py`.

## Quick Start

### Docker

```bash
# Build
docker build -t repohealth-mcp .

# Start server (default: bare run also starts serve)
docker run --rm -p 8000:8000 repohealth-mcp serve

# Run smoke checks
docker run --rm repohealth-mcp smoke

# Mount a local repo for analysis
docker run --rm -p 8000:8000 -v /path/to/your/repo:/workspace repohealth-mcp serve
```

### Local Development

```bash
pip install -e ".[dev]"
repohealth-serve          # start the server on http://localhost:8000
repohealth-smoke          # run smoke checks
pytest                    # run tests
```

### Health Check

```bash
curl http://localhost:8000/health
```

### MCP Inspector

Connect [MCP Inspector](https://github.com/modelcontextprotocol/inspector) to:

```
http://localhost:8000/mcp
```

Select **Streamable HTTP** as the transport type.  
The MCP endpoint accepts both `POST /mcp` (JSON-RPC requests) and `GET /mcp` (SSE notification stream).

## CLI Reference

The container ENTRYPOINT is `python -m repohealth_mcp.cli`.

| Command | Behaviour |
|---------|-----------|
| `docker run IMAGE` | Defaults to `serve` — starts the server on port 8000 |
| `docker run IMAGE serve` | Starts the MCP/HTTP server on port 8000 |
| `docker run IMAGE smoke` | Runs smoke checks; exits 0 on pass, 1 on fail |

## Configuration

See `src/repohealth_mcp/config.py` for all tuneable settings.  
All settings are overridable via `REPOHEALTH_*` environment variables.

| Setting | Default | Description |
|---------|---------|-------------|
| `REPOHEALTH_PORT` | `8000` | Server port |
| `REPOHEALTH_ALLOWED_ROOTS` | `["/workspace", "/demo_project"]` | Paths the server may access |
| `REPOHEALTH_SCORE_THRESHOLD_HEALTHY` | `0.8` | Score above which status is `"healthy"` |
| `REPOHEALTH_SCORE_THRESHOLD_WARNING` | `0.5` | Lower bound for `"needs_attention"` status (score between this value and `THRESHOLD_HEALTHY`); below this threshold → `"critical"` |

## Demo Project

`demo_project/` contains a realistic fixture repository with intentional tech debt, a failing pytest log, and mixed dependency manifests.  It is baked into the Docker image at `/demo_project` and is accessible by default (the server's `allowed_roots` includes `/demo_project`).

| Fixture | Purpose |
|---------|---------|
| `src/auth.py` | FIXME auth bypass + BUG token expiry → HIGH/CRITICAL debt findings |
| `src/service.py` | HACK comment + 500/200 mismatch → tech debt + CI failure correlation |
| `logs/pytest_failure.log` | Real pytest output with `assert 500 == 200` → `test_assertion_failure` |
| `requirements.txt` + `package.json` | Pinned + unpinned deps + wildcard → version risks |
| `metadata/licenses.json` | `legacy-lib: unknown` → unknown license detection |

See `DEMO.md` for a complete 3–5 minute walkthrough using MCP Inspector.

## License

MIT
 
