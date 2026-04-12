# Agent Progress Log — goose_mail

> Append-only. Every session adds an entry at the TOP. Never edit old entries.

---

## Session: 2026-04-12 — Real IMAP runtime integration (gm-009)

**Agent:** opencode (glm-5.1)
**What changed:**
- Created `src/goose_mail/mail/real_imap_client.py` — `RealImapClient` using `imaplib`, connects to real IMAP servers via config presets, reads credentials from env vars, structured error codes (AUTH_MISSING, AUTH_FAILED, CONNECTION_FAILED, BAD_FOLDER, LIST_FAILED, SEARCH_FAILED, MESSAGE_NOT_FOUND)
- Updated `src/goose_mail/tools/folders.py` — defaults to `RealImapClient` when no `client_factory` provided, returns structured `{ok, account_id, folders, count}` or `{ok: false, error: {code, message}}`
- Updated `src/goose_mail/tools/search.py` — defaults to `RealImapClient`, returns structured `{ok, results, count}` or error
- Updated `src/goose_mail/tools/read.py` — defaults to `RealImapClient`, returns full normalized message with `ok: true` or error
- Updated `tests/test_mail_tools.py` — adjusted `test_normalized_shape` for new `ok` field in read_message output
- All existing tests still use `FakeImapClient` via `client_factory` — no live network in tests
- SMTP send path untouched and still working

**What now uses real IMAP:**
- `list_folders` — real `imaplib.IMAP4_SSL` connection, LIST command
- `search_mail` — real SEARCH (OR SUBJECT/FROM), FETCH RFC822 + FLAGS
- `read_message` — real FETCH RFC822 + FLAGS, MIME parsing via existing `mime_parser.py`

**What is still mocked in tests:**
- All 92 tests pass with `FakeImapClient` via `client_factory=lambda _a: FakeImapClient()`
- No live network calls in test suite

**Manual smoke steps:**
1. Create `config/accounts.yaml` from `config/accounts.example.yaml`
2. Set env vars for your account (e.g. `export GMAIL_USER=you@gmail.com GMAIL_PASS=app-password`)
3. Start server: `python -m goose_mail`
4. Via Goose Desktop: try `list_folders`, `search_mail`, `read_message`
5. Expected: real folder list, real search results, real message content

**Truth gate:** `ruff check .` → All checks passed; `pytest -v` → 92 passed
**Environment state:** .venv active, project installed editable, lint + tests green
**Git state:** Clean before this session

---

## Session: 2026-04-12 — Diagnostic: Goose Desktop not loading extension

**Agent:** opencode (glm-5.1)
**Confirmed root cause:**
1. The Goose config entry was structurally correct (cmd/args properly split, type: stdio, enabled: true)
2. However, the earlier gooded session (10:48 AM) loaded goosemail lazily and it crashed within 0.5s: `Failed to list tools extension=goosemail error=Transport closed`
3. The subsequent session (11:16 AM) never attempted to load goosemail — Goose Desktop cached the failure
4. The MCP server itself was healthy all along (verified by manual MCP handshake: initialize + tools/list returns all 6 tools)
5. The only structural difference between goosemail and other working STDIO extensions was an empty `description: ''`
**Fix applied:**
- Added a proper `description` to the goosemail entry in `~/.config/goose/config.yaml`
- Updated `goose-mail-extension.json` sample config to match Goose Desktop's actual config format
**Action required by user:** Restart Goose Desktop to clear the cached failure and force a fresh extension load. The server is confirmed healthy via manual MCP handshake.
**Repo changes:** `goose-mail-extension.json` updated to match Goose Desktop config format
**Environment state:** .venv active, lint + tests green
**Git state:** Clean before this session

---

## Session: 2026-04-12 — gm-008 complete

**Agent:** opencode (glm-5.1)
**What was done:**
- Created `src/goose_mail/mail/smtp_client.py` — SmtpClient protocol, FakeSmtpClient (records sends), build_message helper
- Created `src/goose_mail/tools/send.py` — send_mail tool with input validation, SMTP config check, structured success/error results
- Updated `server.py` — added smtp_factory parameter, registers send_mail tool
- Created `tests/test_send_mail.py` — 17 tests covering:
  - build_message: plain text, CC, no CC header, HTML alternative, multiple recipients
  - FakeSmtpClient: send recording, multiple sends
  - send_mail tool: success, CC/BCC, HTML, SMTP not configured, empty to, empty subject, unknown account, no secrets in output, success/error shapes
