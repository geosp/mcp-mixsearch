from importlib.metadata import version

from fastmcp import Client, FastMCP
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


async def test_server_info_reports_installed_version():
    config = AppConfig()
    mcp = server.MixSearchServer(config.server, server.MixSearchService(config)).create_mcp_app()
    async with Client(mcp, mode="legacy") as client:
        info = client.initialize_result.server_info
    assert info.version == version("mcp-mixsearch")
