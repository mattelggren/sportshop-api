from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, Enum, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, index=True)
    price = Column(Float, nullable=False)
    sku = Column(String, unique=True, index=True, nullable=False)
    stock_qty = Column(Integer, default=0)

    reviews = relationship("Review", back_populates="product")


class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    cancelled = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    items = Column(JSON, nullable=False)  # [{product_id, qty, price_at_purchase}]
    status = Column(Enum(OrderStatus), default=OrderStatus.pending)
    total = Column(Float, nullable=False)


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    items = Column(JSON, default=list)  # [{product_id, qty}]


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # INTENTIONAL DEFECT: no constraint (1-5)
    body = Column(Text)

    product = relationship("Product", back_populates="reviews")
