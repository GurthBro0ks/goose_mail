import json

import pytest
import yaml

from goose_mail.mail.imap_client import FakeImapClient
from goose_mail.server import create_server


def _write_config(tmp_path, accounts=None):
    if accounts is None:
        accounts = [
            {
                "id": "test-gmail",
                "provider": "gmail",
                "email": "user@gmail.com",
                "auth": {
                    "username_env": "GMAIL_USER",
                    "password_env": "GMAIL_PASS",
                },
            },
        ]
    p = tmp_path / "accounts.yaml"
    p.write_text(yaml.dump({"accounts": accounts}), encoding="utf-8")
    return str(p)


def _make_server(tmp_path, accounts=None):
    cfg_path = _write_config(tmp_path, accounts)
    return create_server(
        config_path=cfg_path,
        client_factory=lambda _a: FakeImapClient(),
    )


class TestListAccounts:
    @pytest.mark.anyio
    async def test_returns_enabled_accounts(self, tmp_path):
        mcp = _make_server(tmp_path)
        result = await mcp.call_tool("list_accounts", {})
        data = json.loads(result[0].text)
        assert data["count"] == 1
        assert data["accounts"][0]["id"] == "test-gmail"
        assert data["accounts"][0]["provider"] == "gmail"
        assert data["accounts"][0]["email"] == "user@gmail.com"
        assert data["accounts"][0]["enabled"] is True

    @pytest.mark.anyio
    async def test_no_secrets_in_output(self, tmp_path):
        mcp = _make_server(tmp_path)
        result = await mcp.call_tool("list_accounts", {})
        text = result[0].text
        assert "password_env" not in text
        assert "GMAIL_PASS" not in text
        assert "username_env" not in text

    @pytest.mark.anyio
    async def test_only_enabled(self, tmp_path):
        accounts = [
            {
                "id": "active",
                "provider": "gmail",
                "email": "a@gmail.com",
                "enabled": True,
                "auth": {"username_env": "U1", "password_env": "P1"},
            },
            {
                "id": "disabled",
                "provider": "gmail",
                "email": "b@gmail.com",
                "enabled": False,
                "auth": {"username_env": "U2", "password_env": "P2"},
            },
        ]
        mcp = _make_server(tmp_path, accounts)
        result = await mcp.call_tool("list_accounts", {})
        data = json.loads(result[0].text)
        assert data["count"] == 1
        assert data["accounts"][0]["id"] == "active"

    @pytest.mark.anyio
    async def test_multiple_accounts(self, tmp_path):
        accounts = [
            {
                "id": "gmail",
                "provider": "gmail",
                "email": "a@gmail.com",
                "auth": {"username_env": "U1", "password_env": "P1"},
            },
            {
                "id": "outlook",
                "provider": "outlook",
                "email": "b@outlook.com",
                "auth": {"username_env": "U2", "password_env": "P2"},
            },
        ]
        mcp = _make_server(tmp_path, accounts)
        result = await mcp.call_tool("list_accounts", {})
        data = json.loads(result[0].text)
        assert data["count"] == 2
        ids = [a["id"] for a in data["accounts"]]
        assert "gmail" in ids
        assert "outlook" in ids


class TestListFolders:
    @pytest.mark.anyio
    async def test_returns_folders(self, tmp_path):
        mcp = _make_server(tmp_path)
        result = await mcp.call_tool("list_folders", {"account_id": "test-gmail"})
        data = json.loads(result[0].text)
        assert "INBOX" in data["folders"]
        assert "Sent" in data["folders"]
        assert "Drafts" in data["folders"]
        assert data["account_id"] == "test-gmail"

    @pytest.mark.anyio
    async def test_unknown_account_raises(self, tmp_path):
        mcp = _make_server(tmp_path)
        with pytest.raises(Exception):
            await mcp.call_tool("list_folders", {"account_id": "nonexistent"})


