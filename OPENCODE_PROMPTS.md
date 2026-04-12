### OPENCODE PASTE PROMPT — goose_mail AUTO-WORK
### Copy everything between the dashes and paste into opencode

# -----------------------------------------------------------------------
cat AGENTS.md
cat agent-progress.md
python3 -c "
import json,sys
d=json.load(open('feature_list.json'))
inc=[f for f in d['features'] if not f['passes']]
for f in sorted(inc, key=lambda x:{'critical':0,'high':1,'medium':2,'low':3}.get(x['priority'],9)):
    print(f'[{f[\"priority\"].upper():8}] {f[\"id\"]}: {f[\"description\"]}')
print(f'\n{len(inc)} features remaining.')
"
git log --oneline -10
source init.sh

IMPORTANT TARGET:
This repo is a local MCP server extension for Goose.
Do NOT target old goose-ai plugin APIs, Python entry_points plugin discovery,
or vague "plugin registration" patterns.
Build for Goose custom extension use over STDIO.

Pick the first CRITICAL incomplete feature from feature_list.json.
Work on that ONE feature only. Follow all rules in AGENTS.md.

Required behavior:
- Keep diffs small
- Prefer src/ package layout
- Use mocks/fixtures instead of real mail access
- Never print secrets
- Do not mark a feature done without truth-gate proof

When done:
1. Run the truth gate: ruff check . && pytest
2. Update feature_list.json — set "passes": true ONLY for features you verified
3. Prepend a new entry to agent-progress.md with: date, what you did, what's next, git state
4. git add -A && git commit -m "<type>: <description>"

No questions. Execute autonomously. Go.
# -----------------------------------------------------------------------


### FIX MODE — paste this when something is broken

# -----------------------------------------------------------------------
cat AGENTS.md
cat agent-progress.md
source init.sh

Something is broken. Do NOT random-patch.

PHASE 1 — OBSERVE: run truth gate, record exact failure. Check git log -10.
PHASE 2 — HYPOTHESIZE: one specific falsifiable root cause.
PHASE 3 — TEST: design minimal test to disprove it. Run it.
PHASE 4 — FIX: smallest diff for confirmed root cause only.
PHASE 5 — PROVE: truth gate must pass. Original failure must be gone.
If 3 attempts fail: document as UNRESOLVED in agent-progress.md. Stop.

When done:
1. Prepend entry to agent-progress.md: ROOT CAUSE + WHAT WAS FIXED + WHAT VERIFIED
2. Update feature_list.json if status changed
3. git add -A && git commit -m "fix: <what>"

No questions. Go.
# -----------------------------------------------------------------------


### DIRECTED TASK — fill in [TASK] and paste

# -----------------------------------------------------------------------
cat AGENTS.md
cat agent-progress.md
source init.sh

YOUR TASK: [TASK]

Follow AGENTS.md rules. When done:
1. ruff check . && pytest
2. Update agent-progress.md
3. Update feature_list.json if relevant
4. git add -A && git commit -m "<type>: <description>"

No questions. Go.
# -----------------------------------------------------------------------
