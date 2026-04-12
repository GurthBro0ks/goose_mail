import json

import pytest
import yaml

from goose_mail.mail.smtp_client import FakeSmtpClient, build_message
from goose_mail.server import create_server


def _write_config(tmp_path, accounts=None):
    if accounts is None:
        accounts = [
            {
                "id": "test-gmail",
                "provider": "gmail",
                "email": "user@gmail.com",
                "auth": {"username_env": "GMAIL_USER", "password_env": "GMAIL_PASS"},
            },
        ]
    p = tmp_path / "accounts.yaml"
    p.write_text(yaml.dump({"accounts": accounts}), encoding="utf-8")
    return str(p)


def _make_server(tmp_path, accounts=None):
    cfg_path = _write_config(tmp_path, accounts)
    return create_server(
        config_path=cfg_path,
        smtp_factory=lambda _settings: FakeSmtpClient(),
    )


def _make_server_with_capture(tmp_path, accounts=None):
    cfg_path = _write_config(tmp_path, accounts)
    client = FakeSmtpClient()
    mcp = create_server(
        config_path=cfg_path,
        smtp_factory=lambda _settings: client,
    )
    return mcp, client


class TestBuildMessage:
    def test_plain_text(self):
        raw = build_message(
            from_addr="a@example.com",
            to=["b@example.com"],
            subject="Test",
            body_text="Hello",
        )
        msg = raw.decode("utf-8")
        assert "From: a@example.com" in msg
        assert "To: b@example.com" in msg
        assert "Subject: Test" in msg
        assert "Hello" in msg

    def test_with_cc(self):
        raw = build_message(
            from_addr="a@example.com",
            to=["b@example.com"],
            subject="CC Test",
            body_text="Body",
            cc=["c@example.com"],
        )
        msg = raw.decode("utf-8")
        assert "Cc: c@example.com" in msg

    def test_no_cc_header_when_empty(self):
        raw = build_message(
            from_addr="a@example.com",
            to=["b@example.com"],
            subject="No CC",
            body_text="Body",
        )
        msg = raw.decode("utf-8")
        assert "Cc:" not in msg

    def test_with_html(self):
        raw = build_message(
            from_addr="a@example.com",
            to=["b@example.com"],
            subject="HTML",
            body_text="Plain",
            body_html="<p>HTML</p>",
        )
        msg = raw.decode("utf-8")
        assert "Plain" in msg
        assert "<p>HTML</p>" in msg
        assert "multipart/alternative" in msg

    def test_multiple_to(self):
        raw = build_message(
            from_addr="a@example.com",
            to=["b@example.com", "c@example.com"],
            subject="Multi",
            body_text="Body",
        )
        msg = raw.decode("utf-8")
        assert "b@example.com" in msg
        assert "c@example.com" in msg


class TestFakeSmtpClient:
    def test_send_records(self):
        client = FakeSmtpClient()
        client.send("a@b.com", ["c@d.com"], b"raw message")
        assert len(client.sent) == 1
        assert client.sent[0]["from"] == "a@b.com"
        assert client.sent[0]["to"] == ["c@d.com"]
        assert client.sent[0]["raw_size"] == 11

    def test_multiple_sends(self):
        client = FakeSmtpClient()
        client.send("a@b.com", ["c@d.com"], b"msg1")
        client.send("a@b.com", ["e@f.com"], b"msg2")
        assert len(client.sent) == 2


