from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ImapSettings:
    host: str
    port: int
    ssl: bool


@dataclass(frozen=True)
class SmtpSettings:
    host: str
    port: int
    ssl: bool
    starttls: bool


@dataclass(frozen=True)
class AuthRef:
    username_env: str
    password_env: str


@dataclass(frozen=True)
class AccountConfig:
    id: str
    provider: str
    email: str
    enabled: bool
    imap: ImapSettings
    smtp: SmtpSettings | None
    auth: AuthRef

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "provider": self.provider,
            "email": self.email,
            "enabled": self.enabled,
            "imap": {
                "host": self.imap.host,
                "port": self.imap.port,
                "ssl": self.imap.ssl,
            },
            "auth": {
                "username_env": self.auth.username_env,
                "password_env": self.auth.password_env,
            },
        }
        if self.smtp is not None:
            d["smtp"] = {
                "host": self.smtp.host,
                "port": self.smtp.port,
                "ssl": self.smtp.ssl,
                "starttls": self.smtp.starttls,
            }
        return d


@dataclass(frozen=True)
class MailConfig:
    accounts: list[AccountConfig]
