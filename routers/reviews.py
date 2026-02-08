"""
Docstring
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])


# create a review
@router.post(
    "/", response_model=schemas.ReviewResponse, status_code=status.HTTP_201_CREATED
)
def create_review(
    review: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Docstring
    """
    hall = db.query(models.Hall).filter(models.Hall.id == review.hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found!")

    existing_review = (
        db.query(models.Review)
        .filter(
            models.Review.hall_id == review.hall_id,
            models.Review.user_id == current_user.id,
        )
        .first()
    )

    if existing_review:
        raise HTTPException(
            status_code=400, detail="You have already reviewed this hall!"
        )

    new_review = models.Review(
        rating=review.rating,
        comment=review.comment,
        hall_id=review.hall_id,
        user_id=current_user.id,
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return new_review


# get reviews for a hall
@router.get("/hall/{hall_id}", response_model=List[schemas.ReviewResponse])
def get_reviews_for_hall(hall_id: int, db: Session = Depends(get_db)):
    """
    Docstring
    """
    reviews = db.query(models.Review).filter(models.Review.hall_id == hall_id).all()
    return reviews


# delete a review
@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Docstring
    """
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found!")

    if review.user_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this review!"
        )

    db.delete(review)
    db.commit()
