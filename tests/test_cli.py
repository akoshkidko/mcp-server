"""Tests for the CLI router (src/repohealth_mcp/cli.py)."""

import sys
from unittest.mock import call, patch

import pytest

from repohealth_mcp.cli import SUBCOMMANDS, USAGE, main


# ── Module-level sanity ───────────────────────────────────────────────────────

def test_module_importable() -> None:
    import repohealth_mcp.cli  # noqa: F401


def test_known_subcommands_defined() -> None:
    assert "serve" in SUBCOMMANDS
    assert "smoke" in SUBCOMMANDS


def test_usage_string_mentions_subcommands() -> None:
    assert "serve" in USAGE
    assert "smoke" in USAGE


# ── Default (no args) → serve ─────────────────────────────────────────────────

def test_no_args_defaults_to_serve() -> None:
    """With no CLI arguments, main() must call server.main()."""
    with patch("sys.argv", ["repohealth-mcp"]):
        with patch("repohealth_mcp.server.main") as mock_serve:
            main()
            mock_serve.assert_called_once()


# ── Explicit 'serve' subcommand ───────────────────────────────────────────────

def test_serve_subcommand_calls_server_main() -> None:
    with patch("sys.argv", ["repohealth-mcp", "serve"]):
        with patch("repohealth_mcp.server.main") as mock_serve:
            main()
            mock_serve.assert_called_once()


# ── 'smoke' subcommand ────────────────────────────────────────────────────────

def test_smoke_subcommand_calls_smoke_main() -> None:
    with patch("sys.argv", ["repohealth-mcp", "smoke"]):
        with patch("repohealth_mcp.smoke.main") as mock_smoke:
            main()
            mock_smoke.assert_called_once()


# ── Unknown subcommand → non-zero exit ────────────────────────────────────────

def test_unknown_subcommand_exits_nonzero() -> None:
    with patch("sys.argv", ["repohealth-mcp", "foobar"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code != 0


def test_unknown_subcommand_prints_error_to_stderr(capsys: pytest.CaptureFixture) -> None:
    with patch("sys.argv", ["repohealth-mcp", "foobar"]):
        with pytest.raises(SystemExit):
            main()
    captured = capsys.readouterr()
    assert "foobar" in captured.err
    assert "serve" in captured.err


def test_unknown_subcommand_includes_usage_in_stderr(capsys: pytest.CaptureFixture) -> None:
    with patch("sys.argv", ["repohealth-mcp", "notacommand"]):
        with pytest.raises(SystemExit):
            main()
    captured = capsys.readouterr()
    assert "smoke" in captured.err


# ── Dispatch does NOT call the wrong entrypoint ───────────────────────────────

def test_serve_does_not_call_smoke() -> None:
    with patch("sys.argv", ["repohealth-mcp", "serve"]):
        with patch("repohealth_mcp.server.main"):
            with patch("repohealth_mcp.smoke.main") as mock_smoke:
                main()
                mock_smoke.assert_not_called()


def test_smoke_does_not_call_serve() -> None:
    with patch("sys.argv", ["repohealth-mcp", "smoke"]):
        with patch("repohealth_mcp.smoke.main"):
            with patch("repohealth_mcp.server.main") as mock_serve:
                main()
                mock_serve.assert_not_called()
