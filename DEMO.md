# RepoHealth MCP — Демо

Пошаговый сценарий на основе встроенного демо-проекта.  
Примерное время: **3–5 минут**.

---

## Подготовка

Выполните три команды в терминале:

```bash
# 1. Собрать образ (точка в конце обязательна)
docker build -t repohealth-mcp .

# 2. Запустить сервер (оставьте терминал открытым)
docker run --rm -p 8000:8000 repohealth-mcp serve

# 3. Во втором терминале проверить, что сервер работает
curl http://localhost:8000/health
# → {"status":"ok","service":"repohealth-mcp","version":"0.1.0"}
```

Затем откройте MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
```

В браузере:
- **Transport Type** → `Streamable HTTP`
- **URL** → `http://localhost:8000/mcp`
- Нажать **Connect**

Должны появиться 4 инструмента: `scan_tech_debt`, `diagnose_ci_logs`, `analyze_dependencies`, `project_health_report`.

> Все пути ниже (`/demo_project/...`) — это пути **внутри контейнера**. Вводите их точно как написано.

---

## Шаг 1 — scan_tech_debt

Нажмите на инструмент `scan_tech_debt` в списке.

**Что ввести:**
```json
{
  "project_path": "/demo_project"
}
```

**Ожидаемый результат:**
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

**Что проверить:**
- `total_findings` ≥ 6 (в демо: **9**)
- `critical` + `high` ≥ 1 (в демо: **5**)
- В `src/auth.py` есть FIXME (обход авторизации) и BUG (нет срока жизни токена)

---

## Шаг 2 — diagnose_ci_logs

Нажмите на инструмент `diagnose_ci_logs`.

**Что ввести:**
```json
{
  "log_path": "/demo_project/logs/pytest_failure.log"
}
```

**Ожидаемый результат:**
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

**Что проверить:**
- `category == "test_assertion_failure"` ✓
- `confidence >= 0.90` (в демо: **0.95**) ✓
- В ошибках есть строка `E       assert 500 == 200`

---

## Шаг 3 — analyze_dependencies

Нажмите на инструмент `analyze_dependencies`.

**Что ввести:**
```json
{
  "project_path": "/demo_project"
}
```

**Ожидаемый результат:**
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

> `requests` и `tenacity` встречаются дважды — они объявлены и в `requirements.txt`, и в `pyproject.toml`. Это ожидаемое поведение.

**Что проверить:**
- `manifests_found` содержит все три манифеста ✓
- `version_risk_count >= 2` (в демо: **7**) ✓
- `legacy-lib` имеет `"license": "unknown"` и `"risk_flags": ["wildcard"]` ✓

---

## Шаг 4 — project_health_report

Нажмите на инструмент `project_health_report`.

**Что ввести:**
```json
{
  "project_path": "/demo_project",
  "ci_log_path":  "/demo_project/logs/pytest_failure.log"
}
```

**Ожидаемый результат:**
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

**Что проверить:**
- `health_status == "needs_attention"` ✓
- `health_score` между 0.5 и 0.8 (в демо: **0.657**) ✓
- `top_issues` содержит ≥ 3 записи (в демо: **6**) ✓
- `recommended_actions` содержит ≥ 3 записи (в демо: **6**) ✓

---

## Smoke-проверка

```bash
docker run --rm repohealth-mcp smoke
```

Ожидаемый вывод:

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

## Решение проблем

| Проблема | Решение |
|----------|---------|
| `Path ... is outside all allowed roots` | Убедитесь, что вводите `/demo_project`, а не `/app` или другой путь |
| Inspector не видит инструменты | Проверьте, что сервер запущен, и подключайтесь через **Streamable HTTP** к `http://localhost:8000/mcp` |
| `confidence` меньше ожидаемого | Убедитесь, что используете именно `pytest_failure.log` — другие логи классифицируются иначе |

---

## Дополнительно — другие логи

```json
{ "log_path": "/demo_project/logs/npm_build_failure.log" }
```
→ `category: "build_error"`, ошибки связанные с `legacy-lib`.

```json
{ "log_path": "/demo_project/logs/docker_build_failure.log" }
```
→ `category: "build_error"`, ошибки установки pip.
