# demo_project

A minimal placeholder repository used for integration testing and demonstrations
of the RepoHealth MCP server.

## Purpose

- Smoke tests verify that `demo_project/` is present and accessible.
- Integration tests and demos will populate this directory with realistic
  fixture files (source with TODOs, CI logs with errors, manifests with
  real dependencies).

## Structure

```
demo_project/
├── README.md           ← this file
├── pyproject.toml      ← Python project stub
├── requirements.txt    ← pinned Python dependencies stub
├── package.json        ← Node.js stub
├── Dockerfile          ← container stub
├── src/                ← placeholder source directory
├── tests/              ← placeholder test directory
├── logs/               ← CI log fixtures go here
├── docs/               ← documentation stubs
└── metadata/           ← extra metadata stubs
```

## Populating for Demos

Once the business logic is implemented, add:
- `src/app.py` — a file with intentional TODO/FIXME/HACK comments.
- `logs/ci.log` — a realistic CI log with errors and warnings.
- Real version-pinned `requirements.txt` and `package.json`.
