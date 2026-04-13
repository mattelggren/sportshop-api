# SportShop API — Setup & Claude Code Integration Guide

## Step 1: Download the project

Download `sportshop-api.zip` from the Claude chat interface and unzip it:

```bash
cd ~/Projects          # or wherever you keep projects
unzip ~/Downloads/sportshop-api.zip
cd sportshop-api
```

---

## Step 2: Python environment

You need Python 3.11+. Check first:

```bash
python3 --version
```

If below 3.11, install via Homebrew:

```bash
brew install python@3.11
```

Create and activate a virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Verify the server starts:

```bash
uvicorn app.main:app --reload
# Visit http://localhost:8000/docs — you should see the Swagger UI
```

Run the tests:

```bash
pytest --tb=short
# Expect: most unit tests pass; two integration tests FAIL (intentional defects)
```

---

## Step 3: Git init

```bash
git init
git add .
git commit -m "feat: initial SportShop API scaffold"
```

---

## Step 4: Install Claude Code CLI

```bash
npm install -g @anthropic/claude-code
```

Verify:

```bash
claude --version
```

Authenticate (follow the browser prompt):

```bash
claude
```

---

## Step 5: Open project in Claude Code CLI

From the project root:

```bash
cd ~/Projects/sportshop-api
claude
```

Claude Code will auto-load `CLAUDE.md` as project memory. Confirm it loaded:

```
> What do you know about this project?
```

Claude should describe the SportShop API, the stack, the intentional defects,
and the coding standards — all from CLAUDE.md.

---

## Step 6: Wire the hooks

Claude Code hooks need to be registered in your settings file.
Open (or create) `~/.claude/settings.json` and add:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash /path/to/sportshop-api/.claude/hooks/pre-commit.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash /path/to/sportshop-api/.claude/hooks/security-scan.sh \"$FILE\""
          }
        ]
      }
    ]
  }
}
```

Replace `/path/to/sportshop-api` with your actual path (e.g., `/Users/elggren/Projects/sportshop-api`).

Make hook scripts executable:

```bash
chmod +x .claude/hooks/*.sh
```

---

## Step 7: VS Code integration

Install the Claude Code extension from the VS Code Marketplace:
- Search: **Claude Code** (published by Anthropic)
- Install and reload VS Code

Open the project:

```bash
code ~/Projects/sportshop-api
```

The extension shares the same `CLAUDE.md` and `.claude/` directory as the CLI.
You can invoke Claude Code from VS Code's command palette (`Cmd+Shift+P → Claude`)
or from the sidebar panel. Both the CLI and VS Code extension read from the same
`~/.claude/settings.json`, so hooks you wired in Step 6 apply in both contexts.

**VS Code-specific tip**: open the integrated terminal (`Ctrl+\``) and run
`claude` from there to get the full CLI experience alongside your editor panes.

---

## Step 8: Verify slash commands are available

In Claude Code (CLI or VS Code terminal):

```
> /review app/routers/products.py
```

You should get a structured security and correctness review of the products router,
including the intentional missing auth guard.

```
> /find-defects
```

This should enumerate all four documented defects plus any it finds independently.

```
> /generate-api-docs app/routers/orders.py
```

Should produce a clean markdown API reference for the orders module.

---

## Step 9: First learning exercise

Run the secure-reviewer subagent:

```
> Security audit the auth module and products router
```

Claude Code should delegate to the `secure-reviewer` agent defined in
`.claude/agents/secure-reviewer.md` and return a severity-ranked finding report.

Then run the test-engineer:

```
> Generate tests for the review rating boundary conditions
```

This targets the known defect (unconstrained rating values) and should produce
pytest cases covering 0, 1, 5, 6, -1, and 99 as inputs.

---

## Directory reference

```
sportshop-api/
├── app/                        # Application source
│   ├── main.py
│   ├── core/
│   │   ├── database.py
│   │   └── security.py         # ← Defect 1: hardcoded JWT secret
│   ├── models/
│   │   ├── user.py
│   │   └── catalog.py          # ← Defect 3: unconstrained rating column
│   ├── routers/
│   │   ├── auth.py
│   │   ├── products.py         # ← Defect 2: no auth on POST /products/
│   │   ├── cart.py
│   │   ├── orders.py           # ← Defect 4: non-atomic stock decrement
│   │   └── reviews.py          # ← Defect 3 (runtime): no rating range check
│   └── schemas/__init__.py
├── tests/
│   ├── conftest.py             # Fixtures
│   ├── unit/test_auth.py
│   └── integration/test_orders.py  # Defect-documenting tests (expect 2 failures)
├── .claude/
│   ├── commands/               # Slash commands
│   │   ├── review.md
│   │   ├── generate-api-docs.md
│   │   └── find-defects.md
│   ├── agents/                 # Subagent definitions
│   │   ├── secure-reviewer.md
│   │   └── test-engineer.md
│   └── hooks/                  # Hook scripts
│       ├── pre-commit.sh
│       └── security-scan.sh
├── CLAUDE.md                   # Project memory (auto-loaded by Claude Code)
├── pyproject.toml
├── requirements.txt
└── .gitignore
```