- All errors structured with code + message; no secrets leaked
- No attachment support in this pass (as specified)
- Truth gate: `ruff check .` → All checks passed; `pytest -v` → 92 passed
- Updated `feature_list.json`: gm-008 passes=true
**All 8 features now complete.**
**Manual verification for live SMTP:**
1. Create `config/accounts.yaml` from `config/accounts.example.yaml`
2. Set env vars for your account credentials
3. Run `python -m goose_mail` and use send_mail via Goose Desktop
**Environment state:** .venv active, project installed editable, lint + tests green
**Git state:** Clean before this session

---

## Session: 2026-04-12 — gm-007 complete

**Agent:** opencode (glm-5.1)
**What was done:**
- Created `src/goose_mail/mail/` package with:
  - `__init__.py`
  - `imap_client.py` — ImapClient protocol + FakeImapClient with fixture data (2 emails: simple text + multipart with attachment)
  - `mime_parser.py` — parse_message, html_to_text, parse_addresses, parse_flags, attachment extraction
- Created `src/goose_mail/tools/` package with:
  - `__init__.py` — find_account helper
  - `accounts.py` — list_accounts tool (returns enabled accounts, no secrets)
  - `folders.py` — list_folders tool
  - `search.py` — search_mail tool (compact results, no body/attachments)
  - `read.py` — read_message tool (full normalized output per spec)
- Updated `server.py` — create_server accepts config_path + client_factory, registers all 5 tools
- Created `tests/test_mime_parser.py` — 16 tests for address parsing, HTML-to-text, flags, message parsing
- Created `tests/test_mail_tools.py` — 16 tests for all 4 mail tools + error cases
- All tools return structured dicts (accounts/folders/search wrapped in envelope dicts)
- MIME parser: plain-text preference, HTML-to-text fallback, attachment metadata only
- No secrets leak in any output; env var names excluded from list_accounts
- Truth gate: `ruff check .` → All checks passed; `pytest -v` → 75 passed
- Updated `feature_list.json`: gm-007 passes=true
**What needs to happen next:**
- gm-008: SMTP send_mail with structured results and safe logging
**Environment state:** .venv active, project installed editable, lint + tests green
**Git state:** Clean before this session

---

## Session: 2026-04-12 — gm-006 complete

**Agent:** opencode (glm-5.1)
**What was done:**
- Created `src/goose_mail/errors.py` — structured error hierarchy (ConfigError, MissingFieldError, InvalidProviderError, ConfigFileError)
- Created `src/goose_mail/models.py` — frozen dataclasses for ImapSettings, SmtpSettings, AuthRef, AccountConfig, MailConfig with to_dict()
- Created `src/goose_mail/config.py` — provider presets (gmail, outlook, ionos, generic), YAML config loading, account parsing, validation
- Added `pyyaml>=6.0` dependency to pyproject.toml
- Created `config/accounts.example.yaml` with examples for all 4 providers
- Created `tests/test_config.py` with 30 tests covering presets, parsing, errors, file loading, validation, serialization
- Truth gate: `ruff check .` → All checks passed; `pytest -v` → 37 passed
- Secrets referenced only by env var names; no secret values in exceptions or logs
- Updated `feature_list.json`: gm-006 passes=true
**What needs to happen next:**
- gm-007: Read-only mail tools (list_accounts, list_folders, search_mail, read_message)
**Environment state:** .venv active, project installed editable, lint + tests green
**Git state:** Clean before this session

---

## Session: 2026-04-12 — gm-005 complete

**Agent:** opencode (glm-5.1)
**What was done:**
- Created `goose-mail-extension.json` sample config with STDIO extension definition
- Rewrote `README.md` with install, run, and Goose Desktop setup instructions
- Documented both config-file and manual-entry approaches for Goose Desktop
- Goose Desktop command: `/home/mint/projects/goose_mail/.venv/bin/python -m goose_mail`
- Truth gate: `ruff check .` → All checks passed; `pytest -v` → 7 passed
- Updated `feature_list.json`: gm-005 passes=true
**What needs to happen next:**
- gm-006: Read-only IMAP configuration layer
**Manual verification procedure for Goose Desktop:**
1. Open Goose Desktop → Settings → Extensions → Add Custom Extension (STDIO)
2. Command: `/home/mint/projects/goose_mail/.venv/bin/python`
3. Args: `-m goose_mail`
4. Save, then ask Goose: "Use the ping tool from goose-mail"
5. Expected: `{"ok": true, "service": "goose_mail", "version": "0.1.0"}`
6. Alternatively: `cp goose-mail-extension.json ~/.config/goose/extensions.d/`
**Environment state:** .venv active, project installed editable, lint + tests green
**Git state:** Clean before this session

---

## Session: 2026-04-12 — gm-004 complete