class TestSearchMail:
    @pytest.mark.anyio
    async def test_returns_results(self, tmp_path):
        mcp = _make_server(tmp_path)
        result = await mcp.call_tool(
            "search_mail",
            {"account_id": "test-gmail", "query": "test"},
        )
        data = json.loads(result[0].text)
        assert data["count"] >= 1
        for item in data["results"]:
            assert "message_id" in item
            assert "subject" in item
            assert "from" in item
            assert "date" in item
            assert "snippet" in item
            assert "flags" in item

    @pytest.mark.anyio
    async def test_respects_limit(self, tmp_path):
        mcp = _make_server(tmp_path)
        result = await mcp.call_tool(
            "search_mail",
            {"account_id": "test-gmail", "query": "test", "limit": 1},
        )
        data = json.loads(result[0].text)
        assert data["count"] <= 1

    @pytest.mark.anyio
    async def test_compact_no_body(self, tmp_path):
        mcp = _make_server(tmp_path)
        result = await mcp.call_tool(
            "search_mail",
            {"account_id": "test-gmail", "query": "test"},
        )
        data = json.loads(result[0].text)
        for item in data["results"]:
            assert "body_text" not in item
            assert "attachments" not in item

    @pytest.mark.anyio
    async def test_unknown_account_raises(self, tmp_path):
        mcp = _make_server(tmp_path)
        with pytest.raises(Exception):
            await mcp.call_tool(
                "search_mail",
                {"account_id": "nope", "query": "test"},
            )


class TestReadMessage:
    @pytest.mark.anyio
    async def test_simple_message(self, tmp_path):
        mcp = _make_server(tmp_path)
        result = await mcp.call_tool(
            "read_message",
            {"account_id": "test-gmail", "message_id": "1"},
        )
        data = json.loads(result[0].text)
        assert data["account_id"] == "test-gmail"
        assert data["provider"] == "gmail"
        assert data["folder"] == "INBOX"
        assert data["subject"] == "Hello World"
        assert data["from"][0]["name"] == "Alice Smith"
        assert data["from"][0]["email"] == "alice@example.com"
        assert "Hello, this is a test message." in data["body_text"]
        assert data["has_html"] is False
        assert data["flags"]["seen"] is True
        assert data["flags"]["flagged"] is False
        assert data["attachments"] == []
        assert data["thread_id"] is None
        assert len(data["cc"]) == 1

    @pytest.mark.anyio
    async def test_multipart_with_attachment(self, tmp_path):
        mcp = _make_server(tmp_path)
        result = await mcp.call_tool(
            "read_message",
            {"account_id": "test-gmail", "message_id": "2"},
        )
        data = json.loads(result[0].text)
        assert data["subject"] == "Re: Hello World"
        assert "Plain text version of the reply." in data["body_text"]
        assert data["has_html"] is True
        assert len(data["attachments"]) == 1
        assert data["attachments"][0]["filename"] == "invoice.pdf"
        assert data["attachments"][0]["content_type"] == "application/pdf"
        assert data["attachments"][0]["size"] > 0
        assert data["thread_id"] == "<msg1@example.com>"
        assert data["flags"]["seen"] is True
        assert data["flags"]["flagged"] is True

    @pytest.mark.anyio
    async def test_normalized_shape(self, tmp_path):
        mcp = _make_server(tmp_path)
        result = await mcp.call_tool(
            "read_message",
            {"account_id": "test-gmail", "message_id": "1"},
        )
        data = json.loads(result[0].text)
        required_keys = {
            "account_id",
            "provider",
            "folder",
            "message_id",
            "thread_id",
            "subject",
            "from",
            "to",
            "cc",
            "bcc",
            "reply_to",
            "date",
            "snippet",
            "body_text",
            "has_html",
            "flags",
            "attachments",
        }
        assert required_keys == set(data.keys())

    @pytest.mark.anyio
    async def test_flags_shape(self, tmp_path):
        mcp = _make_server(tmp_path)
        result = await mcp.call_tool(
            "read_message",
            {"account_id": "test-gmail", "message_id": "1"},
        )
        data = json.loads(result[0].text)
        flags = data["flags"]
        assert set(flags.keys()) == {"seen", "answered", "flagged", "draft"}

    @pytest.mark.anyio
    async def test_attachment_shape(self, tmp_path):
        mcp = _make_server(tmp_path)
        result = await mcp.call_tool(
            "read_message",
            {"account_id": "test-gmail", "message_id": "2"},
        )
        data = json.loads(result[0].text)
        attach = data["attachments"][0]
        assert set(attach.keys()) == {"filename", "content_type", "size"}

    @pytest.mark.anyio
    async def test_nonexistent_message_raises(self, tmp_path):
        mcp = _make_server(tmp_path)
        with pytest.raises(Exception):
            await mcp.call_tool(
                "read_message",
                {"account_id": "test-gmail", "message_id": "999"},
            )

    @pytest.mark.anyio
    async def test_unknown_account_raises(self, tmp_path):
        mcp = _make_server(tmp_path)
        with pytest.raises(Exception):
            await mcp.call_tool(
                "read_message",
                {"account_id": "nope", "message_id": "1"},
            )
