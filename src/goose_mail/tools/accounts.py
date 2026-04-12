from goose_mail.config import load_config


def register(mcp, config_path: str, client_factory=None):
    @mcp.tool()
    def list_accounts() -> dict:
        cfg = load_config(config_path)
        accounts = [
            {
                "id": a.id,
                "provider": a.provider,
                "email": a.email,
                "enabled": a.enabled,
            }
            for a in cfg.accounts
            if a.enabled
        ]
        return {"accounts": accounts, "count": len(accounts)}
