from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.catalog import Cart, Product
from app.models.user import User
from app.schemas import CartItem, CartOut

router = APIRouter()


def _get_or_create_cart(user_id: int, db: Session) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id, items=[])
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


@router.get("/", response_model=CartOut)
def view_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_or_create_cart(current_user.id, db)


@router.post("/items", response_model=CartOut)
def add_item(
    item: CartItem,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock_qty < item.qty:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    cart = _get_or_create_cart(current_user.id, db)
    items = list(cart.items)
    for existing in items:
        if existing["product_id"] == item.product_id:
            existing["qty"] += item.qty
            break
    else:
        items.append(item.model_dump())

    cart.items = items
    db.commit()
    db.refresh(cart)
    return cart


@router.delete("/items/{product_id}", response_model=CartOut)
def remove_item(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = _get_or_create_cart(current_user.id, db)
    cart.items = [i for i in cart.items if i["product_id"] != product_id]
    db.commit()
    db.refresh(cart)
    return cart
