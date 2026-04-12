from __future__ import annotations

from goose_mail.config import load_config
from goose_mail.mail.mime_parser import parse_message
from goose_mail.mail.real_imap_client import ImapError, RealImapClient
from goose_mail.tools import find_account


def _make_client(account, client_factory):
    if client_factory is not None:
        return client_factory(account), True
    try:
        return RealImapClient(account), False
    except ImapError as exc:
        return None, exc


def _error_result(exc: ImapError) -> dict:
    return {"ok": False, "error": {"code": exc.code, "message": exc.message}}


def register(mcp, config_path: str, client_factory=None):
    @mcp.tool()
    def read_message(account_id: str, message_id: str, folder: str = "INBOX") -> dict:
        cfg = load_config(config_path)
        account = find_account(cfg, account_id)
        client, err = _make_client(account, client_factory)
        if client is None:
            return _error_result(err)
        try:
            raw = client.fetch_message(message_id, folder)
            flags = client.fetch_flags(message_id, folder)
            result = parse_message(
                raw,
                uid=message_id,
                folder=folder,
                account_id=account.id,
                provider=account.provider,
                flags=flags,
            )
            result["ok"] = True
            return result
        except ImapError as exc:
            return _error_result(exc)
        finally:
            if isinstance(client, RealImapClient):
                client.logout()
