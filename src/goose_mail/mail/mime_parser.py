from __future__ import annotations

import email
import email.utils
from email.message import Message
from html.parser import HTMLParser
from typing import Any


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._pieces: list[str] = []

    def handle_data(self, data: str) -> None:
        self._pieces.append(data)

    def get_text(self) -> str:
        return " ".join(self._pieces).strip()


def html_to_text(html: str) -> str:
    ext = _TextExtractor()
    ext.feed(html)
    return ext.get_text()


def parse_addresses(header_value: str | None) -> list[dict[str, str]]:
    if not header_value:
        return []
    results = []
    for name, addr in email.utils.getaddresses([header_value]):
        results.append({"name": name, "email": addr})
    return results


def parse_flags(flag_list: list[str]) -> dict[str, bool]:
    return {
        "seen": "\\Seen" in flag_list,
        "answered": "\\Answered" in flag_list,
        "flagged": "\\Flagged" in flag_list,
        "draft": "\\Draft" in flag_list,
    }


def _extract_body(msg: Message) -> tuple[str, bool]:
    if not msg.is_multipart():
        ct = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload is None:
            return "", False
        text = payload.decode("utf-8", errors="replace")
        if ct == "text/html":
            return html_to_text(text), True
        return text, False

    text_parts: list[str] = []
    html_parts: list[str] = []
    for part in msg.walk():
        if part.get_filename():
            continue
        ct = part.get_content_type()
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        decoded = payload.decode("utf-8", errors="replace")
        if ct == "text/plain":
            text_parts.append(decoded)
        elif ct == "text/html":
            html_parts.append(decoded)

    if text_parts:
        return "\n".join(text_parts), bool(html_parts)
    if html_parts:
        return html_to_text("\n".join(html_parts)), True
    return "", False


def _extract_attachments(msg: Message) -> list[dict[str, Any]]:
    attachments = []
    for part in msg.walk():
        filename = part.get_filename()
        if not filename:
            continue
        payload = part.get_payload(decode=True)
        attachments.append(
            {
                "filename": filename,
                "content_type": part.get_content_type(),
                "size": len(payload) if payload else 0,
            }
        )
    return attachments


def parse_message(
    raw: bytes,
    uid: str = "",
    folder: str = "INBOX",
    account_id: str = "",
    provider: str = "",
    flags: list[str] | None = None,
) -> dict[str, Any]:
    msg = email.message_from_bytes(raw)

    body_text, has_html = _extract_body(msg)
    body_text = body_text.strip()
    snippet = body_text[:200].replace("\n", " ").strip()

    date_str = msg.get("Date", "")
    try:
        parsed_date = email.utils.parsedate_to_datetime(date_str)
        iso_date = parsed_date.isoformat()
    except Exception:
        iso_date = date_str

    in_reply_to = msg.get("In-Reply-To")
    thread_id = in_reply_to.strip() if in_reply_to else None

    return {
        "account_id": account_id,
        "provider": provider,
        "folder": folder,
        "message_id": msg.get("Message-ID", uid),
        "thread_id": thread_id,
        "subject": msg.get("Subject", ""),
        "from": parse_addresses(msg.get("From")),
        "to": parse_addresses(msg.get("To")),
        "cc": parse_addresses(msg.get("CC")),
        "bcc": parse_addresses(msg.get("BCC")),
        "reply_to": parse_addresses(msg.get("Reply-To")),
        "date": iso_date,
        "snippet": snippet,
        "body_text": body_text,
        "has_html": has_html,
        "flags": parse_flags(flags or []),
        "attachments": _extract_attachments(msg),
    }
