# RepoHealth MCP — Demo Guide

This document walks through a demonstration of the RepoHealth MCP server using the bundled `demo_project/`.

## Prerequisites

- Docker installed, or Python 3.11+ with the package installed locally.
- The server running on `http://localhost:8000`.

## 1. Build and Start the Server

```bash
# Build the image
docker build -t repohealth-mcp .

# Start the server
docker run --rm -p 8000:8000 repohealth-mcp serve
```

Or locally without Docker:

```bash
pip install -e ".[dev]"
repohealth-serve
```

## 2. Verify Health

```bash
curl http://localhost:8000/health
# {"status": "ok", "service": "repohealth-mcp", "version": "0.1.0"}
```

## 3. Run Smoke Checks

```bash
# Docker
docker run --rm repohealth-mcp smoke

# Local
repohealth-smoke
```

Expected output:

```
RepoHealth MCP — smoke tests
========================================
[OK  ] demo_project exists: demo_project/ found at ...
[OK  ] analyzers importable: all analyzer modules imported successfully
[OK  ] core importable: all core modules imported successfully
[OK  ] app creates cleanly: FastAPI app created: repohealth-mcp v0.1.0
========================================
Smoke tests passed.
```

## 4. Connect MCP Inspector

Open [MCP Inspector](https://github.com/modelcontextprotocol/inspector) and connect to:

```
http://localhost:8000/mcp
```

Select **Streamable HTTP** as the transport type.  
You should see four tools listed: `scan_tech_debt`, `diagnose_ci_logs`,
`analyze_dependencies`, `project_health_report`.

You can also verify the endpoint manually:

```bash
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}'
```

## 5. Tool Demos

> **Note:** Tool invocations below use the MCP protocol. In a real session, your AI assistant
> (e.g. Claude) calls these tools on your behalf.

### scan_tech_debt

Scans a project directory for TODO / FIXME / HACK markers.

```json
{
  "tool": "scan_tech_debt",
  "arguments": {
    "project_path": "/workspace/demo_project",
    "include_globs": ["**/*.py"]
  }
}
```

### diagnose_ci_logs

Parses a CI log file and surfaces errors.

```json
{
  "tool": "diagnose_ci_logs",
  "arguments": {
    "log_path": "/workspace/demo_project/logs/ci.log"
  }
}
```

### analyze_dependencies

Inspects manifest files in a project.

```json
{
  "tool": "analyze_dependencies",
  "arguments": {
    "project_path": "/workspace/demo_project"
  }
}
```

### project_health_report

Runs all analyses and returns an aggregated score.

```json
{
  "tool": "project_health_report",
  "arguments": {
    "project_path": "/workspace/demo_project"
  }
}
```

## 6. Expected Output Shape

```json
{
  "project_path": "/workspace/demo_project",
  "health_score": 0.72,
  "health_status": "warning",
  "tech_debt": { "total_findings": 3, "by_severity": {} },
  "ci_diagnosis": { "errors": [], "warnings": [] },
  "dependencies": { "total": 5, "outdated": 1, "missing": 0 },
  "generated_at": "2025-01-01T00:00:00Z"
}
```

## Next Steps

Once the business logic is implemented, populate `demo_project/` with realistic
fixture files (source with TODOs, a real CI log, manifests with pinned versions)
to make this demo fully runnable end-to-end.
