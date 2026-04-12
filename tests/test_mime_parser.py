from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from goose_mail.mail.mime_parser import (
    html_to_text,
    parse_addresses,
    parse_flags,
    parse_message,
)


class TestParseAddresses:
    def test_single(self):
        result = parse_addresses("Alice <alice@example.com>")
        assert result == [{"name": "Alice", "email": "alice@example.com"}]

    def test_multiple(self):
        result = parse_addresses("Alice <alice@example.com>, Bob <bob@example.com>")
        assert len(result) == 2
        assert result[0]["email"] == "alice@example.com"
        assert result[1]["email"] == "bob@example.com"

    def test_email_only(self):
        result = parse_addresses("alice@example.com")
        assert result == [{"name": "", "email": "alice@example.com"}]

    def test_none(self):
        assert parse_addresses(None) == []

    def test_empty(self):
        assert parse_addresses("") == []


class TestHtmlToText:
    def test_simple(self):
        assert html_to_text("<p>Hello world</p>") == "Hello world"

    def test_nested(self):
        text = html_to_text("<div><p>Hello</p><p>World</p></div>")
        assert "Hello" in text
        assert "World" in text

    def test_empty(self):
        assert html_to_text("") == ""

    def test_entities_preserved(self):
        text = html_to_text("<p>A &amp; B</p>")
        assert "A & B" in text


class TestParseFlags:
    def test_seen(self):
        assert parse_flags(["\\Seen"]) == {
            "seen": True,
            "answered": False,
            "flagged": False,
            "draft": False,
        }

    def test_multiple(self):
        result = parse_flags(["\\Seen", "\\Flagged"])
        assert result["seen"] is True
        assert result["flagged"] is True
        assert result["answered"] is False

    def test_empty(self):
        result = parse_flags([])
        assert all(v is False for v in result.values())


class TestParseMessage:
    def test_simple_text(self):
        raw = (
            b"From: Alice <alice@example.com>\r\n"
            b"To: Bob <bob@example.com>\r\n"
            b"Subject: Test\r\n"
            b"Date: Sat, 12 Apr 2026 10:30:00 +0000\r\n"
            b"Message-ID: <msg1@example.com>\r\n"
            b"\r\n"
            b"Hello, this is a test.\r\n"
        )
        result = parse_message(
            raw,
            uid="1",
            folder="INBOX",
            account_id="test",
            provider="gmail",
            flags=["\\Seen"],
        )
        assert result["account_id"] == "test"
        assert result["provider"] == "gmail"
        assert result["folder"] == "INBOX"
        assert result["subject"] == "Test"
        assert result["from"] == [{"name": "Alice", "email": "alice@example.com"}]
        assert result["body_text"] == "Hello, this is a test."
        assert result["has_html"] is False
        assert result["flags"]["seen"] is True
        assert result["attachments"] == []
        assert result["snippet"] == "Hello, this is a test."
        assert "2026-04-12" in result["date"]

    def test_with_cc(self):
        raw = (
            b"From: alice@example.com\r\n"
            b"To: bob@example.com\r\n"
            b"Cc: charlie@example.com\r\n"
            b"Subject: CC Test\r\n"
            b"Date: Sat, 12 Apr 2026 10:30:00 +0000\r\n"
            b"\r\n"
            b"Body text.\r\n"
        )
        result = parse_message(raw)
        assert len(result["cc"]) == 1
        assert result["cc"][0]["email"] == "charlie@example.com"

    def test_html_fallback(self):
        raw = (
            b"From: alice@example.com\r\n"
            b"To: bob@example.com\r\n"
            b"Subject: HTML Test\r\n"
            b"Date: Sat, 12 Apr 2026 10:30:00 +0000\r\n"
            b"Content-Type: text/html\r\n"
            b"\r\n"
            b"<html><body><p>Hello HTML</p></body></html>\r\n"
        )
        result = parse_message(raw)
        assert "Hello HTML" in result["body_text"]
        assert result["has_html"] is True

    def test_multipart_with_attachment(self):
        msg = MIMEMultipart("mixed")
        msg["From"] = "bob@example.com"
        msg["To"] = "alice@example.com"
        msg["Subject"] = "Multipart Test"
        msg["Date"] = "Sat, 12 Apr 2026 11:00:00 +0000"

        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText("Plain text body.", "plain"))
        alt.attach(MIMEText("<html><body><p>HTML body.</p></body></html>", "html"))
        msg.attach(alt)

        attach = MIMEBase("application", "pdf")
        attach.set_payload(b"%PDF-1.4 fake")
        attach.add_header("Content-Disposition", "attachment", filename="test.pdf")
        msg.attach(attach)

        result = parse_message(msg.as_bytes())
        assert result["body_text"] == "Plain text body."
        assert result["has_html"] is True
        assert len(result["attachments"]) == 1
        assert result["attachments"][0]["filename"] == "test.pdf"
        assert result["attachments"][0]["content_type"] == "application/pdf"
        assert result["attachments"][0]["size"] > 0

    def test_thread_id_from_in_reply_to(self):
        raw = (
            b"From: bob@example.com\r\n"
            b"To: alice@example.com\r\n"
            b"Subject: Re: Test\r\n"
            b"Date: Sat, 12 Apr 2026 11:00:00 +0000\r\n"
            b"In-Reply-To: <original@example.com>\r\n"
            b"\r\n"
            b"Reply body.\r\n"
        )
        result = parse_message(raw)
        assert result["thread_id"] == "<original@example.com>"

    def test_no_thread_id(self):
        raw = (
            b"From: alice@example.com\r\n"
            b"To: bob@example.com\r\n"
            b"Subject: Test\r\n"
            b"Date: Sat, 12 Apr 2026 10:30:00 +0000\r\n"
            b"\r\n"
            b"Body.\r\n"
        )
        result = parse_message(raw)
        assert result["thread_id"] is None

    def test_snippet_truncation(self):
        raw = (
            b"From: alice@example.com\r\n"
            b"To: bob@example.com\r\n"
            b"Subject: Long\r\n"
            b"Date: Sat, 12 Apr 2026 10:30:00 +0000\r\n"
            b"\r\n" + b"A" * 500 + b"\r\n"
        )
        result = parse_message(raw)
        assert len(result["snippet"]) <= 200

    def test_empty_body(self):
        raw = (
            b"From: alice@example.com\r\n"
            b"To: bob@example.com\r\n"
            b"Subject: Empty\r\n"
            b"Date: Sat, 12 Apr 2026 10:30:00 +0000\r\n"
            b"\r\n"
        )
        result = parse_message(raw)
        assert result["body_text"] == ""
        assert result["snippet"] == ""

    def test_bcc_and_reply_to(self):
        raw = (
            b"From: alice@example.com\r\n"
            b"To: bob@example.com\r\n"
            b"Bcc: secret@example.com\r\n"
            b"Reply-To: replies@example.com\r\n"
            b"Subject: BCC Test\r\n"
            b"Date: Sat, 12 Apr 2026 10:30:00 +0000\r\n"
            b"\r\n"
            b"Body.\r\n"
        )
        result = parse_message(raw)
        assert result["bcc"][0]["email"] == "secret@example.com"
        assert result["reply_to"][0]["email"] == "replies@example.com"
