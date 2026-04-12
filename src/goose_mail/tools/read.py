from __future__ import annotations

from goose_mail.config import load_config
from goose_mail.mail.imap_client import FakeImapClient
from goose_mail.mail.mime_parser import parse_message
from goose_mail.tools import find_account


def register(mcp, config_path: str, client_factory=None):
    _factory = client_factory or (lambda _acct: FakeImapClient())

    @mcp.tool()
    def read_message(account_id: str, message_id: str, folder: str = "INBOX") -> dict:
        cfg = load_config(config_path)
        account = find_account(cfg, account_id)
        client = _factory(account)
        raw = client.fetch_message(message_id, folder)
        flags = client.fetch_flags(message_id, folder)
        return parse_message(
            raw,
            uid=message_id,
            folder=folder,
            account_id=account.id,
            provider=account.provider,
            flags=flags,
        )