**Agent:** opencode (glm-5.1)
**What was done:**
- Added `mcp>=1.0` as a runtime dependency in `pyproject.toml`
- Created `src/goose_mail/server.py` with FastMCP server and `ping` tool returning `{"ok": true, "service": "goose_mail", "version": "0.1.0"}`
- Updated `src/goose_mail/__main__.py` to call `server.run()` (STDIO transport)
- Added 4 new tests: server module import, server create, ping tool registered, ping tool handler
- All 7 tests pass (2 async via pytest-anyio)
- Truth gate: `ruff check .` → All checks passed; `pytest -v` → 7 passed
- Local smoke check: `python -m goose_mail` starts without crash (exits 0 via timeout in test)
- Updated `feature_list.json`: gm-004 passes=true
**What needs to happen next:**
- gm-005: Goose Desktop can load the extension as a STDIO custom extension
**Manual verification note:**
- Full STDIO handshake test is deferred; `python -m goose_mail` boots without immediate crash
- A live MCP handshake with `mcp` client library or Goose Desktop is the next integration step
**Environment state:** .venv active, project installed editable, lint + tests green
**Git state:** Clean before this session

---

## Session: 2026-04-12 — gm-003 complete

**Agent:** opencode (glm-5.1)
**What was done:**
- Verified pytest config in `pyproject.toml` (`testpaths = ["tests"]`)
- Added `test_main_entrypoint` smoke test verifying `python -m goose_mail` works
- Now 3 intentional smoke tests: version, import, main entrypoint behavior
- Ran truth gate: `ruff check .` → All checks passed; `pytest -v` → 3 passed
- Updated `feature_list.json`: gm-003 passes=true
**What needs to happen next:**
- gm-004: MCP server boots locally with one stub tool over STDIO
**Environment state:** .venv active, project installed editable, lint + tests green
**Git state:** Clean before this session

---

## Session: 2026-04-12 — gm-002 complete

**Agent:** opencode (glm-5.1)
**What was done:**
- Verified ruff config already present in `pyproject.toml` (target-version, line-length, lint select rules)
- Confirmed ruff is listed as a dev dependency and installed
- Ran truth gate: `ruff check .` → All checks passed; `pytest -v` → 2 passed
- Updated `feature_list.json`: gm-002 passes=true
- No code changes required — lint was already green from gm-001 bootstrap
**What needs to happen next:**
- gm-003 (pytest smoke) is already satisfied by existing tests
- Next real work: gm-004 (MCP server boots with one stub tool)
**Environment state:** .venv active, project installed editable, lint + tests green
**Git state:** Clean before this session

---

## Session: 2026-04-12 — gm-001 complete

**Agent:** opencode (glm-5.1)
**What was done:**
- Created `pyproject.toml` with setuptools build, src layout, ruff + pytest dev deps
- Created `src/goose_mail/__init__.py` with `__version__ = "0.1.0"`
- Created `src/goose_mail/__main__.py` with stub entrypoint
- Created `tests/test_smoke.py` with 2 passing tests (version + import)
- Installed with `uv pip install -e ".[dev]"` — all 7 packages resolved
- Truth gate: `ruff check .` → All checks passed; `pytest -v` → 2 passed
- Updated `feature_list.json`: gm-001 passes=true
**What needs to happen next:**
- gm-002 (ruff config) and gm-003 (pytest smoke) are effectively already satisfied
- Next real work: gm-004 (MCP server boots with one stub tool)
**Environment state:** .venv active, project installed editable, lint + tests green
**Git state:** Working tree dirty with gm-001 artifacts

---

## Session: 2026-04-12 (Harness retargeted to MCP/STDIO)

**Agent:** Human (pre-start harness correction)
**What was done:**
- Retargeted project from generic Goose plugin wording to Goose MCP server over STDIO
- Replaced feature roadmap so bootstrap, MCP stub, Goose integration, IMAP read-only, and SMTP send happen in the right order
- Kept init.sh as-is for bootstrap

**What needs to happen next:**
- First agent session: tackle gm-001 only
- Then gm-002 and gm-003
- Do not attempt live Goose integration until gm-004 exists

**Environment state:** Fresh repo, no real project code yet
**Git state:** Harness corrected before first autonomous build

---

## Session: 2026-04-12 (Harness initialization)

**Agent:** Human (harness setup)
**What was done:**
- Created AGENTS.md, feature_list.json, agent-progress.md, init.sh
- 5 initial features scaffolded (all passes: false)
- Project is a Goose (Block) plugin — Python

**What needs to happen next:**
- First agent session: tackle gm-001 (pyproject.toml + src layout)
- Clarify which Goose plugin API to target (goose-ai pip package vs block/goose)
- Run init.sh and confirm Python environment works on Mint laptop

**Environment state:** Fresh repo, no .venv yet
**Git state:** Harness files uncommitted

---
