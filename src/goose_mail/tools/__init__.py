from goose_mail.errors import ConfigError
from goose_mail.models import AccountConfig, MailConfig


def find_account(config: MailConfig, account_id: str) -> AccountConfig:
    for acct in config.accounts:
        if acct.id == account_id:
            return acct
    raise ConfigError(f"Account not found: {account_id!r}", account_id=account_id)
