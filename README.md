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
docker build -t repohealth-mcp .
docker run -p 8000:8000 -v /path/to/your/repo:/workspace repohealth-mcp
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

The MCP endpoint is a **Streamable HTTP** transport — it accepts both `POST /mcp`
(JSON-RPC requests) and `GET /mcp` (SSE server-notification stream).

## Configuration

See `src/repohealth_mcp/config.py` for all tuneable settings.

| Setting | Default | Description |
|---------|---------|-------------|
| `PORT` | `8000` | Server port |
| `ALLOWED_ROOTS` | `["/workspace"]` | Paths the server may access |
| `DEBT_SCORE_THRESHOLD_WARN` | `0.6` | Health score that triggers a warning |
| `DEBT_SCORE_THRESHOLD_CRITICAL` | `0.3` | Health score that triggers a critical alert |

## Demo Project

`demo_project/` contains a minimal placeholder repository used for integration testing and demonstrations.

## License

MIT
