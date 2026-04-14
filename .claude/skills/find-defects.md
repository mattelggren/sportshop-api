# /find-defects

Scan the codebase for the known intentional defects documented in CLAUDE.md,
plus any additional security or correctness issues.

## Instructions

1. Read CLAUDE.md to load the known defect list
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
