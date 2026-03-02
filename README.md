# RepoHealth MCP

Локальный MCP-сервер, который помогает AI-ассистентам быстро разобраться в состоянии репозитория: найти технический долг, диагностировать падения CI, проверить зависимости и выдать единый health score.

---

## Что делает сервер

### Какую боль решает

Когда репозиторий начинает деградировать — накапливаются TODO/FIXME-аннотации, CI нестабилен, версии зависимостей заданы через `*` или `>=` — сложно быстро получить структурированную картину того, насколько всё плохо. Разработчик либо читает файлы вручную, либо ждёт полного прогона CI.

### Для кого

- **Разработчики**, которые принимают чужой код или проводят ревью незнакомого репозитория.
- **AI-ассистенты** (Claude, Cursor и др.), которым нужен структурированный контекст перед тем, как предлагать правки.
- **Тимлиды**, которые хотят объективный снимок состояния проекта перед спринтом или релизом.

### Четыре инструмента

| Инструмент | Что делает |
|------------|-----------|
| `scan_tech_debt` | Находит TODO / FIXME / HACK / BUG / XXX в исходных файлах, группирует по критичности |
| `diagnose_ci_logs` | Парсит лог CI и классифицирует причину сбоя (упавший тест, OOM, сеть, ошибка сборки) с оценкой уверенности |
| `analyze_dependencies` | Читает `requirements.txt`, `package.json`, `pyproject.toml` и находит незакреплённые версии и неизвестные лицензии |
| `project_health_report` | Запускает все три анализа и возвращает итоговый score от 0 до 1 со статусом и списком рекомендаций |

---

## Быстрый старт

### Что нужно установить заранее

