from __future__ import annotations

import imaplib
import os
from typing import Any


class ImapError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class RealImapClient:
    def __init__(self, account: Any) -> None:
        self._account = account
        self._host = account.imap.host
        self._port = account.imap.port
        self._use_ssl = account.imap.ssl
        username = os.environ.get(account.auth.username_env, "")
        password = os.environ.get(account.auth.password_env, "")
        if not username or not password:
            raise ImapError(
                "AUTH_MISSING",
                (
                    f"Credentials not found in env vars"
                    f" {account.auth.username_env}/{account.auth.password_env}"
                ),
            )
        self._username = username
        self._password = password
        self._conn: imaplib.IMAP4 | imaplib.IMAP4_SSL | None = None

    def _connect(self) -> imaplib.IMAP4 | imaplib.IMAP4_SSL:
        try:
            if self._use_ssl:
                conn = imaplib.IMAP4_SSL(self._host, self._port)
            else:
                conn = imaplib.IMAP4(self._host, self._port)
        except OSError as exc:
            raise ImapError(
                "CONNECTION_FAILED",
                f"Cannot connect to {self._host}:{self._port}: {exc}",
            ) from exc
        try:
            conn.login(self._username, self._password)
        except imaplib.IMAP4.error as exc:
            raise ImapError(
                "AUTH_FAILED",
                f"Authentication failed for {self._account.id}: {exc}",
            ) from exc
        return conn

    def _get_conn(self) -> imaplib.IMAP4 | imaplib.IMAP4_SSL:
        if self._conn is None:
            self._conn = self._connect()
        return self._conn

    def _select(self, folder: str) -> imaplib.IMAP4 | imaplib.IMAP4_SSL:
        conn = self._get_conn()
        status, data = conn.select(f'"{folder}"', readonly=True)
        if status != "OK":
            raise ImapError("BAD_FOLDER", f"Cannot select folder {folder!r}: {data}")
        return conn

    def list_folders(self) -> list[str]:
        conn = self._get_conn()
        status, data = conn.list()
        if status != "OK":
            raise ImapError("LIST_FAILED", "Failed to list folders")
        folders: list[str] = []
        for item in data:
            if not item:
                continue
            if isinstance(item, bytes):
                parts = item.decode("utf-8", errors="replace").split('"/"')
                if len(parts) >= 2:
                    name = parts[-1].strip().strip('"')
                else:
                    name = item.decode("utf-8", errors="replace").strip()
                folders.append(name)
        return folders

    def search(self, criteria: str, folder: str) -> list[str]:
        conn = self._select(folder)
        search_criteria = f'(OR SUBJECT "{criteria}" FROM "{criteria}")'
        status, data = conn.search(None, search_criteria)
        if status != "OK":
            raise ImapError("SEARCH_FAILED", f"Search failed in {folder}")
        if not data or not data[0]:
            return []
        return [uid.strip() for uid in data[0].decode("utf-8").split() if uid.strip()]

    def fetch_message(self, uid: str, folder: str) -> bytes:
        conn = self._select(folder)
        status, data = conn.fetch(uid, "(RFC822)")
        if status != "OK" or not data or not data[0]:
            raise ImapError(
                "MESSAGE_NOT_FOUND",
                f"Message {uid} not found in {folder}",
            )
        for item in data:
            if isinstance(item, tuple) and len(item) >= 2:
                return item[1]
        raise ImapError(
            "MESSAGE_NOT_FOUND",
            f"Message {uid} not found in {folder}",
        )

    def fetch_flags(self, uid: str, folder: str) -> list[str]:
        conn = self._select(folder)
        status, data = conn.fetch(uid, "(FLAGS)")
        if status != "OK" or not data or not data[0]:
            return []
        flags_raw = data[0]
        if isinstance(flags_raw, bytes):
            text = flags_raw.decode("utf-8", errors="replace")
        elif isinstance(flags_raw, tuple):
            text = (
                flags_raw[0].decode("utf-8", errors="replace") if flags_raw[0] else ""
            )
        else:
            text = str(flags_raw)
        flags: list[str] = []
        for token in text.split():
            if token.startswith("\\"):
                flags.append(token.rstrip(")"))
        return flags

    def append_message(self, folder: str, message_bytes: bytes) -> None:
        conn = self._get_conn()
        status, data = conn.append(
            f'"{folder}"',
            "(\\Seen)",
            message_bytes,
        )
        if status != "OK":
            raise ImapError(
                "APPEND_FAILED",
                f"Failed to append message to {folder!r}: {data}",
            )

    def find_sent_folder(self) -> str | None:
        SENT_PATTERNS = [
            "[Gmail]/Sent Mail",
            "Sent",
            "INBOX.Sent",
            "Sent Items",
            "INBOX.Sent Items",
        ]
        try:
            folders = self.list_folders()
        except ImapError:
            return None
        for pattern in SENT_PATTERNS:
            for folder in folders:
                if folder.lower() == pattern.lower():
                    return folder
        return None

    def logout(self) -> None:
        if self._conn is not None:
            try:
                self._conn.logout()
            except Exception:
                pass
            self._conn = None
