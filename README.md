# RepoHealth MCP

Локальный Dockerized [MCP](https://modelcontextprotocol.io)-сервер, который даёт AI-ассистентам возможность быстро разобраться в состоянии репозитория — найти технический долг, диагностировать падения CI, проверить зависимости и выдать единый health score.

---

## Что делает сервер

### Какую боль решает

Когда репозиторий начинает деградировать — накапливаются TODO/FIXME-аннотации, CI нестабилен, версии зависимостей заданы через `*` или `>=` — сложно быстро получить структурированную картину *насколько всё плохо*. Разработчик либо читает файлы вручную, либо ждёт полного прогона CI, чтобы подтвердить очевидное.

### Для кого

- **Разработчики**, которые принимают чужой код или проводят ревью незнакомого репозитория.
- **AI-ассистенты** (Claude, Cursor и др.), которым нужен структурированный контекст перед тем, как предлагать правки.
- **Тимлиды**, которые хотят объективный снимок состояния проекта перед спринтом или релизом.

### Какие инструменты реализованы

Четыре MCP-инструмента, доступных из любого MCP-совместимого клиента:

| Инструмент | Что делает |
|------------|-----------|
| `scan_tech_debt` | Обходит исходные файлы и находит аннотации TODO / FIXME / HACK / BUG / XXX / DEPRECATED, группирует по степени критичности |
| `diagnose_ci_logs` | Парсит лог-файл CI и классифицирует категорию сбоя (падение теста, OOM, сеть, ошибка сборки и т.д.) с оценкой уверенности |
| `analyze_dependencies` | Читает манифесты (`requirements.txt`, `package.json`, `pyproject.toml`) и отмечает незакреплённые, wildcard или слишком широкие версии, а также неизвестные лицензии |
| `project_health_report` | Запускает все три анализа и возвращает итоговый health score в `[0, 1]` со статусом `healthy` / `needs_attention` / `critical`, списком проблем и рекомендациями |

---

## Быстрый старт

### Что нужно

- [Docker](https://docs.docker.com/get-docker/) (любая актуальная версия)
- Терминал

### Шаг 1 — Клонировать репозиторий

```bash
git clone <repo-url>
cd mcp-server
```

### Шаг 2 — Собрать образ

```bash
docker build -t repohealth-mcp .
```

Ожидаемый результат: сборка завершается без ошибок, создаётся образ с тегом `repohealth-mcp`.

### Шаг 3 — Запустить сервер

```bash
docker run --rm -p 8000:8000 repohealth-mcp serve
```

Сервер слушает на `http://localhost:8000`. Оставьте этот терминал открытым.

### Шаг 4 — Проверить, что сервер запустился

Откройте второй терминал и выполните:

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{"status": "ok", "service": "repohealth-mcp", "version": "0.1.0"}
```

### Шаг 5 — Подключиться через MCP Inspector

1. Откройте [MCP Inspector](https://inspector.tools) в браузере (или запустите локально: `npx @modelcontextprotocol/inspector`).
2. Введите URL сервера: `http://localhost:8000/mcp`
3. Выберите тип транспорта: **Streamable HTTP**
4. Нажмите **Connect**.

В списке инструментов должны появиться четыре: `scan_tech_debt`, `diagnose_ci_logs`, `analyze_dependencies`, `project_health_report`.

> **Cursor / Claude Desktop:** добавьте сервер как MCP-источник с URL `http://localhost:8000/mcp` и транспортом `streamable-http`.

### Шаг 6 — Анализировать свой репозиторий (опционально)

Примонтируйте локальную директорию как `/workspace`, чтобы сервер мог читать её файлы:

```bash
docker run --rm -p 8000:8000 \
  -v /path/to/your/repo:/workspace \
  repohealth-mcp serve
```

Затем используйте `/workspace` в качестве значения параметра `project_path` при вызове инструментов.

---

## Как использовать

В каждый образ вшит демо-проект по пути `/demo_project`. Все примеры ниже используют его. Для собственного репозитория подставьте `/workspace` (требует монтирование из шага 6).

---

### `scan_tech_debt`

Сканирует исходные файлы на наличие аннотаций технического долга.

**Параметры**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|:---:|---------|
| `project_path` | string | да | Абсолютный путь к корню проекта |
| `include_globs` | список строк | нет | Паттерны файлов для сканирования (по умолчанию: `**/*.py`, `**/*.js`, `**/*.ts` и другие) |
| `exclude_globs` | список строк | нет | Паттерны для исключения (по умолчанию: `node_modules`, `.git`, `__pycache__` и т.д.) |

**Пример вызова (MCP Inspector → "Call Tool")**

```json
{
  "project_path": "/demo_project"
}
```

**Ожидаемый результат (сокращённо)**

```json
{
  "total_findings": 9,
  "scanned_files": 7,
  "by_severity": { "critical": 2, "high": 3, "low": 3, "info": 1 },
  "by_marker":   { "BUG": 2, "FIXME": 1, "HACK": 2, "TODO": 3, "NOQA": 1 },
  "findings": [
    {
      "file": "src/auth.py",
      "line": 7,
      "marker": "FIXME",
      "severity": "high",
      "text": "# FIXME: temporary auth bypass for demo login, remove before production"
    }
  ]
}
```

---

### `diagnose_ci_logs`

Парсит лог-файл CI и определяет корневую причину сбоя.

**Параметры**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|:---:|---------|
| `log_path` | string | да | Абсолютный путь к текстовому лог-файлу |

**Пример вызова**

```json
{
  "log_path": "/demo_project/logs/pytest_failure.log"
}
```

**Ожидаемый результат**

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

**Поддерживаемые категории сбоев**

`test_assertion_failure` · `out_of_memory` · `timeout` · `network_error` · `build_error` · `generic_failure`

---

### `analyze_dependencies`

Проверяет манифесты зависимостей на риски версионирования и неизвестные лицензии.

**Параметры**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|:---:|---------|
| `project_path` | string | да | Абсолютный путь к корню проекта |

**Пример вызова**

```json
{
  "project_path": "/demo_project"
}
```

**Ожидаемый результат (ключевые поля)**

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
    { "name": "legacy-lib", "version_spec": "*",          "risk_flags": ["wildcard"],   "license": "unknown" }
  ]
}
```

**Флаги рисков:** `unpinned` · `wildcard` · `wide_range` · `patch_range`

---

### `project_health_report`

Агрегирует все анализы в единый health score.

**Параметры**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|:---:|---------|
| `project_path` | string | да | Абсолютный путь к корню проекта |
| `ci_log_path` | string | нет | Абсолютный путь к лог-файлу CI. Если не указан — CI-измерение исключается из расчёта score |

**Пример вызова**

```json
{
  "project_path": "/demo_project",
  "ci_log_path":  "/demo_project/logs/pytest_failure.log"
}
```

**Ожидаемый результат**

```json
{
  "health_score": 0.657,
  "health_status": "needs_attention",
  "top_issues": [
    "High-severity tech debt: 5 FIXME/BUG marker(s) require immediate attention",
    "Failing tests: assertion failures detected (confidence 95%)",
    "Dependency risk: 7 package(s) with wildcard / unpinned / wide-range version specs"
  ],
  "recommended_actions": [
    "Fix BUG in src/auth.py:30 — # BUG: token has no expiry — sessions live forever",
    "Fix failing test assertions — check assert values match function return codes",
    "Pin 7 unpinned dependency/ies to exact versions to ensure reproducible builds"
  ]
}
```

**Пороговые значения статусов** (настраиваются через переменные окружения):

| Диапазон score | Статус |
|----------------|--------|
| ≥ 0.8 | `healthy` |
| 0.5 – 0.8 | `needs_attention` |
| < 0.5 | `critical` |

---

## Smoke-проверки

Самодиагностика: убеждается, что модули импортируются, демо-проект на месте, приложение стартует:

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

Код завершения: `0` — всё прошло, `1` — есть сбой.

---

## Ограничения и допущения

### Что поддерживается

- Исходные файлы `.py`, `.js`, `.ts`, `.go`, `.java`, `.rb`, `.rs` — для поиска технического долга.
- Текстовые лог-файлы CI любого формата (GitHub Actions, GitLab CI, Jenkins, CircleCI и др.).
- Манифесты зависимостей: `requirements.txt`, `package.json`, `pyproject.toml`.
- Поиск лицензий через `metadata/licenses.json` внутри проекта (необязательно; если файл отсутствует — лицензия помечается как `unknown`).

### Что не поддерживается

- Бинарные файлы, скомпилированные артефакты, нетекстовые логи.
- Проверка уязвимостей в реальном времени (CVE-базы) — только анализ ограничений версий.
- Git blame, история коммитов, сравнение веток.
- Рекурсивное сканирование сабмодулей.
- Удалённые репозитории — сервер читает только локальную файловую систему.

### Безопасность путей

Все вызовы инструментов проверяются против `allowed_roots`. По умолчанию доступны только `/workspace` и `/demo_project`. Пути за пределами этих корней отклоняются с ошибкой. Переопределяется через переменную `REPOHEALTH_ALLOWED_ROOTS`.

### На чём проверялось

Демо-проект `demo_project/`, вшитый в образ: ~250 строк Python в 5 исходных файлах, один лог упавшего pytest, два манифеста зависимостей и `metadata/licenses.json`.

---

## Конфигурация

Все настройки читаются из переменных окружения с префиксом `REPOHEALTH_`.

| Переменная | Значение по умолчанию | Описание |
|------------|-----------------------|---------|
| `REPOHEALTH_PORT` | `8000` | Порт сервера |
| `REPOHEALTH_HOST` | `0.0.0.0` | Адрес для прослушивания |
| `REPOHEALTH_ALLOWED_ROOTS` | `/workspace,/demo_project` | Список допустимых корней файловой системы через запятую |
| `REPOHEALTH_SCORE_THRESHOLD_HEALTHY` | `0.8` | Минимальный score для статуса `healthy` |
| `REPOHEALTH_SCORE_THRESHOLD_WARNING` | `0.5` | Нижняя граница для `needs_attention` (ниже → `critical`) |

**Пример: сменить порт и добавить собственный путь**

```bash
docker run --rm -p 9000:9000 \
  -e REPOHEALTH_PORT=9000 \
  -e REPOHEALTH_ALLOWED_ROOTS=/workspace,/demo_project,/tmp/myrepo \
  -v /tmp/myrepo:/tmp/myrepo \
  repohealth-mcp serve
```

---

## Локальная разработка

```bash
# 1. Установить пакет с dev-зависимостями (Python 3.11+)
pip install -e ".[dev]"

# 2. Запустить тесты
pytest

# 3. Запустить сервер
repohealth-serve

# 4. Запустить smoke-проверки
repohealth-smoke
```

Сервер стартует на `http://localhost:8000`. Подключите MCP Inspector к `http://localhost:8000/mcp`.

> **Важно:** локально `allowed_roots` по умолчанию — `/workspace` и `/demo_project`. Чтобы анализировать свой репозиторий, добавьте его путь через переменную окружения:
> ```bash
> REPOHEALTH_ALLOWED_ROOTS=/workspace,/demo_project,/path/to/your/repo repohealth-serve
> ```

---

## Подробное демо

Пошаговый сценарий по всем четырём инструментам с точными ожидаемыми ответами — в файле **[DEMO.md](DEMO.md)**.

---

## Лицензия

MIT
