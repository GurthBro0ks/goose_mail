from __future__ import annotations


class ConfigError(Exception):
    """Base error for configuration issues."""

    def __init__(self, message: str, account_id: str | None = None) -> None:
        self.account_id = account_id
        super().__init__(message)


class MissingFieldError(ConfigError):
    """A required config field is missing."""


class InvalidProviderError(ConfigError):
    """An unsupported provider was specified."""


class ConfigFileError(ConfigError):
    """The config file could not be read or parsed."""
