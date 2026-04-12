from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from goose_mail import __version__
from goose_mail.tools.accounts import register as reg_accounts
from goose_mail.tools.folders import register as reg_folders
from goose_mail.tools.read import register as reg_read
from goose_mail.tools.search import register as reg_search


def create_server(
    config_path: str | None = None,
    client_factory=None,
) -> FastMCP:
    cfg_path = config_path or "config/accounts.yaml"
    mcp = FastMCP("goose_mail")

    @mcp.tool()
    def ping() -> dict:
        return {"ok": True, "service": "goose_mail", "version": __version__}

    reg_accounts(mcp, cfg_path, client_factory)
    reg_folders(mcp, cfg_path, client_factory)
    reg_search(mcp, cfg_path, client_factory)
    reg_read(mcp, cfg_path, client_factory)

    return mcp


server = create_server()
