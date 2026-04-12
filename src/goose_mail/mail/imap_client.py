from __future__ import annotations

from email.message import EmailMessage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Protocol


class ImapClient(Protocol):
    def list_folders(self) -> list[str]: ...
    def search(self, criteria: str, folder: str) -> list[str]: ...
    def fetch_message(self, uid: str, folder: str) -> bytes: ...
    def fetch_flags(self, uid: str, folder: str) -> list[str]: ...


def _build_fixture_emails() -> dict[str, dict[str, bytes]]:
    msg1 = EmailMessage()
    msg1["From"] = "Alice Smith <alice@example.com>"
    msg1["To"] = "Bob Jones <bob@example.com>"
    msg1["CC"] = "Charlie <charlie@example.com>"
    msg1["Subject"] = "Hello World"
    msg1["Date"] = "Sat, 12 Apr 2026 10:30:00 +0000"
    msg1["Message-ID"] = "<msg1@example.com>"
    msg1.set_content("Hello, this is a test message.\nWith two lines.")

    msg2 = MIMEMultipart("mixed")
    msg2["From"] = "Bob Jones <bob@example.com>"
    msg2["To"] = "Alice Smith <alice@example.com>"
    msg2["Subject"] = "Re: Hello World"
    msg2["Date"] = "Sat, 12 Apr 2026 11:00:00 +0000"
    msg2["Message-ID"] = "<msg2@example.com>"
    msg2["In-Reply-To"] = "<msg1@example.com>"

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText("Plain text version of the reply.", "plain"))
    alt.attach(
        MIMEText("<html><body><p>HTML version of the reply.</p></body></html>", "html")
    )
    msg2.attach(alt)

    attach = MIMEBase("application", "pdf")
    attach.set_payload(b"%PDF-1.4 fake content here")
    attach.add_header("Content-Disposition", "attachment", filename="invoice.pdf")
    msg2.attach(attach)

    return {
        "INBOX": {
            "1": msg1.as_bytes(),
            "2": msg2.as_bytes(),
        },
        "Sent": {},
    }


_FIXTURE_EMAILS = _build_fixture_emails()
_FIXTURE_FOLDERS = ["INBOX", "Sent", "Drafts", "Trash", "Spam", "Archive"]
_FIXTURE_FLAGS: dict[str, dict[str, list[str]]] = {
    "INBOX": {
        "1": ["\\Seen"],
        "2": ["\\Seen", "\\Flagged"],
    },
    "Sent": {},
}


class FakeImapClient:
    def list_folders(self) -> list[str]:
        return list(_FIXTURE_FOLDERS)

    def search(self, criteria: str, folder: str) -> list[str]:
        folder_msgs = _FIXTURE_EMAILS.get(folder, {})
        return list(folder_msgs.keys())

    def fetch_message(self, uid: str, folder: str) -> bytes:
        folder_msgs = _FIXTURE_EMAILS.get(folder, {})
        if uid not in folder_msgs:
            raise KeyError(f"Message {uid} not found in {folder}")
        return folder_msgs[uid]

    def fetch_flags(self, uid: str, folder: str) -> list[str]:
        folder_flags = _FIXTURE_FLAGS.get(folder, {})
        return folder_flags.get(uid, [])
