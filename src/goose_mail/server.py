from mcp.server.fastmcp import FastMCP

from goose_mail import __version__


def create_server() -> FastMCP:
    mcp = FastMCP("goose_mail")

    @mcp.tool()
    def ping() -> dict:
        return {"ok": True, "service": "goose_mail", "version": __version__}

    return mcp


server = create_server()
