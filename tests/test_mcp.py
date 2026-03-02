"""Tests for the MCP Streamable HTTP transport layer."""

import json

import pytest
from fastapi.testclient import TestClient

from repohealth_mcp.app import create_app
from repohealth_mcp.transport.mcp_factory import create_mcp_server


# ── Server creation ───────────────────────────────────────────────────────────

def test_create_mcp_server_returns_fastmcp() -> None:
    from mcp.server.fastmcp import FastMCP

    mcp = create_mcp_server()
    assert isinstance(mcp, FastMCP)


def test_mcp_server_name() -> None:
    mcp = create_mcp_server()
    assert mcp.name == "RepoHealth MCP"


def test_all_four_tools_registered() -> None:
    """All four tool names must be present on the FastMCP instance."""
    mcp = create_mcp_server()
    registered = {t.name for t in mcp._tool_manager.list_tools()}
    expected = {"scan_tech_debt", "diagnose_ci_logs", "analyze_dependencies", "project_health_report"}
    assert expected == registered


def test_tools_have_descriptions() -> None:
    """Every tool must have a non-empty description."""
    mcp = create_mcp_server()
    for tool in mcp._tool_manager.list_tools():
        assert tool.description, f"Tool '{tool.name}' is missing a description"


# ── /mcp endpoint reachability ────────────────────────────────────────────────

@pytest.fixture()
def client():
    # MCP SDK v1.26+ enables DNS rebinding protection by default.
    # It allows "localhost:*" but NOT bare "localhost" (no port).
    # base_url="http://localhost:8000" → Host: localhost:8000, which matches.
    app = create_app()
    with TestClient(app, base_url="http://localhost:8000") as c:
        yield c


def test_mcp_endpoint_exists_post(client: TestClient) -> None:
    """POST /mcp must not return 404 (it may return 400/422 for a bad body)."""
    response = client.post("/mcp", json={})
    assert response.status_code != 404


def test_mcp_endpoint_exists_get(client: TestClient) -> None:
    """GET /mcp must not return 404 (used for SSE/server notifications)."""
    response = client.get("/mcp", headers={"Accept": "text/event-stream"})
    assert response.status_code != 404


def test_health_still_works_with_mcp_mounted(client: TestClient) -> None:
    """/health must remain functional after MCP is mounted."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ── Streamable HTTP basic handshake ───────────────────────────────────────────

def _parse_mcp_response(response: "TestClient") -> dict:  # type: ignore[type-arg]
    """Parse an MCP response body, which may be plain JSON or SSE-wrapped JSON.

    The MCP Streamable HTTP transport returns SSE-formatted responses when the
    client advertises ``Accept: text/event-stream``. This helper extracts the
    first JSON-RPC message from either format.
    """
    text = response.text
    # SSE format: "event: message\r\ndata: {...}\r\n\r\n"
    for line in text.splitlines():
        if line.startswith("data: "):
            return json.loads(line[len("data: "):])
    # Fallback: plain JSON response
    return json.loads(text)


def _mcp_headers(**extra: str) -> dict[str, str]:
    """Return the minimum headers required by MCP Streamable HTTP spec."""
    return {
        "Content-Type": "application/json",
        # Streamable HTTP requires the client to accept both JSON and SSE.
        "Accept": "application/json, text/event-stream",
        **extra,
    }


def test_mcp_initialize_request(client: TestClient) -> None:
    """A minimal MCP initialize request should receive a valid JSON-RPC response."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "0.0.1"},
        },
    }
    response = client.post("/mcp", json=payload, headers=_mcp_headers())
    # MCP server must return 200 with a JSON-RPC result envelope
    assert response.status_code == 200
    body = _parse_mcp_response(response)
    assert body.get("jsonrpc") == "2.0"
    assert body.get("id") == 1
    assert "result" in body


def test_mcp_tools_list_request(client: TestClient) -> None:
    """tools/list must return all four registered tools."""
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "0.0.1"},
        },
    }
    init_resp = client.post("/mcp", json=init_payload, headers=_mcp_headers())
    assert init_resp.status_code == 200

    # Carry the session ID so the second request is treated as the same session.
    session_id = init_resp.headers.get("mcp-session-id")
    extra = {"mcp-session-id": session_id} if session_id else {}

    list_payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    list_resp = client.post("/mcp", json=list_payload, headers=_mcp_headers(**extra))
    assert list_resp.status_code == 200

    body = _parse_mcp_response(list_resp)
    assert "result" in body
    tool_names = {t["name"] for t in body["result"].get("tools", [])}
    assert "scan_tech_debt" in tool_names
    assert "diagnose_ci_logs" in tool_names
    assert "analyze_dependencies" in tool_names
    assert "project_health_report" in tool_names
