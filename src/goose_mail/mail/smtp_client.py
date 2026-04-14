from __future__ import annotations

import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from typing import Protocol


class SmtpClient(Protocol):
    def send(
        self, from_addr: str, to_addrs: list[str], message_bytes: bytes
    ) -> None: ...


class FakeSmtpClient:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    def send(self, from_addr: str, to_addrs: list[str], message_bytes: bytes) -> None:
        self.sent.append(
            {
                "from": from_addr,
                "to": to_addrs,
                "raw_size": len(message_bytes),
            }
        )


def build_message(
    from_addr: str,
    to: list[str],
    subject: str,
    body_text: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    body_html: str | None = None,
) -> bytes:
    cc = cc or []
    bcc = bcc or []

    if body_html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))
    else:
        msg = MIMEMultipart("mixed")
        msg.attach(MIMEText(body_text, "plain"))

    msg["From"] = from_addr
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = f"<{uuid.uuid4()}@{from_addr.split('@')[-1]}>"
    msg["MIME-Version"] = "1.0"

    return msg.as_bytes()
