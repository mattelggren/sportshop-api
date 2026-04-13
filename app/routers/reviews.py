from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.catalog import Review, Product
from app.models.user import User
from app.schemas import ReviewCreate, ReviewOut

router = APIRouter()


@router.post("/{product_id}", response_model=ReviewOut, status_code=201)
def post_review(
    product_id: int,
    review_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # INTENTIONAL DEFECT: no check that rating is 1-5
    review = Review(
        product_id=product_id,
        user_id=current_user.id,
        rating=review_in.rating,
        body=review_in.body,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/{product_id}", response_model=List[ReviewOut])
def list_reviews(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db.query(Review).filter(Review.product_id == product_id).all()
