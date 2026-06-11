# List of Known Defects


1. **Hardcoded JWT secret** — `app/core/security.py` line ~10
   - `SECRET_KEY = "dev-secret-key-replace-in-production"`
   - Should be loaded from environment variable

2. **Unauthenticated product creation** — `app/routers/products.py` POST `/`
   - `create_product` has no `Depends(get_current_user)` guard
   - Any unauthenticated caller can create products

3. **Unconstrained review rating** — `app/models/catalog.py` Review model + `app/routers/reviews.py`
   - `rating` has no database or Pydantic constraint (should be 1–5)
   - Values like 0, -1, 99 are accepted without error

4. **Non-atomic stock decrement** — `app/routers/orders.py` `place_order`
   - Stock decremented per-product without a transaction lock
   - Concurrent orders can oversell inventory
