from __future__ import annotations

from goose_mail.config import load_config
from goose_mail.mail.imap_client import FakeImapClient
from goose_mail.tools import find_account


def register(mcp, config_path: str, client_factory=None):
    _factory = client_factory or (lambda _acct: FakeImapClient())

    @mcp.tool()
    def list_folders(account_id: str) -> dict:
        cfg = load_config(config_path)
        account = find_account(cfg, account_id)
        client = _factory(account)
        folders = client.list_folders()
        return {"account_id": account_id, "folders": folders, "count": len(folders)}
