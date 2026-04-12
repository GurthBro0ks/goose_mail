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
    def search_mail(
        account_id: str,
        query: str,
        folder: str = "INBOX",
        limit: int = 20,
    ) -> dict:
        cfg = load_config(config_path)
        account = find_account(cfg, account_id)
        client, err = _make_client(account, client_factory)
        if client is None:
            return _error_result(err)
        try:
            uids = client.search(query, folder)[:limit]
            results = []
            for uid in uids:
                raw = client.fetch_message(uid, folder)
                flags = client.fetch_flags(uid, folder)
                parsed = parse_message(
                    raw,
                    uid=uid,
                    folder=folder,
                    account_id=account.id,
                    provider=account.provider,
                    flags=flags,
                )
                results.append(
                    {
                        "message_id": uid,
                        "subject": parsed["subject"],
                        "from": parsed["from"],
                        "date": parsed["date"],
                        "snippet": parsed["snippet"],
                        "flags": parsed["flags"],
                    }
                )
            return {"ok": True, "results": results, "count": len(results)}
        except ImapError as exc:
            return _error_result(exc)
        finally:
            if isinstance(client, RealImapClient):
                client.logout()
