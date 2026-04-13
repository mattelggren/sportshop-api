def test_place_order_success(client, auth_headers, sample_product):
    # Add to cart
    client.post("/cart/items", json={"product_id": sample_product["id"], "qty": 2}, headers=auth_headers)
    resp = client.post("/orders/", headers=auth_headers)
    assert resp.status_code == 201
    order = resp.json()
    assert order["status"] == "pending"
    assert order["total"] == round(sample_product["price"] * 2, 2)


def test_place_order_empty_cart(client, auth_headers):
    resp = client.post("/orders/", headers=auth_headers)
    assert resp.status_code == 400


def test_cancel_order(client, auth_headers, sample_product):
    client.post("/cart/items", json={"product_id": sample_product["id"], "qty": 1}, headers=auth_headers)
    order = client.post("/orders/", headers=auth_headers).json()
    resp = client.patch(f"/orders/{order['id']}/cancel", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_cancel_non_pending_order_fails(client, auth_headers, sample_product):
    """Cancelling an already-cancelled order should return 400."""
    client.post("/cart/items", json={"product_id": sample_product["id"], "qty": 1}, headers=auth_headers)
    order = client.post("/orders/", headers=auth_headers).json()
    client.patch(f"/orders/{order['id']}/cancel", headers=auth_headers)
    resp = client.patch(f"/orders/{order['id']}/cancel", headers=auth_headers)
    assert resp.status_code == 400


# --- Intentional defect tests (these should FAIL until defects are fixed) ---

def test_review_rating_validation(client, auth_headers, sample_product):
    """Rating of 99 should be rejected — but won't be until defect is fixed."""
    resp = client.post(
        f"/reviews/{sample_product['id']}",
        json={"rating": 99, "body": "Great shoe!"},
        headers=auth_headers,
    )
    # This assertion documents expected behavior; currently passes with 201 (defect)
    assert resp.status_code == 422, "Rating validation defect: values outside 1-5 not rejected"


def test_create_product_requires_auth(client):
    """Unauthenticated product creation should be rejected — but isn't (defect)."""
    resp = client.post("/products/", json={
        "name": "Ghost Product",
        "category": "test",
        "price": 9.99,
        "sku": "GHOST-001",
        "stock_qty": 1,
    })
    # Documents the defect: should be 401, currently 201
    assert resp.status_code == 401, "Auth defect: unauthenticated product creation succeeds"