class TestSendMailTool:
    @pytest.mark.anyio
    async def test_send_success(self, tmp_path):
        mcp, fake_smtp = _make_server_with_capture(tmp_path)
        result = await mcp.call_tool(
            "send_mail",
            {
                "account_id": "test-gmail",
                "to": ["recipient@example.com"],
                "subject": "Hello",
                "body_text": "Test body",
            },
        )
        data = json.loads(result[0].text)
        assert data["ok"] is True
        assert data["account_id"] == "test-gmail"
        assert data["provider"] == "gmail"
        assert data["message"]["subject"] == "Hello"
        assert data["message"]["to"] == ["recipient@example.com"]
        assert data["message"]["cc"] == []
        assert data["message"]["bcc"] == []
        assert data["transport"]["host"] == "smtp.gmail.com"
        assert data["transport"]["port"] == 587
        assert len(fake_smtp.sent) == 1

    @pytest.mark.anyio
    async def test_send_with_cc_bcc(self, tmp_path):
        mcp, fake_smtp = _make_server_with_capture(tmp_path)
        result = await mcp.call_tool(
            "send_mail",
            {
                "account_id": "test-gmail",
                "to": ["to@example.com"],
                "subject": "CC/BCC",
                "body_text": "Body",
                "cc": ["cc@example.com"],
                "bcc": ["bcc@example.com"],
            },
        )
        data = json.loads(result[0].text)
        assert data["ok"] is True
        assert data["message"]["cc"] == ["cc@example.com"]
        assert data["message"]["bcc"] == ["bcc@example.com"]
        sent = fake_smtp.sent[0]
        assert "to@example.com" in sent["to"]
        assert "cc@example.com" in sent["to"]
        assert "bcc@example.com" in sent["to"]

    @pytest.mark.anyio
    async def test_send_with_html(self, tmp_path):
        mcp, fake_smtp = _make_server_with_capture(tmp_path)
        result = await mcp.call_tool(
            "send_mail",
            {
                "account_id": "test-gmail",
                "to": ["to@example.com"],
                "subject": "HTML",
                "body_text": "Plain",
                "body_html": "<p>HTML</p>",
            },
        )
        data = json.loads(result[0].text)
        assert data["ok"] is True
        raw = fake_smtp.sent[0]
        assert raw["raw_size"] > 0

    @pytest.mark.anyio
    async def test_send_no_smtp_configured(self, tmp_path):
        accounts = [
            {
                "id": "no-smtp",
                "provider": "generic",
                "email": "user@example.org",
                "imap": {"host": "imap.example.org", "port": 993, "ssl": True},
                "auth": {"username_env": "U", "password_env": "P"},
            },
        ]
        mcp = _make_server(tmp_path, accounts)
        result = await mcp.call_tool(
            "send_mail",
            {
                "account_id": "no-smtp",
                "to": ["to@example.com"],
                "subject": "Test",
                "body_text": "Body",
            },
        )
        data = json.loads(result[0].text)
        assert data["ok"] is False
        assert data["error"]["code"] == "SMTP_NOT_CONFIGURED"
        assert "no-smtp" in data["error"]["message"]

    @pytest.mark.anyio
    async def test_send_empty_to(self, tmp_path):
        mcp, fake_smtp = _make_server_with_capture(tmp_path)
        result = await mcp.call_tool(
            "send_mail",
            {
                "account_id": "test-gmail",
                "to": [],
                "subject": "Test",
                "body_text": "Body",
            },
        )
        data = json.loads(result[0].text)
        assert data["ok"] is False
        assert data["error"]["code"] == "MISSING_RECIPIENTS"
        assert len(fake_smtp.sent) == 0

    @pytest.mark.anyio
    async def test_send_empty_subject(self, tmp_path):
        mcp, fake_smtp = _make_server_with_capture(tmp_path)
        result = await mcp.call_tool(
            "send_mail",
            {
                "account_id": "test-gmail",
                "to": ["to@example.com"],
                "subject": "",
                "body_text": "Body",
            },
        )
        data = json.loads(result[0].text)
        assert data["ok"] is False
        assert data["error"]["code"] == "MISSING_SUBJECT"
        assert len(fake_smtp.sent) == 0

    @pytest.mark.anyio
    async def test_send_unknown_account(self, tmp_path):
        mcp = _make_server(tmp_path)
        with pytest.raises(Exception):
            await mcp.call_tool(
                "send_mail",
                {
                    "account_id": "nonexistent",
                    "to": ["to@example.com"],
                    "subject": "Test",
                    "body_text": "Body",
                },
            )

    @pytest.mark.anyio
    async def test_send_no_secrets_in_output(self, tmp_path):
        mcp, _ = _make_server_with_capture(tmp_path)
        result = await mcp.call_tool(
            "send_mail",
            {
                "account_id": "test-gmail",
                "to": ["to@example.com"],
                "subject": "Test",
                "body_text": "Body",
            },
        )
        text = result[0].text
        assert "GMAIL_PASS" not in text
        assert "password_env" not in text
        assert "username_env" not in text

    @pytest.mark.anyio
    async def test_send_success_shape(self, tmp_path):
        mcp, _ = _make_server_with_capture(tmp_path)
        result = await mcp.call_tool(
            "send_mail",
            {
                "account_id": "test-gmail",
                "to": ["to@example.com"],
                "subject": "Shape test",
                "body_text": "Body",
            },
        )
        data = json.loads(result[0].text)
        assert set(data.keys()) == {
            "ok",
            "account_id",
            "provider",
            "message",
            "transport",
        }
        assert set(data["message"].keys()) == {"subject", "to", "cc", "bcc"}
        assert set(data["transport"].keys()) == {"host", "port", "ssl"}

    @pytest.mark.anyio
    async def test_send_error_shape(self, tmp_path):
        accounts = [
            {
                "id": "bare",
                "provider": "generic",
                "email": "u@example.org",
                "imap": {"host": "imap.example.org", "port": 993, "ssl": True},
                "auth": {"username_env": "U", "password_env": "P"},
            },
        ]
        mcp = _make_server(tmp_path, accounts)
        result = await mcp.call_tool(
            "send_mail",
            {
                "account_id": "bare",
                "to": ["to@example.com"],
                "subject": "Test",
                "body_text": "Body",
            },
        )
        data = json.loads(result[0].text)
        assert set(data.keys()) == {"ok", "error"}
        assert set(data["error"].keys()) == {"code", "message"}
