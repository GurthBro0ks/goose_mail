import pytest
import yaml

from goose_mail.config import (
    PROVIDER_PRESETS,
    _parse_account,
    load_config,
    validate_config,
)
from goose_mail.errors import (
    ConfigFileError,
    InvalidProviderError,
    MissingFieldError,
)
from goose_mail.models import MailConfig


def _write_yaml(tmp_path, data):
    p = tmp_path / "accounts.yaml"
    p.write_text(yaml.dump(data), encoding="utf-8")
    return str(p)


class TestProviderPresets:
    def test_all_providers_defined(self):
        for name in ("gmail", "outlook", "ionos", "generic"):
            assert name in PROVIDER_PRESETS

    def test_gmail_imap(self):
        imap = PROVIDER_PRESETS["gmail"]["imap"]
        assert imap["host"] == "imap.gmail.com"
        assert imap["port"] == 993
        assert imap["ssl"] is True

    def test_gmail_smtp(self):
        smtp = PROVIDER_PRESETS["gmail"]["smtp"]
        assert smtp["host"] == "smtp.gmail.com"
        assert smtp["port"] == 587

    def test_generic_has_no_preset(self):
        assert PROVIDER_PRESETS["generic"] == {}


class TestParseAccount:
    def test_gmail_account(self):
        raw = {
            "id": "test",
            "provider": "gmail",
            "email": "u@gmail.com",
            "auth": {"username_env": "U", "password_env": "P"},
        }
        acct = _parse_account(raw)
        assert acct.id == "test"
        assert acct.provider == "gmail"
        assert acct.imap.host == "imap.gmail.com"
        assert acct.imap.port == 993
        assert acct.smtp is not None
        assert acct.enabled is True

    def test_outlook_account(self):
        raw = {
            "id": "ol",
            "provider": "outlook",
            "email": "u@outlook.com",
            "auth": {"username_env": "OU", "password_env": "OP"},
        }
        acct = _parse_account(raw)
        assert acct.imap.host == "outlook.office365.com"
        assert acct.smtp is not None

    def test_ionos_account(self):
        raw = {
            "id": "ion",
            "provider": "ionos",
            "email": "u@ionos.com",
            "auth": {"username_env": "IU", "password_env": "IP"},
        }
        acct = _parse_account(raw)
        assert acct.imap.host == "imap.ionos.com"

    def test_generic_with_explicit_imap(self):
        raw = {
            "id": "gen",
            "provider": "generic",
            "email": "u@example.org",
            "imap": {"host": "imap.example.org", "port": 993, "ssl": True},
            "auth": {"username_env": "GU", "password_env": "GP"},
        }
        acct = _parse_account(raw)
        assert acct.imap.host == "imap.example.org"
        assert acct.smtp is None

    def test_generic_with_imap_and_smtp(self):
        raw = {
            "id": "gen2",
            "provider": "generic",
            "email": "u@example.org",
            "imap": {"host": "imap.example.org", "port": 993, "ssl": True},
            "smtp": {
                "host": "smtp.example.org",
                "port": 587,
                "ssl": False,
                "starttls": True,
            },
            "auth": {"username_env": "GU", "password_env": "GP"},
        }
        acct = _parse_account(raw)
        assert acct.smtp is not None
        assert acct.smtp.host == "smtp.example.org"

    def test_enabled_false(self):
        raw = {
            "id": "off",
            "provider": "gmail",
            "email": "u@gmail.com",
            "enabled": False,
            "auth": {"username_env": "U", "password_env": "P"},
        }
        acct = _parse_account(raw)
        assert acct.enabled is False

    def test_preset_override_port(self):
        raw = {
            "id": "custom-port",
            "provider": "gmail",
            "email": "u@gmail.com",
            "imap": {"host": "imap.gmail.com", "port": 143, "ssl": False},
            "auth": {"username_env": "U", "password_env": "P"},
        }
        acct = _parse_account(raw)
        assert acct.imap.port == 143
        assert acct.imap.ssl is False


