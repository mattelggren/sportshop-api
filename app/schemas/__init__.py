from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum


# --- Auth ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# --- Products ---

class ProductCreate(BaseModel):
    name: str
    category: str
    price: float
    sku: str
    stock_qty: int = 0


class ProductOut(ProductCreate):
    id: int

    class Config:
        from_attributes = True


# --- Cart ---

class CartItem(BaseModel):
    product_id: int
    qty: int


class CartOut(BaseModel):
    user_id: int
    items: List[CartItem]

    class Config:
        from_attributes = True


# --- Orders ---

class OrderItemDetail(BaseModel):
    product_id: int
    qty: int
    price_at_purchase: float


class OrderOut(BaseModel):
    id: int
    user_id: int
    items: List[OrderItemDetail]
    status: str
    total: float

    class Config:
        from_attributes = True


# --- Reviews ---

class ReviewCreate(BaseModel):
    rating: int
    body: Optional[str] = None


class ReviewOut(ReviewCreate):
    id: int
    product_id: int
    user_id: int

    class Config:
        from_attributes = True
