# goose_mail — Agent Operating Manual

You are an autonomous coding agent working on goose_mail, a local MCP server
extension for Goose (by Block). This file is your operating manual.

## Startup Sequence (EVERY session — no skipping)

1. `cat agent-progress.md`
2. `cat feature_list.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
inc=[f for f in d['features'] if not f['passes']]
for f in sorted(inc, key=lambda x:{'critical':0,'high':1,'medium':2,'low':3}.get(x['priority'],9)):
    print(f'[{f[\"priority\"].upper():8}] {f[\"id\"]}: {f[\"description\"]}')
"`
3. `git log --oneline -10`
4. `source init.sh`
5. Pick the first CRITICAL incomplete feature
6. Only THEN begin coding

## Repo Structure (initial — update as project grows)

```text
goose_mail/
├── AGENTS.md
├── agent-progress.md
├── feature_list.json
├── init.sh
├── README.md
├── pyproject.toml
├── src/
│   └── goose_mail/
│       ├── __init__.py
│       ├── __main__.py
│       ├── server.py
│       ├── config.py
│       ├── models.py
│       ├── errors.py
│       └── tools/
└── tests/
    └── test_*.py
```

## Tech Stack

- Language: Python 3.x
- Protocol/framework: MCP server for Goose
- Integration target: Goose Desktop custom extension via STDIO
- Package manager: uv or pip (prefer uv if available)
- Test runner: pytest
- Linting: ruff

## Truth Gate

A feature is only "done" when:
1. `ruff check .` passes with zero errors
2. `pytest` passes
3. The feature works end-to-end for its scope
4. For MCP milestones, manual verification is recorded when required

## Forbidden Zones (DO NOT TOUCH)

- `.env*` files — never read or write secrets
- Real credentials, tokens, passwords, app passwords
- `__pycache__/`, `.venv/` — never modify directly

## Work Rules

- ONE feature per session
- Keep diffs small and surgical
- Do not target old `goose-ai` plugin interfaces or Python entry-point plugin discovery
- This repo targets a local MCP server exposed over STDIO
- Read-only mail features come before send features
- Never mark a feature as passes=true without running the truth gate
- If a feature depends on live credentials, implement with mocks/tests first and document the manual step separately

## End-of-Session Checklist

1. Truth gate passes (`ruff check .` + `pytest`)
2. `feature_list.json` updated only for verified features
3. `agent-progress.md` updated at the top
4. `git add -A && git commit -m "<type>: <description>"`
5. Leave the repo in a state where `source init.sh` still works

## Risk Levels

| Level | When | What's Required |
|-------|------|----------------|
| low | Small isolated repo/bootstrap change | Truth gate + smoke test |
| medium | MCP wiring or mail parsing | Truth gate + edge cases |
| high | Auth flow, SMTP send, destructive mail actions | Truth gate + regression + manual verify |