class TestParseAccountErrors:
    def test_missing_id(self):
        with pytest.raises(MissingFieldError):
            _parse_account(
                {
                    "provider": "gmail",
                    "email": "u@g.com",
                    "auth": {"username_env": "U", "password_env": "P"},
                }
            )

    def test_missing_provider(self):
        with pytest.raises(MissingFieldError):
            _parse_account(
                {
                    "id": "x",
                    "email": "u@g.com",
                    "auth": {"username_env": "U", "password_env": "P"},
                }
            )

    def test_missing_email(self):
        with pytest.raises(MissingFieldError):
            _parse_account(
                {
                    "id": "x",
                    "provider": "gmail",
                    "auth": {"username_env": "U", "password_env": "P"},
                }
            )

    def test_missing_auth(self):
        with pytest.raises(MissingFieldError):
            _parse_account({"id": "x", "provider": "gmail", "email": "u@g.com"})

    def test_invalid_provider(self):
        with pytest.raises(InvalidProviderError):
            _parse_account(
                {
                    "id": "x",
                    "provider": "yaho",
                    "email": "u@g.com",
                    "auth": {"username_env": "U", "password_env": "P"},
                }
            )

    def test_missing_auth_username_env(self):
        with pytest.raises(MissingFieldError, match="username_env"):
            _parse_account(
                {
                    "id": "x",
                    "provider": "gmail",
                    "email": "u@g.com",
                    "auth": {"password_env": "P"},
                }
            )

    def test_missing_auth_password_env(self):
        with pytest.raises(MissingFieldError, match="password_env"):
            _parse_account(
                {
                    "id": "x",
                    "provider": "gmail",
                    "email": "u@g.com",
                    "auth": {"username_env": "U"},
                }
            )

    def test_generic_without_imap(self):
        with pytest.raises(MissingFieldError, match="IMAP"):
            _parse_account(
                {
                    "id": "x",
                    "provider": "generic",
                    "email": "u@g.com",
                    "auth": {"username_env": "U", "password_env": "P"},
                }
            )

    def test_error_has_no_secret_values(self):
        with pytest.raises(InvalidProviderError) as exc_info:
            _parse_account(
                {
                    "id": "x",
                    "provider": "badprovider",
                    "email": "u@g.com",
                    "auth": {
                        "username_env": "MY_SECRET_USER",
                        "password_env": "MY_SECRET_PASS",
                    },
                }
            )
        msg = str(exc_info.value)
        assert "MY_SECRET_USER" not in msg
        assert "MY_SECRET_PASS" not in msg


class TestLoadConfig:
    def test_load_valid(self, tmp_path):
        path = _write_yaml(
            tmp_path,
            {
                "accounts": [
                    {
                        "id": "g1",
                        "provider": "gmail",
                        "email": "u@gmail.com",
                        "auth": {"username_env": "GU", "password_env": "GP"},
                    },
                ],
            },
        )
        config = load_config(path)
        assert isinstance(config, MailConfig)
        assert len(config.accounts) == 1
        assert config.accounts[0].id == "g1"

    def test_load_multiple(self, tmp_path):
        path = _write_yaml(
            tmp_path,
            {
                "accounts": [
                    {
                        "id": "g1",
                        "provider": "gmail",
                        "email": "u1@gmail.com",
                        "auth": {"username_env": "U1", "password_env": "P1"},
                    },
                    {
                        "id": "o1",
                        "provider": "outlook",
                        "email": "u2@outlook.com",
                        "auth": {"username_env": "U2", "password_env": "P2"},
                    },
                ],
            },
        )
        config = load_config(path)
        assert len(config.accounts) == 2

    def test_file_not_found(self):
        with pytest.raises(ConfigFileError, match="Cannot read"):
            load_config("/nonexistent/path.yaml")

    def test_invalid_yaml(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text(": [invalid yaml {{", encoding="utf-8")
        with pytest.raises(ConfigFileError, match="Invalid YAML"):
            load_config(str(p))

    def test_missing_accounts_key(self, tmp_path):
        path = _write_yaml(tmp_path, {"stuff": []})
        with pytest.raises(ConfigFileError, match="accounts"):
            load_config(path)

    def test_accounts_not_list(self, tmp_path):
        path = _write_yaml(tmp_path, {"accounts": "nope"})
        with pytest.raises(ConfigFileError, match="list"):
            load_config(path)


class TestValidateConfig:
    def test_no_errors(self, tmp_path):
        path = _write_yaml(
            tmp_path,
            {
                "accounts": [
                    {
                        "id": "a",
                        "provider": "gmail",
                        "email": "u@gmail.com",
                        "auth": {"username_env": "U", "password_env": "P"},
                    },
                ],
            },
        )
        config = load_config(path)
        errors = validate_config(config)
        assert errors == []

    def test_duplicate_ids(self, tmp_path):
        path = _write_yaml(
            tmp_path,
            {
                "accounts": [
                    {
                        "id": "dup",
                        "provider": "gmail",
                        "email": "u1@gmail.com",
                        "auth": {"username_env": "U1", "password_env": "P1"},
                    },
                    {
                        "id": "dup",
                        "provider": "outlook",
                        "email": "u2@outlook.com",
                        "auth": {"username_env": "U2", "password_env": "P2"},
                    },
                ],
            },
        )
        config = load_config(path)
        errors = validate_config(config)
        assert len(errors) == 1
        assert "dup" in errors[0]


class TestAccountToDict:
    def test_roundtrip_gmail(self):
        raw = {
            "id": "g1",
            "provider": "gmail",
            "email": "u@gmail.com",
            "auth": {"username_env": "GU", "password_env": "GP"},
        }
        acct = _parse_account(raw)
        d = acct.to_dict()
        assert d["id"] == "g1"
        assert d["imap"]["host"] == "imap.gmail.com"
        assert d["smtp"]["host"] == "smtp.gmail.com"
        assert d["auth"]["username_env"] == "GU"

    def test_roundtrip_generic_no_smtp(self):
        raw = {
            "id": "gen",
            "provider": "generic",
            "email": "u@example.org",
            "imap": {"host": "imap.example.org", "port": 993, "ssl": True},
            "auth": {"username_env": "GU", "password_env": "GP"},
        }
        acct = _parse_account(raw)
        d = acct.to_dict()
        assert "smtp" not in d
