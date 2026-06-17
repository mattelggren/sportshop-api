"""
Unit tests for app.services.inventory.check_low_stock.

Tests cover:
- Below-threshold → alert fires (log WARNING + metric called once)
- At-threshold (== threshold) → no alert (strict < semantics)
- Above-threshold → no alert
- Explicit threshold= kwarg overrides the global default
- Metric call receives the expected positional args and SKU tag
"""
import logging
from unittest.mock import MagicMock

from app.models.catalog import Product
from app.services.inventory import check_low_stock


def _make_product(stock_qty: int, sku: str = "TEST-SKU-001", name: str = "Test Product") -> Product:
    """Build an in-memory Product without touching the DB."""
    p = Product()
    p.id = 1
    p.name = name
    p.sku = sku
    p.stock_qty = stock_qty
    p.price = 9.99
    p.category = "test"
    return p


# ---------------------------------------------------------------------------
# Core boundary tests
# ---------------------------------------------------------------------------

def test_check_low_stock_below_threshold_fires_alert(caplog):
    """stock_qty < threshold → True returned, WARNING logged."""
    product = _make_product(stock_qty=2)
    mock_metrics = MagicMock()

    with caplog.at_level(logging.WARNING, logger="sportshop.inventory"):
        result = check_low_stock(product, threshold=5, metrics=mock_metrics)

    assert result is True
    assert any("[ALERT]" in r.message for r in caplog.records)
    # Log should include identifying context
    alert_msg = next(r.message for r in caplog.records if "[ALERT]" in r.message)
    assert "TEST-SKU-001" in alert_msg
    assert "2" in alert_msg   # current qty
    assert "5" in alert_msg   # threshold


def test_check_low_stock_at_threshold_does_not_alert(caplog):
    """stock_qty == threshold → False (strict < boundary, no alert)."""
    product = _make_product(stock_qty=5)
    mock_metrics = MagicMock()

    with caplog.at_level(logging.WARNING, logger="sportshop.inventory"):
        result = check_low_stock(product, threshold=5, metrics=mock_metrics)

    assert result is False
    assert not any("[ALERT]" in r.message for r in caplog.records)
    mock_metrics.assert_not_called()


def test_check_low_stock_above_threshold_does_not_alert(caplog):
    """stock_qty > threshold → False, no alert."""
    product = _make_product(stock_qty=10)
    mock_metrics = MagicMock()

    with caplog.at_level(logging.WARNING, logger="sportshop.inventory"):
        result = check_low_stock(product, threshold=5, metrics=mock_metrics)

    assert result is False
    assert not any("[ALERT]" in r.message for r in caplog.records)
    mock_metrics.assert_not_called()


# ---------------------------------------------------------------------------
# Metric emission
# ---------------------------------------------------------------------------

def test_check_low_stock_calls_metrics_with_correct_args():
    """Alert path calls metrics emitter with (name, value, tags)."""
    product = _make_product(stock_qty=1, sku="SKU-METRIC")
    mock_metrics = MagicMock()

    check_low_stock(product, threshold=5, metrics=mock_metrics)

    mock_metrics.assert_called_once()
    name, value, tags = mock_metrics.call_args.args
    assert name == "inventory.low_stock_alert"
    assert value == 1
    assert tags.get("sku") == "SKU-METRIC"


def test_check_low_stock_metric_not_called_above_threshold():
    """No alert → metrics emitter is never called."""
    product = _make_product(stock_qty=99)
    mock_metrics = MagicMock()

    check_low_stock(product, threshold=5, metrics=mock_metrics)

    mock_metrics.assert_not_called()


# ---------------------------------------------------------------------------
# Threshold override
# ---------------------------------------------------------------------------

def test_check_low_stock_explicit_threshold_overrides_default(monkeypatch):
    """Explicit threshold= kwarg takes precedence over the global default."""
    # Global default is 5; we pass threshold=20 — stock_qty=10 should alert
    monkeypatch.setattr("app.services.inventory._THRESHOLD", 5)
    product = _make_product(stock_qty=10)
    mock_metrics = MagicMock()

    result = check_low_stock(product, threshold=20, metrics=mock_metrics)

    assert result is True
    mock_metrics.assert_called_once()


def test_check_low_stock_uses_global_threshold_when_not_supplied(monkeypatch):
    """When threshold= is omitted, the global LOW_STOCK_THRESHOLD is used."""
    monkeypatch.setattr("app.services.inventory._THRESHOLD", 10)
    product = _make_product(stock_qty=3)
    mock_metrics = MagicMock()

    result = check_low_stock(product, metrics=mock_metrics)

    # stock_qty=3 < _THRESHOLD=10 → should alert
    assert result is True
    mock_metrics.assert_called_once()


def test_check_low_stock_global_threshold_no_alert_when_above(monkeypatch):
    """stock_qty above patched global threshold → no alert."""
    monkeypatch.setattr("app.services.inventory._THRESHOLD", 2)
    product = _make_product(stock_qty=5)
    mock_metrics = MagicMock()

    result = check_low_stock(product, metrics=mock_metrics)

    assert result is False
    mock_metrics.assert_not_called()
