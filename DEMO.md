# RepoHealth MCP — Demo Guide

End-to-end walkthrough using the bundled `demo_project/` fixtures.  
Estimated time: **3–5 minutes**.

---

## Prerequisites

```bash
# 1. Build the image
docker build -t repohealth-mcp .

# 2. Start the server (demo_project is baked into the image at /demo_project)
docker run --rm -p 8000:8000 repohealth-mcp serve

# 3. Verify it's alive
curl http://localhost:8000/health
# → {"status":"ok","service":"repohealth-mcp","version":"0.1.0"}
```

Open **MCP Inspector** → connect to `http://localhost:8000/mcp`  
(Transport type: **Streamable HTTP**)

You should see 4 tools: `scan_tech_debt`, `diagnose_ci_logs`,
`analyze_dependencies`, `project_health_report`.

> All paths below use `/demo_project` — the path inside the container.
> If you mount an external repo, substitute `/workspace/your-repo`.

---

## Step 1 — scan_tech_debt

**Tool:** `scan_tech_debt`

**Arguments:**
```json
{
  "project_path": "/demo_project"
}
```

**Expected result (abridged):**
```json
{
  "total_findings": 9,
  "scanned_files": 7,
  "by_severity": { "critical": 2, "high": 3, "low": 3, "info": 1 },
  "by_marker":   { "BUG": 2, "FIXME": 1, "HACK": 2, "TODO": 3, "NOQA": 1 },
  "findings": [
    {
      "file": "src/auth.py", "line": 7, "marker": "FIXME", "severity": "high",
      "text": "# FIXME: temporary auth bypass for demo login, remove before production"
    },
    {
      "file": "src/auth.py", "line": 30, "marker": "BUG", "severity": "critical",
      "text": "    # BUG: token has no expiry — sessions live forever"
    }
  ]
}
```

**What to verify:**
- `total_findings` ≥ 6 (actual: **9**)
- `by_severity.critical + by_severity.high` ≥ 1 (actual: **5**)
- `src/auth.py` contains a FIXME (auth bypass) and a BUG (token expiry)
- `src/service.py` contains a HACK marker

---

## Step 2 — diagnose_ci_logs

**Tool:** `diagnose_ci_logs`

**Arguments:**
```json
{
  "log_path": "/demo_project/logs/pytest_failure.log"
}
```

**Expected result:**
```json
{
  "category": "test_assertion_failure",
  "confidence": 0.95,
  "error_count": 2,
  "warning_count": 1,
  "summary": "Detected: Category: test_assertion_failure, 2 error(s), 1 warning(s).",
  "errors": [
    { "line_number": 18, "content": "E       assert 500 == 200", "category": "error" },
    { "line_number": 23, "content": "FAILED tests/test_service.py::test_create_user ...", "category": "error" }
  ]
}
```

**What to verify:**
- `category == "test_assertion_failure"` ✓
- `confidence >= 0.90` (actual: **0.95**) ✓
- Error lines include `E       assert 500 == 200` and the `FAILED` summary line

---

## Step 3 — analyze_dependencies

**Tool:** `analyze_dependencies`

**Arguments:**
```json
{
  "project_path": "/demo_project"
}
```

**Expected result (key fields):**
```json
{
  "manifests_found": ["requirements.txt", "pyproject.toml", "package.json"],
  "total": 10,
  "unpinned_count": 7,
  "version_risk_count": 7,
  "unknown_license_count": 1,
  "dependencies": [
    { "name": "requests",   "version_spec": "==2.28.0", "risk_flags": [],             "license": "Apache-2.0" },
    { "name": "tenacity",   "version_spec": "",          "risk_flags": ["unpinned"],   "license": "Apache-2.0" },
    { "name": "flask",      "version_spec": ">=2.0",     "risk_flags": ["unpinned"],   "license": "BSD-3-Clause" },
    { "name": "express",    "version_spec": "^4.18.2",   "risk_flags": ["wide_range"], "license": "MIT" },
    { "name": "legacy-lib", "version_spec": "*",          "risk_flags": ["wildcard"],   "license": "unknown" },
    { "name": "lodash",     "version_spec": "4.17.21",   "risk_flags": [],             "license": "MIT" }
  ]
}
```

> `requests` and `tenacity` appear twice (once from `requirements.txt`, once from `pyproject.toml`) — this is expected; they represent the same deps declared in two manifests.

**What to verify:**
- `manifests_found` contains `requirements.txt`, `pyproject.toml`, and `package.json`
- `version_risk_count >= 2` (actual: **7**) ✓
- `unknown_license_count >= 1` (actual: **1** — `legacy-lib`) ✓
- `legacy-lib` has `"license": "unknown"` and `"risk_flags": ["wildcard"]`

---

## Step 4 — project_health_report

**Tool:** `project_health_report`

**Arguments:**
```json
{
  "project_path": "/demo_project",
  "ci_log_path":  "/demo_project/logs/pytest_failure.log"
}
```

**Expected result:**
```json
{
  "health_score": 0.657,
  "health_status": "needs_attention",
  "top_issues": [
    "High-severity tech debt: 5 FIXME/BUG marker(s) require immediate attention",
    "Tech debt: 9 annotation(s) across 7 file(s)",
    "Failing tests: assertion failures detected (confidence 95%)",
    "CI log: 2 error line(s) in pytest_failure.log",
    "Dependency risk: 7 package(s) with wildcard / unpinned / wide-range version specs",
    "License risk: 1 package(s) with unknown license"
  ],
  "recommended_actions": [
    "Fix BUG in tests/test_service.py:23 — # BUG: returns 500 — tracked in service.py HACK comment",
    "Fix FIXME in src/auth.py:7 — # FIXME: temporary auth bypass for demo login, remove before production",
    "Fix BUG in src/auth.py:30 — # BUG: token has no expiry — sessions live forever",
    "Fix failing test assertions — check assert values match function return codes",
    "Pin 7 unpinned dependency/ies to exact versions to ensure reproducible builds",
    "Audit packages with unknown license for legal compliance"
  ]
}
```

**What to verify:**
- `health_status == "needs_attention"` ✓
- `health_score` between 0.5 and 0.8 (actual: **0.657**) ✓
- `top_issues` has ≥ 3 entries (actual: **6**) ✓
- `recommended_actions` has ≥ 3 entries (actual: **6**) ✓

---

## Smoke Checks

```bash
docker run --rm repohealth-mcp smoke
```

Expected output:

```
RepoHealth MCP — smoke tests
========================================
[OK  ] demo_project exists: demo_project/ found at /demo_project
[OK  ] analyzers importable: all analyzer modules imported successfully
[OK  ] core importable: all core modules imported successfully
[OK  ] app creates cleanly: FastAPI app created: repohealth-mcp v0.1.0
========================================
Smoke tests passed.
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `InvalidProjectPathError` | The container path is `/demo_project` (not `/workspace/demo_project`). Use the exact path shown above. |
| Inspector shows no tools | Confirm the server is running and connect to `http://localhost:8000/mcp` with **Streamable HTTP** transport. |
| `406 Not Acceptable` from curl | Add `-H "Accept: application/json, text/event-stream"` to your curl command. |
| `confidence` lower than expected | Verify you're using `pytest_failure.log` — the other log files are classified differently. |

---

## Optional: Test Other Log Files

```json
{ "log_path": "/demo_project/logs/npm_build_failure.log" }
```
→ `category: "network_error"` or `"build_error"`, errors related to `legacy-lib`.

```json
{ "log_path": "/demo_project/logs/docker_build_failure.log" }
```
→ `category: "build_error"`, errors related to pip install failure.
