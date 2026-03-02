"""Smoke test runner for RepoHealth MCP.

Verifies that the runtime environment is sane before or after deployment.
Exit code 0 = all checks passed; non-zero = at least one check failed.
"""

import importlib
import sys
from pathlib import Path


# ── Individual checks ────────────────────────────────────────────────────────

def _check_demo_project_exists() -> tuple[bool, str]:
    """Ensure the demo_project/ directory is present.

    Searches in order:
    1. Relative to this source file (src-layout: parents[2] = project root) — works in local dev.
    2. /demo_project — the absolute path used inside the Docker container.
    """
    candidates = [
        Path(__file__).resolve().parents[2] / "demo_project",
        Path("/demo_project"),
    ]
    for demo_path in candidates:
        if demo_path.is_dir():
            return True, f"demo_project/ found at {demo_path}"
    searched = ", ".join(str(p) for p in candidates)
    return False, f"demo_project/ NOT found (searched: {searched})"


def _check_analyzers_importable() -> tuple[bool, str]:
    """Ensure all analyzer modules can be imported without errors."""
    modules = [
        "repohealth_mcp.analyzers.tech_debt",
        "repohealth_mcp.analyzers.ci_logs",
        "repohealth_mcp.analyzers.dependencies",
        "repohealth_mcp.analyzers.report",
    ]
    failed: list[str] = []
    for mod in modules:
        try:
            importlib.import_module(mod)
        except Exception as exc:  # noqa: BLE001
            failed.append(f"{mod}: {exc}")

    if not failed:
        return True, "all analyzer modules imported successfully"
    return False, "import failures:\n  " + "\n  ".join(failed)


def _check_core_importable() -> tuple[bool, str]:
    """Ensure core modules are importable."""
    modules = [
        "repohealth_mcp.core.models",
        "repohealth_mcp.core.errors",
        "repohealth_mcp.core.paths",
        "repohealth_mcp.core.scoring",
        "repohealth_mcp.core.constants",
    ]
    failed: list[str] = []
    for mod in modules:
        try:
            importlib.import_module(mod)
        except Exception as exc:  # noqa: BLE001
            failed.append(f"{mod}: {exc}")

    if not failed:
        return True, "all core modules imported successfully"
    return False, "import failures:\n  " + "\n  ".join(failed)


def _check_app_creates() -> tuple[bool, str]:
    """Ensure create_app() returns a FastAPI instance without errors."""
    try:
        from repohealth_mcp.app import create_app
        app = create_app()
        return True, f"FastAPI app created: {app.title} v{app.version}"
    except Exception as exc:  # noqa: BLE001
        return False, f"create_app() raised: {exc}"


# ── Runner ───────────────────────────────────────────────────────────────────

CHECKS = [
    ("demo_project exists", _check_demo_project_exists),
    ("analyzers importable", _check_analyzers_importable),
    ("core importable", _check_core_importable),
    ("app creates cleanly", _check_app_creates),
]


def main() -> None:
    """Run all smoke checks and exit with an appropriate code."""
    all_passed = True

    print("RepoHealth MCP — smoke tests\n" + "=" * 40)
    for label, check_fn in CHECKS:
        passed, message = check_fn()
        status = "OK  " if passed else "FAIL"
        print(f"[{status}] {label}: {message}")
        if not passed:
            all_passed = False

    print("=" * 40)
    if all_passed:
        print("Smoke tests passed.")
        sys.exit(0)
    else:
        print("Smoke tests FAILED. See above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
