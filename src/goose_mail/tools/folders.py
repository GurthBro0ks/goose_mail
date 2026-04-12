from __future__ import annotations

from goose_mail.config import load_config
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
    def list_folders(account_id: str) -> dict:
        cfg = load_config(config_path)
        account = find_account(cfg, account_id)
        client, err = _make_client(account, client_factory)
        if client is None:
            return _error_result(err)
        try:
            folders = client.list_folders()
            return {
                "ok": True,
                "account_id": account_id,
                "folders": folders,
                "count": len(folders),
            }
        except ImapError as exc:
            return _error_result(exc)
        finally:
            if isinstance(client, RealImapClient):
                client.logout()
