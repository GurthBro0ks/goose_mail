import json
import subprocess
import sys

import pytest

import goose_mail
from goose_mail.server import create_server


def test_version():
    assert goose_mail.__version__ == "0.1.0"


def test_import():
    assert hasattr(goose_mail, "__version__")


def test_main_entrypoint():
    result = subprocess.run(
        [sys.executable, "-m", "goose_mail"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0


def test_server_module_import():
    from goose_mail import server

    assert hasattr(server, "server")
    assert hasattr(server, "create_server")


def test_server_create():
    mcp = create_server()
    assert mcp.name == "goose_mail"


@pytest.mark.anyio
async def test_ping_tool_registered():
    mcp = create_server()
    tools = await mcp.list_tools()
    names = [t.name for t in tools]
    assert "ping" in names


@pytest.mark.anyio
async def test_ping_tool_handler():
    mcp = create_server()
    result = await mcp.call_tool("ping", {})
    text = result[0].text
    data = json.loads(text)
    assert data["ok"] is True
    assert data["service"] == "goose_mail"
    assert data["version"] == goose_mail.__version__
