# Inventory Low-Stock Alert System

## Context

SportShop tracked `Product.stock_qty` but had no mechanism to surface when an
item was running low. Stock is decremented when an order is placed and can be
edited by admins via `PUT /products/{id}`, but nothing reacted when it fell to
a dangerous level.

This document describes the design and implementation of an inventory alert that
fires when stock drops below a configurable threshold.

## Decision

**Notify mechanism**: log-only — emit a structured WARNING log entry plus a
metric. No new DB table, no new endpoint, no email integration.

**Threshold scope**: single global value (`LOW_STOCK_THRESHOLD`), configurable
via environment variable. Default: `5`.

**Re-alert policy**: every breach — alert fires on each stock-mutating event
that leaves `stock_qty` strictly below the threshold. No de-duplication or
suppression.

These choices keep the change side-effect-free and easy to test while modelling
a realistic ops concern.

## Architecture

```text
                   ┌─────────────────────────────┐
  place_order ─────┤ product.stock_qty -= qty     │
  (orders.py)      └──────────────┬──────────────┘
                                  │ calls
  update_product ──┐              ▼
  create_product   │   ┌──────────────────────────────────┐
  (products.py) ───┴──▶│ check_low_stock(product)          │
                       │  app/services/inventory.py        │
                       │   if stock_qty < threshold:        │
                       │     logger.warning("[ALERT] …")   │
                       │     metrics("inventory.            │
                       │              low_stock_alert", …) │
                       └──────────────┬────────────────────┘
                                      ▼
                   structured WARNING log + metric emit
```

The alert logic lives in **one service function** so every stock-mutating path
calls the same code. The `MetricsEmitter` callable is injected (DI) so
production code and tests can use different implementations without patching
module state.

## Files

### Created

| File | Purpose |
|---|---|
| `app/core/config.py` | `LOW_STOCK_THRESHOLD` constant, env-overridable |
| `app/services/__init__.py` | Services package marker |
| `app/services/inventory.py` | `check_low_stock()` — core alert logic |
| `tests/unit/test_inventory.py` | 8 unit tests covering boundary semantics and DI |
| `tests/integration/test_inventory_alerts.py` | 6 end-to-end tests via HTTP client |

### Modified

| File | Change |
|---|---|
| `app/routers/orders.py` | Call `check_low_stock(product)` after each stock decrement in `place_order` |
| `app/routers/products.py` | Call `check_low_stock(product)` after `create_product` and `update_product` |

## Implementation Details

### `app/core/config.py`

```python
import os
LOW_STOCK_THRESHOLD: int = int(os.getenv("SPORTSHOP_LOW_STOCK_THRESHOLD", "5"))
```

Tests monkeypatch `app.services.inventory._THRESHOLD` directly to avoid
`importlib` reload complexity.

### `app/services/inventory.py`

```python
def check_low_stock(
    product: Product,
    *,
    threshold: Optional[int] = None,           # falls back to _THRESHOLD
    metrics: MetricsEmitter = _default_metrics,
) -> bool:
```

- Returns `True` if an alert fired, `False` otherwise.
- Alert condition: `product.stock_qty < effective_threshold` (strict `<`).
- WARNING log includes: `product_id`, `sku`, `name`, `stock_qty`, `threshold`,
  UTC timestamp.
- Metric: `("inventory.low_stock_alert", 1, {"sku": …, "product_id": …, "threshold": …})`.
- `_default_metrics` is a log-backed no-op emitter; swap in a real sink when
  telemetry infra is available.

### `MetricsEmitter` protocol

```python
class MetricsEmitter(Protocol):
    def __call__(self, name: str, value: float, tags: dict[str, str]) -> None: ...
```

Tests inject `MagicMock()` to assert on call count and arguments.

## Alert Semantics

| `stock_qty` vs threshold | Alert fires? |
|---|---|
| `stock_qty < threshold` | Yes |
| `stock_qty == threshold` | No (strict `<`) |
| `stock_qty > threshold` | No |

Two consecutive orders both leaving stock below threshold each fire their own
alert (every-breach policy — no suppression).

## Configuration

Set `SPORTSHOP_LOW_STOCK_THRESHOLD` in the environment before starting:

```bash
SPORTSHOP_LOW_STOCK_THRESHOLD=10 python -m uvicorn app.main:app --reload
```

Default is `5` when the variable is absent.

## Testing

```bash
# Unit tests (boundary conditions, mock metrics, threshold injection)
pytest tests/unit/test_inventory.py -v

# Integration tests (HTTP-driven, caplog assertion)
pytest tests/integration/test_inventory_alerts.py -v

# Full suite (2 pre-existing intentional-defect failures are expected)
pytest --tb=short
```

### Integration test coverage

| Test | Scenario |
|---|---|
| `test_order_dropping_below_threshold_fires_alert` | Order takes qty from 4 → 2 (below 3) |
| `test_order_keeping_stock_at_or_above_threshold_no_alert` | Order leaves stock at 19 (above 3) |
| `test_every_breach_order_fires_separate_alert` | Two orders both breaching → two alerts |
| `test_admin_update_lowering_stock_below_threshold_fires_alert` | Admin PUT reduces stock to 1 |
| `test_admin_restock_above_threshold_no_alert` | Admin PUT restocks to 50 |
| `test_create_product_below_threshold_fires_alert` | Product created with `stock_qty=1` |