1. **Docker Desktop** — скачайте с [docker.com/get-docker](https://docs.docker.com/get-docker/) и запустите его. В меню-баре macOS должна появиться иконка кита. Без запущенного Docker Desktop ничего не заработает.

2. **Node.js** — нужен только для MCP Inspector. Скачайте LTS-версию с [nodejs.org](https://nodejs.org).

---

### Шаг 1 — Клонировать репозиторий

```bash
git clone <repo-url>
cd mcp-server
```

---

### Шаг 2 — Собрать Docker-образ

```bash
docker build -t repohealth-mcp .
```

> **Важно:** точка в конце обязательна — она означает «текущая папка».

Ожидаемый результат: через 1–2 минуты появится сообщение вида:
```
=> exporting to image
=> => naming to docker.io/library/repohealth-mcp
```

Если видите ошибку `docker: 'docker buildx build' requires 1 argument` — вы забыли точку в конце команды.  
Если видите `cannot connect to Docker daemon` — убедитесь, что Docker Desktop запущен.

---

### Шаг 3 — Запустить сервер

```bash
docker run --rm -p 8000:8000 repohealth-mcp serve
```

Оставьте этот терминал открытым. Сервер работает, пока терминал открыт.

Если видите ошибку `port is already allocated` — порт 8000 занят другим процессом. Найдите и остановите его:

```bash
# Посмотреть, что занимает порт 8000
docker ps

# Остановить контейнер по ID
docker stop <CONTAINER_ID>

# После этого повторите запуск
docker run --rm -p 8000:8000 repohealth-mcp serve
```

---

### Шаг 4 — Проверить, что сервер работает

Откройте **новый терминал** (первый не закрывайте) и выполните:

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{"status": "ok", "service": "repohealth-mcp", "version": "0.1.0"}
```

---

### Шаг 5 — Открыть MCP Inspector

MCP Inspector — это веб-интерфейс для вызова инструментов сервера вручную.

Запустите его в том же новом терминале:

```bash
npx @modelcontextprotocol/inspector
```

Команда автоматически откроет браузер. Если не открылась — перейдите вручную на `http://localhost:6274`.

---

### Шаг 6 — Подключиться к серверу в Inspector

В интерфейсе Inspector:

1. **Transport Type** → выберите `Streamable HTTP`
2. **URL** → введите `http://localhost:8000/mcp`
3. Нажмите кнопку **Connect**

В левой панели появится надпись **Connected** и имя сервера `RepoHealth MCP`.  
В центральной панели во вкладке **Tools** появятся четыре инструмента.

---

### Шаг 7 — Вызвать инструмент

Нажмите на инструмент в списке (например, `scan_tech_debt`).

В поле **project_path** введите:

```
/demo_project
```

> **Важно:** путь `/demo_project` — это путь внутри Docker-контейнера, не на вашем компьютере. Вводите именно его, без изменений.

Нажмите **Run Tool**. Через секунду появится JSON с результатом.

---

## Как использовать каждый инструмент

Все пути ниже (`/demo_project/...`) вводятся в MCP Inspector в соответствующие поля. Это пути внутри контейнера, они фиксированные — не меняйте их.

---

### `scan_tech_debt` — поиск технического долга

**Поля для заполнения:**

| Поле | Что ввести | Обязательно |
|------|-----------|:-----------:|
| `project_path` | `/demo_project` | да |
| `include_globs` | оставить пустым | нет |
| `exclude_globs` | оставить пустым | нет |

**Ожидаемый результат:**

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

### `diagnose_ci_logs` — диагностика лога CI

**Поля для заполнения:**

| Поле | Что ввести | Обязательно |
|------|-----------|:-----------:|
| `log_path` | `/demo_project/logs/pytest_failure.log` | да |

**Ожидаемый результат:**

```json
{
  "category": "test_assertion_failure",
  "confidence": 0.95,
  "error_count": 2,
  "warning_count": 1,
  "errors": [
    { "line_number": 18, "content": "E       assert 500 == 200", "category": "error" },
    { "line_number": 23, "content": "FAILED tests/test_service.py::test_create_user ...", "category": "error" }
  ]
}
```

Другие логи для проверки (тоже уже внутри контейнера):
- `/demo_project/logs/npm_build_failure.log` → категория `build_error`
- `/demo_project/logs/docker_build_failure.log` → категория `build_error`

---

### `analyze_dependencies` — проверка зависимостей

**Поля для заполнения:**

| Поле | Что ввести | Обязательно |
|------|-----------|:-----------:|
| `project_path` | `/demo_project` | да |

**Ожидаемый результат:**

```json
{
  "manifests_found": ["requirements.txt", "pyproject.toml", "package.json"],
  "total": 10,
  "unpinned_count": 7,
  "version_risk_count": 7,
  "unknown_license_count": 1,
  "dependencies": [
    { "name": "requests",   "version_spec": "==2.28.0", "risk_flags": [],           "license": "Apache-2.0" },
    { "name": "tenacity",   "version_spec": "",          "risk_flags": ["unpinned"], "license": "Apache-2.0" },
    { "name": "legacy-lib", "version_spec": "*",          "risk_flags": ["wildcard"], "license": "unknown" }
  ]
}
```

---

### `project_health_report` — итоговый отчёт

**Поля для заполнения:**

| Поле | Что ввести | Обязательно |
|------|-----------|:-----------:|
| `project_path` | `/demo_project` | да |
| `ci_log_path` | `/demo_project/logs/pytest_failure.log` | нет |

**Ожидаемый результат:**

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

**Значения `health_status`:**

| Score | Статус |
|-------|--------|
| ≥ 0.8 | `healthy` |
| 0.5 – 0.8 | `needs_attention` |
| < 0.5 | `critical` |

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
- Удалённые репозитории — сервер читает только локальную файловую систему.

### Безопасность путей

Все вызовы инструментов проверяются против `allowed_roots`. По умолчанию доступны только `/workspace` и `/demo_project`. Пути за пределами этих корней отклоняются с ошибкой `Path is outside all allowed roots`. Переопределяется через переменную `REPOHEALTH_ALLOWED_ROOTS`.

### На чём проверялось

Демо-проект `demo_project/`, вшитый в образ: ~250 строк Python в 5 исходных файлах, один лог упавшего pytest, манифесты `requirements.txt` / `package.json` / `pyproject.toml`, и `metadata/licenses.json`.

---

## Smoke-проверка (самодиагностика)

Проверяет, что всё внутри контейнера работает корректно:

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

Код завершения: `0` — всё в порядке, `1` — есть сбой.

---

## Анализ своего репозитория

Это альтернативный вариант **шага 3**. Вместо обычного запуска используйте эту команду:

```bash
docker run --rm -p 8000:8000 \
  -v /Users/your-name/Projects/my-repo:/workspace \
  repohealth-mcp serve
```

Замените `/Users/your-name/Projects/my-repo` на реальный путь к вашему репозиторию на компьютере. Например: `/Users/aleksej/Projects/my-app`.

Шаги 4–7 остаются теми же. Единственное отличие — в MCP Inspector вместо `/demo_project` вводите `/workspace`:

```
project_path: /workspace
```

---

## Конфигурация

Все параметры задаются через переменные окружения (`-e` при запуске Docker).

| Переменная | Значение по умолчанию | Описание |
|------------|-----------------------|---------|
| `REPOHEALTH_PORT` | `8000` | Порт сервера |
| `REPOHEALTH_ALLOWED_ROOTS` | `/workspace,/demo_project` | Пути, к которым сервер имеет доступ. Пути за пределами — отклоняются с ошибкой |
| `REPOHEALTH_SCORE_THRESHOLD_HEALTHY` | `0.8` | Минимальный score для статуса `healthy` |
| `REPOHEALTH_SCORE_THRESHOLD_WARNING` | `0.5` | Нижняя граница для `needs_attention` (ниже — `critical`) |

**Пример: сменить порт**

```bash
docker run --rm -p 9000:9000 \
  -e REPOHEALTH_PORT=9000 \
  repohealth-mcp serve
```

---

## Локальная разработка (без Docker)

```bash
# Установить пакет с dev-зависимостями (нужен Python 3.11+)
pip install -e ".[dev]"

# Запустить тесты
pytest

# Запустить сервер
repohealth-serve

# Запустить smoke-проверку
repohealth-smoke
```

---

## Подробное демо

Пошаговый сценарий по всем четырём инструментам с точными ожидаемыми ответами — в файле **[DEMO.md](DEMO.md)**.

---

## Лицензия

MIT
