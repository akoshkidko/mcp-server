"""Tests for the /health HTTP endpoint and general app creation."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from repohealth_mcp import __version__
from repohealth_mcp.app import create_app
from repohealth_mcp.config import settings


@pytest.fixture()
def client():
    """TestClient that runs the full lifespan (required for MCP session manager)."""
    app = create_app()
    with TestClient(app, base_url="http://localhost:8000") as c:
        yield c


# ── /health endpoint ──────────────────────────────────────────────────────────

def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_shape(client: TestClient) -> None:
    data = client.get("/health").json()
    assert data["status"] == "ok"
    assert data["service"] == settings.service_name
    assert data["version"] == __version__


def test_health_content_type(client: TestClient) -> None:
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]


# ── App factory ───────────────────────────────────────────────────────────────

def test_create_app_returns_fastapi_instance() -> None:
    app = create_app()
    assert isinstance(app, FastAPI)


def test_app_title_matches_config() -> None:
    app = create_app()
    assert app.title == settings.service_name


def test_app_version_matches_package() -> None:
    app = create_app()
    assert app.version == __version__


def test_app_has_lifespan() -> None:
    """App must declare a lifespan so the MCP session manager is managed."""
    app = create_app()
    assert app.router.lifespan_context is not None


# ── Route inventory ───────────────────────────────────────────────────────────

def test_mcp_mount_is_registered() -> None:
    """/mcp must be a registered mount, not a plain route."""
    app = create_app()
    mount_paths = [route.path for route in app.routes]  # type: ignore[attr-defined]
    assert "/mcp" in mount_paths
