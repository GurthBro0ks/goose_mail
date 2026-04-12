from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from goose_mail.errors import ConfigFileError, InvalidProviderError, MissingFieldError
from goose_mail.models import (
    AccountConfig,
    AuthRef,
    ImapSettings,
    MailConfig,
    SmtpSettings,
)

PROVIDER_PRESETS: dict[str, dict[str, Any]] = {
    "gmail": {
        "imap": {"host": "imap.gmail.com", "port": 993, "ssl": True},
        "smtp": {"host": "smtp.gmail.com", "port": 587, "ssl": False, "starttls": True},
    },
    "outlook": {
        "imap": {"host": "outlook.office365.com", "port": 993, "ssl": True},
        "smtp": {
            "host": "smtp.office365.com",
            "port": 587,
            "ssl": False,
            "starttls": True,
        },
    },
    "ionos": {
        "imap": {"host": "imap.ionos.com", "port": 993, "ssl": True},
        "smtp": {"host": "smtp.ionos.com", "port": 587, "ssl": False, "starttls": True},
    },
    "generic": {},
}

REQUIRED_ACCOUNT_FIELDS = {"id", "provider", "email", "auth"}


def _merge_preset(provider: str, raw: dict[str, Any]) -> dict[str, Any]:
    preset = PROVIDER_PRESETS.get(provider)
    if preset is None:
        raise InvalidProviderError(
            f"Unknown provider: {provider!r}", account_id=raw.get("id")
        )
    merged: dict[str, Any] = {**preset, **raw}
    if "imap" not in merged:
        raise MissingFieldError(
            "IMAP settings required for generic provider", account_id=raw.get("id")
        )
    if "imap" in preset and "imap" in raw:
        merged["imap"] = {**preset["imap"], **raw["imap"]}
    if "smtp" in preset and "smtp" in raw:
        merged["smtp"] = {**preset["smtp"], **raw["smtp"]}
    return merged


def _parse_imap(raw: dict[str, Any]) -> ImapSettings:
    return ImapSettings(
        host=raw["host"],
        port=int(raw["port"]),
        ssl=bool(raw.get("ssl", True)),
    )


def _parse_smtp(raw: dict[str, Any]) -> SmtpSettings:
    return SmtpSettings(
        host=raw["host"],
        port=int(raw["port"]),
        ssl=bool(raw.get("ssl", False)),
        starttls=bool(raw.get("starttls", True)),
    )


def _parse_auth(raw: dict[str, Any]) -> AuthRef:
    if "username_env" not in raw:
        raise MissingFieldError("auth.username_env is required")
    if "password_env" not in raw:
        raise MissingFieldError("auth.password_env is required")
    return AuthRef(username_env=raw["username_env"], password_env=raw["password_env"])


def _parse_account(raw: dict[str, Any]) -> AccountConfig:
    missing = REQUIRED_ACCOUNT_FIELDS - set(raw.keys())
    if missing:
        field = sorted(missing)[0]
        raise MissingFieldError(
            f"Required field missing: {field}", account_id=raw.get("id")
        )

    provider = raw["provider"]
    if provider not in PROVIDER_PRESETS:
        raise InvalidProviderError(
            f"Unknown provider: {provider!r}", account_id=raw.get("id")
        )

    merged = _merge_preset(provider, raw)

    imap = _parse_imap(merged["imap"])
    smtp = _parse_smtp(merged["smtp"]) if "smtp" in merged else None
    auth = _parse_auth(raw["auth"])

    return AccountConfig(
        id=raw["id"],
        provider=provider,
        email=raw["email"],
        enabled=bool(raw.get("enabled", True)),
        imap=imap,
        smtp=smtp,
        auth=auth,
    )


def load_config(path: str | Path) -> MailConfig:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigFileError(f"Cannot read config file: {exc}") from exc

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigFileError(f"Invalid YAML in config file: {exc}") from exc

    if not isinstance(data, dict) or "accounts" not in data:
        raise ConfigFileError("Config file must contain an 'accounts' list")

    accounts_raw = data["accounts"]
    if not isinstance(accounts_raw, list):
        raise ConfigFileError("'accounts' must be a list")

    accounts: list[AccountConfig] = []
    for raw in accounts_raw:
        accounts.append(_parse_account(raw))

    return MailConfig(accounts=accounts)


def validate_config(config: MailConfig) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for account in config.accounts:
        if account.id in seen_ids:
            errors.append(f"Duplicate account id: {account.id}")
        seen_ids.add(account.id)
    return errors
