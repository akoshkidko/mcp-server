"""Tests for the smoke check runner."""

import sys
from unittest.mock import patch

import pytest

from repohealth_mcp.smoke import (
    CHECKS,
    _check_analyzers_importable,
    _check_app_creates,
    _check_core_importable,
    _check_demo_project_exists,
)


# ── Individual check smoke tests ──────────────────────────────────────────────

def test_analyzers_importable_check_passes() -> None:
    passed, message = _check_analyzers_importable()
    assert passed, f"Expected pass, got: {message}"


def test_core_importable_check_passes() -> None:
    passed, message = _check_core_importable()
    assert passed, f"Expected pass, got: {message}"


def test_app_creates_check_passes() -> None:
    passed, message = _check_app_creates()
    assert passed, f"Expected pass, got: {message}"


def test_check_tuple_has_bool_and_str() -> None:
    """All checks should return (bool, str)."""
    for label, fn in CHECKS:
        result = fn()
        assert isinstance(result, tuple) and len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)


# ── Main entrypoint ───────────────────────────────────────────────────────────

def test_main_exits_zero_when_all_pass() -> None:
    """When all checks pass, main() should exit with code 0."""
    from repohealth_mcp.smoke import main

    # Patch all checks to return passing results.
    passing = [(label, lambda: (True, "ok")) for label, _ in CHECKS]

    with patch("repohealth_mcp.smoke.CHECKS", passing):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 0


def test_main_exits_nonzero_when_any_fails() -> None:
    """When any check fails, main() should exit with a non-zero code."""
    from repohealth_mcp.smoke import main

    failing = [(label, lambda: (False, "not ok")) for label, _ in CHECKS]

    with patch("repohealth_mcp.smoke.CHECKS", failing):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code != 0


# ── TODO: future tests ────────────────────────────────────────────────────────
# TODO: test demo_project check with a real temp directory
# TODO: test check output formatting / captured stdout
