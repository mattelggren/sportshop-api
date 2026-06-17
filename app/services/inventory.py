"""
Inventory alert service.

Centralises low-stock detection so every stock-mutating path (place_order,
create_product, update_product) calls the same logic rather than duplicating it.

Alert policy (by design decision):
- Fire on EVERY event that leaves stock_qty strictly below threshold.
- No de-duplication or suppression — each breach is an independent alert.

Metrics emission is injected via the `metrics` parameter so callers (including
tests) can substitute a mock without touching module state.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Protocol, runtime_checkable

from app.core.config import LOW_STOCK_THRESHOLD
from app.models.catalog import Product

logger = logging.getLogger("sportshop.inventory")

# Module-level threshold mirror; monkeypatch this in tests to override the global.
_THRESHOLD: int = LOW_STOCK_THRESHOLD


@runtime_checkable
class MetricsEmitter(Protocol):
    """Callable signature for emitting a single named metric with tags."""

    def __call__(self, name: str, value: float, tags: dict[str, str]) -> None: ...


def _default_metrics(name: str, value: float, tags: dict[str, str]) -> None:
    """Log-backed metrics emitter used in production (no real telemetry sink wired)."""
    logger.info(
        "[METRIC] name=%s value=%s tags=%s ts=%s",
        name,
        value,
        tags,
        datetime.now(timezone.utc).isoformat(),
    )


def check_low_stock(
    product: Product,
    *,
    threshold: Optional[int] = None,
    metrics: MetricsEmitter = _default_metrics,
) -> bool:
    """Check whether a product's current stock is below the alert threshold.

    Fires a WARNING log entry and a metric when stock_qty < threshold.
    Returns True if an alert fired, False otherwise.

    Args:
        product:   The Product instance to inspect (stock_qty must be current).
        threshold: Override the global LOW_STOCK_THRESHOLD for this call.
        metrics:   Callable matching MetricsEmitter; defaults to the log-backed emitter.
    """
    effective_threshold = threshold if threshold is not None else _THRESHOLD

    if product.stock_qty >= effective_threshold:
        return False

    ts = datetime.now(timezone.utc).isoformat()
    logger.warning(
        "[ALERT] low stock detected — product_id=%s sku=%s name=%r "
        "stock_qty=%s threshold=%s ts=%s",
        product.id,
        product.sku,
        product.name,
        product.stock_qty,
        effective_threshold,
        ts,
    )
    metrics(
        "inventory.low_stock_alert",
        1,
        {
            "sku": product.sku,
            "product_id": str(product.id),
            "threshold": str(effective_threshold),
        },
    )
    return True
