"""CLI router for RepoHealth MCP.

Dispatches Docker / shell subcommands to the appropriate entrypoint:

    python -m repohealth_mcp.cli serve   → start the HTTP/MCP server
    python -m repohealth_mcp.cli smoke   → run smoke checks and exit
    python -m repohealth_mcp.cli         → defaults to serve

Intentionally uses only stdlib so it has zero extra dependencies and starts
fast even before the rest of the package is imported.
"""

import sys

USAGE = """\
Usage: repohealth-mcp <subcommand>

Subcommands:
  serve   Start the MCP server on port 8000 (default)
  smoke   Run smoke checks and exit (0 = pass, 1 = fail)
"""

SUBCOMMANDS = ("serve", "smoke")


def main() -> None:
    """Parse the first CLI argument and dispatch to the right entrypoint."""
    args = sys.argv[1:]
    subcommand = args[0] if args else "serve"

    if subcommand == "serve":
        from repohealth_mcp.server import main as serve_main
        serve_main()

    elif subcommand == "smoke":
        from repohealth_mcp.smoke import main as smoke_main
        smoke_main()

    else:
        print(f"Error: unknown subcommand '{subcommand}'\n", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
