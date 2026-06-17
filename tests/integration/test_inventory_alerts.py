"""
Integration tests for the inventory low-stock alert system.

Tests exercise the full HTTP request → stock decrement → check_low_stock path,
asserting on captured log output (caplog) rather than on any DB state.

Alert policy under test:
- Fire on EVERY order/update that leaves stock_qty < threshold (no de-dup)
- Strict < semantics (== threshold is not an alert)

Admin fixture: there is no admin-registration endpoint, so we promote a user
to admin directly via the `db` session fixture.
"""
import logging

import pytest

from app.models.user import UserRole

# Threshold is set low (3) via monkeypatching for all tests in this module.
LOW = 3


@pytest.fixture(autouse=True)
def patch_threshold(monkeypatch):
    """Override the module-level _THRESHOLD and config value to LOW for all tests here."""
    monkeypatch.setattr("app.services.inventory._THRESHOLD", LOW)
    monkeypatch.setenv("SPORTSHOP_LOW_STOCK_THRESHOLD", str(LOW))


@pytest.fixture
def low_stock_product(client):
    """Product with stock_qty just above the patched threshold (4 > 3)."""
    resp = client.post("/products/", json={
        "name": "Low Stock Item",
        "category": "gear",
        "price": 49.99,
        "sku": "LSI-001",
        "stock_qty": 4,
    })
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def ample_stock_product(client):
    """Product with stock_qty well above threshold (20 > 3)."""
    resp = client.post("/products/", json={
        "name": "Ample Stock Item",
        "category": "gear",
        "price": 19.99,
        "sku": "ASI-001",
        "stock_qty": 20,
    })
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def admin_auth_headers(client, db):
    """Register a user and promote them to admin directly via the db session."""
    from app.core.security import get_password_hash
    from app.models.user import User

    admin_email = "admin@example.com"
    admin_password = "adminpass123"

    user = User(
        email=admin_email,
        hashed_password=get_password_hash(admin_password),
        role=UserRole.admin,
    )
    db.add(user)
    db.commit()

    resp = client.post("/auth/login", data={"username": admin_email, "password": admin_password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _add_to_cart_and_order(client, auth_headers, product_id: int, qty: int):
    """Helper: add qty of product to cart, then place an order."""
    resp = client.post("/cart/items", json={"product_id": product_id, "qty": qty},
                       headers=auth_headers)
    assert resp.status_code in (200, 201)
    resp = client.post("/orders/", headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Order-driven breach
# ---------------------------------------------------------------------------

def test_order_dropping_below_threshold_fires_alert(
    client, auth_headers, low_stock_product, caplog
):
    """Placing an order that takes stock from 4 → 2 (< 3) fires an alert."""
    with caplog.at_level(logging.WARNING, logger="sportshop.inventory"):
        _add_to_cart_and_order(client, auth_headers, low_stock_product["id"], qty=2)

    assert any("[ALERT]" in r.message for r in caplog.records), \
        "Expected a low-stock [ALERT] log entry but none was found"


def test_order_keeping_stock_at_or_above_threshold_no_alert(
    client, auth_headers, ample_stock_product, caplog
):
    """Placing an order that takes stock from 20 → 19 (> 3) fires no alert."""
    with caplog.at_level(logging.WARNING, logger="sportshop.inventory"):
        _add_to_cart_and_order(client, auth_headers, ample_stock_product["id"], qty=1)

    assert not any("[ALERT]" in r.message for r in caplog.records), \
        "Unexpected low-stock [ALERT] for product still well above threshold"


def test_every_breach_order_fires_separate_alert(client, auth_headers, caplog):
    """Every qualifying order fires an independent alert (no de-dup suppression)."""
    # Create a product with enough stock for two orders each dropping below threshold.
    resp = client.post("/products/", json={
        "name": "Multi Breach Item",
        "category": "gear",
        "price": 9.99,
        "sku": "MBI-001",
        "stock_qty": 6,   # order 1: 6→4 (still ≥ 3, no alert), order 2: 4→2 (<3, alert)
    })
    # Actually let's set it up so BOTH orders breach:
    # stock=5, order1 qty=3 → stock=2 (<3, alert), order2 qty=1 → stock=1 (<3, alert)
    resp = client.post("/products/", json={
        "name": "Double Breach Item",
        "category": "gear",
        "price": 9.99,
        "sku": "DBI-001",
        "stock_qty": 5,
    })
    assert resp.status_code == 201
    product_id = resp.json()["id"]

    with caplog.at_level(logging.WARNING, logger="sportshop.inventory"):
        # First order: 5 → 2  (< 3, breach)
        _add_to_cart_and_order(client, auth_headers, product_id, qty=3)
        # Second order: 2 → 1  (< 3, still breaching — every-breach policy)
        _add_to_cart_and_order(client, auth_headers, product_id, qty=1)

    alert_count = sum(1 for r in caplog.records if "[ALERT]" in r.message)
    assert alert_count == 2, \
        f"Expected 2 low-stock alerts (every-breach policy) but got {alert_count}"


# ---------------------------------------------------------------------------
# Admin PUT stock update
# ---------------------------------------------------------------------------

def test_admin_update_lowering_stock_below_threshold_fires_alert(
    client, admin_auth_headers, low_stock_product, caplog
):
    """Admin PUT /products/{id} reducing stock_qty below threshold fires an alert."""
    payload = {**low_stock_product, "stock_qty": 1}   # 1 < 3
    # Remove 'id' from payload since ProductCreate schema doesn't include it
    payload.pop("id", None)

    with caplog.at_level(logging.WARNING, logger="sportshop.inventory"):
        resp = client.put(
            f"/products/{low_stock_product['id']}",
            json=payload,
            headers=admin_auth_headers,
        )

    assert resp.status_code == 200
    assert any("[ALERT]" in r.message for r in caplog.records), \
        "Expected alert when admin lowers stock below threshold"


def test_admin_restock_above_threshold_no_alert(
    client, admin_auth_headers, low_stock_product, caplog
):
    """Admin PUT restocking above threshold does not fire an alert."""
    payload = {**low_stock_product, "stock_qty": 50}  # 50 >= 3
    payload.pop("id", None)

    with caplog.at_level(logging.WARNING, logger="sportshop.inventory"):
        resp = client.put(
            f"/products/{low_stock_product['id']}",
            json=payload,
            headers=admin_auth_headers,
        )

    assert resp.status_code == 200
    assert not any("[ALERT]" in r.message for r in caplog.records), \
        "Unexpected alert when admin restocks above threshold"


# ---------------------------------------------------------------------------
# Create-product edge case
# ---------------------------------------------------------------------------

def test_create_product_below_threshold_fires_alert(client, caplog):
    """Creating a product with stock_qty < threshold fires an immediate alert."""
    with caplog.at_level(logging.WARNING, logger="sportshop.inventory"):
        resp = client.post("/products/", json={
            "name": "Born Low",
            "category": "gear",
            "price": 5.00,
            "sku": "BL-001",
            "stock_qty": 1,  # 1 < 3
        })

    assert resp.status_code == 201
    assert any("[ALERT]" in r.message for r in caplog.records), \
        "Expected alert when a product is created with stock below threshold"
