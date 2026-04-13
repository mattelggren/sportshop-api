from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.catalog import Cart, Order, Product, OrderStatus
from app.models.user import User
from app.schemas import OrderOut

router = APIRouter()


@router.post("/", response_model=OrderOut, status_code=201)
def place_order(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    order_items = []
    total = 0.0

    for item in cart.items:
        product = db.query(Product).filter(Product.id == item["product_id"]).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item['product_id']} not found")
        if product.stock_qty < item["qty"]:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")

        # INTENTIONAL DEFECT: stock decremented but not committed atomically;
        # concurrent orders can oversell
        product.stock_qty -= item["qty"]
        line_total = product.price * item["qty"]
        total += line_total
        order_items.append({
            "product_id": product.id,
            "qty": item["qty"],
            "price_at_purchase": product.price,
        })

    order = Order(
        user_id=current_user.id,
        items=order_items,
        total=round(total, 2),
        status=OrderStatus.pending,
    )
    db.add(order)
    cart.items = []
    db.commit()
    db.refresh(order)
    return order


@router.get("/", response_model=List[OrderOut])
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Order).filter(Order.user_id == current_user.id).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.pending:
        raise HTTPException(status_code=400, detail="Only pending orders can be cancelled")
    order.status = OrderStatus.cancelled
    db.commit()
    db.refresh(order)
    return order
