import os

# Global low-stock threshold; override with SPORTSHOP_LOW_STOCK_THRESHOLD env var.
# Alert fires when product.stock_qty drops strictly below this value.
LOW_STOCK_THRESHOLD: int = int(os.getenv("SPORTSHOP_LOW_STOCK_THRESHOLD", "5"))
