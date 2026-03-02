"""FastAPI application factory for RepoHealth MCP."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from repohealth_mcp import __version__
from repohealth_mcp.config import settings
from repohealth_mcp.transport.health import router as health_router
from repohealth_mcp.transport.mcp_factory import create_mcp_server


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application.

    Wiring order:
    1. ``create_mcp_server()`` registers all tools on a ``FastMCP`` instance.
    2. ``mcp.streamable_http_app()`` initialises the session manager lazily and
       returns a Starlette ASGI app.
    3. The FastAPI lifespan runs ``mcp.session_manager.run()`` so Streamable
       HTTP sessions are managed correctly for the lifetime of the process.
    4. The MCP Starlette app is mounted at ``/mcp``.
    """
    mcp = create_mcp_server()
    # Must be called before accessing mcp.session_manager — initialises it lazily.
    mcp_asgi = mcp.streamable_http_app()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with mcp.session_manager.run():
            yield

    app = FastAPI(
        title=settings.service_name,
        version=__version__,
        description="Repository health analysis via MCP.",
        docs_url="/docs",
        redoc_url=None,
        lifespan=lifespan,
    )

    # ── HTTP routers ────────────────────────────────────────────────────────
    app.include_router(health_router)

    # ── MCP Streamable HTTP transport at /mcp ───────────────────────────────
    app.mount("/mcp", mcp_asgi)

    return app
