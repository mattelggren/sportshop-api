from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
from enum import Enum


# --- Auth ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str


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
    model_config = ConfigDict(from_attributes=True)

    id: int


# --- Cart ---

class CartItem(BaseModel):
    product_id: int
    qty: int


class CartOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    items: List[CartItem]


# --- Orders ---

class OrderItemDetail(BaseModel):
    product_id: int
    qty: int
    price_at_purchase: float


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    items: List[OrderItemDetail]
    status: str
    total: float


# --- Reviews ---

class ReviewCreate(BaseModel):
    rating: int
    body: Optional[str] = None


class ReviewOut(ReviewCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    user_id: int
