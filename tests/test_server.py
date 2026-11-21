from importlib.metadata import version

from fastmcp import FastMCP
from starlette.testclient import TestClient

import server
from config import AppConfig


def test_health_reports_installed_version():
    mcp = FastMCP("test")
    server.MixSearchService(AppConfig()).register_mcp_tools(mcp)
    with TestClient(mcp.http_app()) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == version("mcp-mixsearch")


def test_server_info_reports_installed_version():
    assert server.SERVICE_VERSION == version("mcp-mixsearch")
    assert server.MixSearchServer.service_version.fget(None) == version("mcp-mixsearch")
