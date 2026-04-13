# /review

Perform a structured code review of the specified file or module.

## Instructions

1. Read the target file(s) thoroughly
2. Check against the standards in CLAUDE.md
3. Report findings in these categories:

### Security
- Auth guards present on all write endpoints?
- No hardcoded secrets?
- Input validation complete?

### Correctness
- Edge cases handled (empty collections, not-found, wrong ownership)?
- State transitions guarded correctly?

### Test Coverage
- Does a test exist for the happy path?
- Does a test exist for the primary failure path?
- Are intentional defects documented by failing tests?

### Code Style
- Ruff-compliant (run `ruff check` mentally)?
- Response models declared on all endpoints?

## Output Format
For each finding: **[SEVERITY]** `file:line` — description and recommended fix.
Severity levels: CRITICAL / HIGH / MEDIUM / LOW / INFO
