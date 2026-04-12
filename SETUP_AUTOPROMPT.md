Paste this into opencode after you place the harness files into your fresh repo.

# -----------------------------------------------------------------------
cat AGENTS.md
cat agent-progress.md
python3 -c "
import json,sys
d=json.load(open('feature_list.json'))
for f in d['features']:
    print(f'{f["id"]}: passes={f["passes"]} priority={f["priority"]} :: {f["description"]}')
"
source init.sh

You are setting up the initial project foundation for goose_mail on a fresh Linux Mint laptop repo.

Important target:
- This project is a local MCP server for Goose Desktop over STDIO
- Do NOT target old goose-ai plugin APIs
- Do NOT implement real mail logic yet
- Do NOT ask questions

Your task is ONLY to complete gm-001.

Definition of done for gm-001:
- Add pyproject.toml
- Create src/goose_mail/__init__.py
- Create src/goose_mail/__main__.py
- Use a src/ layout
- Project installs with uv or pip in editable mode
- `python -c "import goose_mail; print(goose_mail.__version__)"` works
- Truth gate passes: `ruff check . && pytest`
- Update feature_list.json only for verified items
- Prepend a new session entry to agent-progress.md
- Commit changes with a clear commit message

Constraints:
- Keep the project minimal
- Add only the smallest smoke test needed so pytest passes if required by gm-001
- Do not start gm-002 or later intentionally, except for the minimal config needed to make gm-001 verifiable
- No secrets, no live credentials, no real network auth

When done, print:
1. files created
2. install command used
3. verification commands used
4. final commit hash
# -----------------------------------------------------------------------
