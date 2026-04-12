# goose_mail

Local MCP server extension for [Goose](https://github.com/block/goose) — mail tools over STDIO.

## Install

```bash
cd ~/projects/goose_mail
python3 -m venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Or without uv:

```bash
pip install -e ".[dev]"
```

## Run locally

```bash
python -m goose_mail
```

This starts the MCP server on STDIO. It will listen for JSON-RPC messages and respond to tool calls.

## Goose Desktop setup

### Option A: via config file

Copy or symlink the sample config to your Goose configuration directory:

```bash
cp goose-mail-extension.json ~/.config/goose/extensions.d/goose-mail-extension.json
```

### Option B: manual entry in Goose Desktop

1. Open Goose Desktop settings
2. Go to **Extensions** (or "Add Extension")
3. Choose **Custom Extension / STDIO**
4. Enter:

| Field | Value |
|-------|-------|
| **Name** | `goose-mail` |
| **Type** | `stdio` |
| **Command** | `/home/mint/projects/goose_mail/.venv/bin/python` |
| **Args** | `-m goose_mail` |

5. Save and restart Goose if needed.

### Verify

After setup, the `ping` tool should appear in Goose's available tools. Ask Goose:

> "Use the ping tool from goose-mail"

Expected response: `{"ok": true, "service": "goose_mail", "version": "0.1.0"}`

## Development

```bash
ruff check .        # lint
pytest -v           # tests
ruff format .       # format
```

## Current tools

| Tool | Description |
|------|-------------|
| `ping` | Health check — returns service name and version |
| `list_accounts` | List enabled mail accounts |
| `list_folders` | List IMAP folders for an account (real IMAP) |
| `search_mail` | Search messages by subject/from (real IMAP) |
| `read_message` | Read a full message with normalized output (real IMAP) |
| `send_mail` | Send email via SMTP |

## Manual IMAP smoke test

1. Copy `config/accounts.example.yaml` to `config/accounts.yaml` and fill in your account details.
2. Export credentials:
   ```bash
   export GMAIL_USER=you@gmail.com
   export GMAIL_PASS=your-app-password
   ```
3. Start the server and test via Goose Desktop:
   - `list_folders(account_id="your-account-id")` → should return real folder names
   - `search_mail(account_id="your-account-id", query="test")` → real search results
   - `read_message(account_id="your-account-id", message_id="<uid>")` → real message
