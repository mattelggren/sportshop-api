# Orders API

Base path: `/orders`

---

## `POST /orders/`

**Auth**: Bearer token required (any authenticated user)

**Request**: No request body. Order is built from the caller's current cart.

**Response `201 Created`**:

| Field | Type | Description |
|---|---|---|
| `id` | `integer` | Order ID |
| `user_id` | `integer` | Owning user ID |
| `status` | `string` | Initial status: `"pending"` |
| `total` | `float` | Sum of `price × qty` for all line items, rounded to 2 decimal places |
| `items` | `array` | Line items snapshot (see below) |

`items` entries:

| Field | Type | Description |
|---|---|---|
| `product_id` | `integer` | Product ID |
| `qty` | `integer` | Quantity ordered |
| `price_at_purchase` | `float` | Product price at time of order |

**Errors**:

| Status | Condition |
|---|---|
| `400` | Cart is empty or does not exist |
| `400` | A product in the cart no longer exists |
| `400` | Insufficient stock for one or more products |
| `401` | Missing or invalid Bearer token |

**Known defects**:
> `orders.py:35` — Stock is decremented without a row lock (`SELECT ... FOR UPDATE`). Concurrent requests can both pass the stock check and both decrement, producing negative inventory (oversell). See `defect-scan-2026-04-13.md` #4.
>
> `orders.py:30` — Stock check is disconnected from the cart add-item check, creating a TOCTOU window. See `defect-scan-2026-04-13.md` #6.

---

## `GET /orders/`

**Auth**: Bearer token required (any authenticated user)

**Request**: No parameters.

**Response `200 OK`**: Array of `OrderOut` objects (see schema above) belonging to the authenticated user. Returns `[]` if the user has no orders.

**Errors**:

| Status | Condition |
|---|---|
| `401` | Missing or invalid Bearer token |

---

## `GET /orders/{order_id}`

**Auth**: Bearer token required (any authenticated user)

**Path parameters**:

| Parameter | Type | Description |
|---|---|---|
| `order_id` | `integer` | ID of the order to retrieve |

**Response `200 OK`**: Single `OrderOut` object.

**Errors**:

| Status | Condition |
|---|---|
| `404` | Order does not exist, or belongs to a different user |
| `401` | Missing or invalid Bearer token |

> **Note**: The `404` response is returned for both "not found" and "wrong owner" cases — ownership is enforced silently by filtering on `user_id` in the query.

---

## `PATCH /orders/{order_id}/cancel`

**Auth**: Bearer token required (any authenticated user, own orders only)

**Path parameters**:

| Parameter | Type | Description |
|---|---|---|
| `order_id` | `integer` | ID of the order to cancel |

**Request**: No request body.

**Response `200 OK`**: Updated `OrderOut` object with `status: "cancelled"`.

**Errors**:

| Status | Condition |
|---|---|
| `400` | Order status is not `pending` (already confirmed, shipped, or cancelled) |
| `404` | Order does not exist, or belongs to a different user |
| `401` | Missing or invalid Bearer token |

**Known defects**:
> `orders.py:88` — Cancellation does not restore stock. Units decremented at order placement are permanently removed from inventory on cancellation. See `defect-scan-2026-04-13.md` #7.

---

## Order Status Reference

| Status | Reachable via API | Transitions to |
|---|---|---|
| `pending` | Yes — set on `POST /orders/` | `cancelled` |
| `confirmed` | **No** — no endpoint exists | — |
| `shipped` | **No** — no endpoint exists | — |
| `cancelled` | Yes — via `PATCH /cancel` | (terminal) |

> **Known gap**: `confirmed` and `shipped` statuses are defined in `OrderStatus` but no endpoint can set them. There is no admin workflow to advance an order beyond `pending`. See `defect-scan-2026-04-13.md` #8.
