from __future__ import annotations

from goose_mail.config import load_config
from goose_mail.mail.smtp_client import FakeSmtpClient, build_message
from goose_mail.tools import find_account


def register(mcp, config_path: str, smtp_factory=None):
    _factory = smtp_factory or (lambda _settings: FakeSmtpClient())

    @mcp.tool()
    def send_mail(
        account_id: str,
        to: list[str],
        subject: str,
        body_text: str,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        body_html: str | None = None,
    ) -> dict:
        cfg = load_config(config_path)
        account = find_account(cfg, account_id)

        if account.smtp is None:
            return {
                "ok": False,
                "error": {
                    "code": "SMTP_NOT_CONFIGURED",
                    "message": f"SMTP is not configured for account {account.id!r}.",
                },
            }

        cc = cc or []
        bcc = bcc or []

        if not to:
            return {
                "ok": False,
                "error": {
                    "code": "MISSING_RECIPIENTS",
                    "message": "At least one 'to' recipient is required.",
                },
            }

        if not subject:
            return {
                "ok": False,
                "error": {
                    "code": "MISSING_SUBJECT",
                    "message": "Subject is required.",
                },
            }

        message_bytes = build_message(
            from_addr=account.email,
            to=to,
            subject=subject,
            body_text=body_text,
            cc=cc,
            bcc=bcc,
            body_html=body_html,
        )

        client = _factory(account.smtp)
        all_recipients = list(to) + list(cc) + list(bcc)
        client.send(account.email, all_recipients, message_bytes)

        return {
            "ok": True,
            "account_id": account.id,
            "provider": account.provider,
            "message": {
                "subject": subject,
                "to": to,
                "cc": cc,
                "bcc": bcc,
            },
            "transport": {
                "host": account.smtp.host,
                "port": account.smtp.port,
                "ssl": account.smtp.ssl,
            },
        }
