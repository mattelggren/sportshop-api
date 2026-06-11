# SportShop API — Claude Code Project Memory

## Project Overview

Minimal FastAPI e-commerce backend for sporting goods. Used as a learning sandbox
for claude-howto modules (slash commands, memory, skills, subagents, hooks, MCP, plugins).


## Guidance

@README.md for overall project guidance.


## Stack

- Python 3.13
- FastAPI + Pydantic v2
- SQLAlchemy 2.x with SQLite (test: in-memory via conftest.py)
- JWT auth via python-jose + passlib
- pytest + httpx for testing
- ruff for linting, bandit for security scanning, mypy for type checking


## Project Structure

```text title="SportShop API Directory Structure"
app/
  main.py           # FastAPI app, router registration, CORS
  core/
    database.py     # SQLAlchemy engine, session, get_db dependency
    security.py     # JWT creation/validation, password hashing, get_current_user
  models/
    user.py         # User, UserRole
    catalog.py      # Product, Order, Cart, Review, OrderStatus
  routers/
    auth.py         # POST /auth/register, /auth/login
    products.py     # CRUD /products/
    cart.py         # GET/POST/DELETE /cart/
    orders.py       # POST/GET/PATCH /orders/
    reviews.py      # POST/GET /reviews/{product_id}
  schemas/
    __init__.py     # All Pydantic request/response schemas
tests/
  conftest.py       # Fixtures: db, client, auth_headers, sample_product
  unit/             # Isolated endpoint tests
  integration/      # Multi-step flow tests (order lifecycle, defect coverage)
```

## Coding Standards

- All endpoints must have a `response_model` declared
- Auth-required endpoints use `Depends(get_current_user)`
- Admin-only writes check `current_user.role != UserRole.admin`
- No raw SQL; use SQLAlchemy ORM only
- Schemas live in `app/schemas/__init__.py`; do not scatter them into routers
- Ruff line length: 100 chars


## Known Intentional Defects (for QE learning exercises)

These defects are deliberate. Do not fix them unless explicitly instructed.

For the full defect checklist, see [skills/find-defects/references/defect-known-defects.md](skills/find-defects/references/known-defects.md)


## Test Strategy

- `tests/integration/test_orders.py` contains defect-documenting tests that
  are expected to FAIL until defects are fixed. This is intentional.
- Run `pytest --tb=short` to see current pass/fail state
- Run `bandit -c pyproject.toml -r app/` for security scan
- Run `ruff check app/` for linting


## Running Locally

```bash
python -m uvicorn app.main:app --reload
# API docs at http://localhost:8000/docs
```

## Claude Code Notes

- Use planning mode before any refactor that touches orders.py (state machine complexity)
- The secure-reviewer subagent should target app/core/security.py and app/routers/products.py first
- The test-engineer subagent should focus on the order cancellation state machine
  and the concurrent stock decrement scenario