## Non-Goals

- No new DB table, model, or REST endpoint.
- No per-product threshold — a single global value was chosen.
- No alert de-duplication or suppression.
- No real email/Slack/webhook delivery.
- The two existing intentional defects (`create_product` missing auth guard,
  non-atomic stock decrement in `place_order`) are preserved unchanged.

---

## Appendix: Post-Implementation Notes

### Cart endpoint discovery

The integration test helper originally used `POST /cart/` to add items. This
returned `405 Method Not Allowed` because the actual endpoint is
`POST /cart/items` (see `app/routers/cart.py`). The helper was corrected before
the tests were considered complete. The plan did not reference the cart router,
so this was caught only when the integration tests ran for the first time.

**Takeaway**: when writing integration tests for an order flow, confirm the
cart add endpoint path from the router before writing the helper — `cart.py`
defines `POST /cart/items`, `DELETE /cart/items/{product_id}`, and `GET /cart/`.

### Ruff findings in new files

Three issues were introduced in the new files and fixed before merge:

| File | Rule | Issue |
|---|---|---|
| `tests/unit/test_inventory.py` | F401 | `import pytest` left over from scaffolding; no pytest decorators used |
| `tests/integration/test_inventory_alerts.py` | I001 | Local imports inside `admin_auth_headers` fixture were in wrong order |
| `tests/integration/test_inventory_alerts.py` | E501 | Two lines exceeded the 100-char limit (fixture body, test function signature) |

The rest of the codebase already had pre-existing ruff violations (I001 import
sort issues in `database.py`, `security.py`, `main.py`, `models/`, `schemas/`,
and existing test files). Those were not introduced by this change and were left
untouched per the project norm of not reformatting unrelated files.

### Test results (2026-06-17)

Full suite run after implementation (`pytest --tb=short`):

```
collected 24 items

tests/integration/test_inventory_alerts.py::test_order_dropping_below_threshold_fires_alert PASSED
tests/integration/test_inventory_alerts.py::test_order_keeping_stock_at_or_above_threshold_no_alert PASSED
tests/integration/test_inventory_alerts.py::test_every_breach_order_fires_separate_alert PASSED
tests/integration/test_inventory_alerts.py::test_admin_update_lowering_stock_below_threshold_fires_alert PASSED
tests/integration/test_inventory_alerts.py::test_admin_restock_above_threshold_no_alert PASSED
tests/integration/test_inventory_alerts.py::test_create_product_below_threshold_fires_alert PASSED
tests/integration/test_orders.py::test_place_order_success PASSED
tests/integration/test_orders.py::test_place_order_empty_cart PASSED
tests/integration/test_orders.py::test_cancel_order PASSED
tests/integration/test_orders.py::test_cancel_non_pending_order_fails PASSED
tests/integration/test_orders.py::test_review_rating_validation FAILED   ← intentional defect
tests/integration/test_orders.py::test_create_product_requires_auth FAILED  ← intentional defect
tests/unit/test_auth.py::test_register_success PASSED
tests/unit/test_auth.py::test_register_duplicate_email PASSED
tests/unit/test_auth.py::test_login_success PASSED
tests/unit/test_auth.py::test_login_wrong_password PASSED
tests/unit/test_inventory.py::test_check_low_stock_below_threshold_fires_alert PASSED
tests/unit/test_inventory.py::test_check_low_stock_at_threshold_does_not_alert PASSED
tests/unit/test_inventory.py::test_check_low_stock_above_threshold_does_not_alert PASSED
tests/unit/test_inventory.py::test_check_low_stock_calls_metrics_with_correct_args PASSED
tests/unit/test_inventory.py::test_check_low_stock_metric_not_called_above_threshold PASSED
tests/unit/test_inventory.py::test_check_low_stock_explicit_threshold_overrides_default PASSED
tests/unit/test_inventory.py::test_check_low_stock_uses_global_threshold_when_not_supplied PASSED
tests/unit/test_inventory.py::test_check_low_stock_global_threshold_no_alert_when_above PASSED

2 failed, 22 passed
```

The 2 failures (`test_review_rating_validation`, `test_create_product_requires_auth`) are
pre-existing intentional-defect tests in `tests/integration/test_orders.py` and were
failing before this feature was added. All 14 new tests pass.

### `_THRESHOLD` module-level mirror

`app/services/inventory.py` exposes a module-level `_THRESHOLD` variable
(initialised from `LOW_STOCK_THRESHOLD` at import time) specifically to make
monkeypatching straightforward in tests:

```python
monkeypatch.setattr("app.services.inventory._THRESHOLD", 3)
```

An alternative would be to re-read `config.LOW_STOCK_THRESHOLD` on every call,
which would allow `monkeypatch.setattr("app.core.config.LOW_STOCK_THRESHOLD", 3)`
instead. Either works; the chosen approach makes the service module's dependency
on config explicit and avoids repeated attribute lookups on the hot path.
