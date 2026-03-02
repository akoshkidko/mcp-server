# demo_project

A realistic fixture repository used for integration testing and demonstrations
of the RepoHealth MCP server.

## Purpose

- Smoke tests verify that `demo_project/` is present and accessible.
- All four MCP tools are designed to run against this directory and produce
  deterministic, meaningful outputs (see `DEMO.md` in the project root).

## Structure

```
demo_project/
├── README.md           ← this file
├── pyproject.toml      ← Python project with unpinned deps for risk detection
├── requirements.txt    ← mixed pinned/unpinned Python deps
├── package.json        ← Node.js deps with wildcard and wide-range versions
├── Dockerfile          ← container stub
├── src/                ← source with intentional TODO/FIXME/HACK/BUG markers
├── tests/              ← tests including one that intentionally fails
├── logs/               ← CI log fixtures
│   ├── pytest_failure.log        ← realistic pytest failure (assert 500 == 200)
│   ├── npm_build_failure.log     ← npm error output
│   └── docker_build_failure.log  ← Docker build error output
├── docs/               ← notes with TODO markers
└── metadata/
    └── licenses.json   ← local license mapping (includes unknown entry)
```

## Tool Outputs (summary)

| Tool | Key result |
|------|-----------|
| `scan_tech_debt` | 9 findings, 5 HIGH/CRITICAL |
| `diagnose_ci_logs` (`pytest_failure.log`) | `test_assertion_failure`, confidence 0.95 |
| `analyze_dependencies` | 7 version risks, 1 unknown license |
| `project_health_report` | score ~0.66, status `needs_attention` |

See `DEMO.md` in the project root for the full step-by-step walkthrough.
