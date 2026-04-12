from __future__ import annotations

from goose_mail.config import load_config
from goose_mail.mail.imap_client import FakeImapClient
from goose_mail.mail.mime_parser import parse_message
from goose_mail.tools import find_account


def register(mcp, config_path: str, client_factory=None):
    _factory = client_factory or (lambda _acct: FakeImapClient())

    @mcp.tool()
    def search_mail(
        account_id: str,
        query: str,
        folder: str = "INBOX",
        limit: int = 20,
    ) -> dict:
        cfg = load_config(config_path)
        account = find_account(cfg, account_id)
        client = _factory(account)
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
        return {"results": results, "count": len(results)}
