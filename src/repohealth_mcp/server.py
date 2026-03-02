"""Runnable entrypoint — starts the RepoHealth MCP server via Uvicorn."""

import uvicorn

from repohealth_mcp.config import settings


def main() -> None:
    """Start the Uvicorn server.  Invoked by the ``repohealth-serve`` script."""
    uvicorn.run(
        "repohealth_mcp.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
