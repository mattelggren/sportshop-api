---
name: find-defects
description: Scan the codebase for known intentional defects listed in CLAUDE.md plus any additional security or correctness issues. Use when auditing the app for bugs or vulnerabilities.
context: fork
agent: Explore
allowed-tools: Bash(*)
disable-model-invocation: true
---

# /find-defects

Scan the codebase for the known intentional defects documented in CLAUDE.md,
plus any additional security or correctness issues.

## Current Test State

!`source .venv/bin/activate && python -m pytest --tb=no -q 2>&1 | tail -5`

## Instructions

1. Read the list of Known Intentional Defects referenced in CLAUDE.md
2. Locate each defect in the source code and confirm it is present
3. Scan for additional issues not in the known list
4. For each defect (known and new), provide:
   - File and line number
   - Defect description
   - Exploitability assessment (can this be triggered by an unauthenticated caller?)
   - Recommended fix
5. Summarize: how many defects found vs. how many were known

## Focus Areas (in priority order)
1. `app/core/security.py` — secrets, token handling
2. `app/routers/products.py` — auth guards
3. `app/routers/reviews.py` — input validation
4. `app/routers/orders.py` — concurrency, state machine
