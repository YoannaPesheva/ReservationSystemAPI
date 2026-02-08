"""
Docstring
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db
from routers.auth import get_current_user, get_hashed_pass

router = APIRouter(prefix="/users", tags=["Users"])

# users management


# get the current user info
@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """
    Docstring
    """
    return current_user


# update the current user ifno
@router.put("/me", response_model=schemas.UserResponse)
def update_current_user_info(
    updated_info: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Docstring
    """
    if updated_info.email:
        db_user = (
            db.query(models.User)
            .filter(models.User.email == updated_info.email)
            .first()
        )
        if db_user and db_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered by another user!",
            )

    if updated_info.email:
        current_user.email = updated_info.email

    if updated_info.password:
        current_user.hashed_password = get_hashed_pass(updated_info.password)

    db.commit()
    db.refresh(current_user)
    return current_user


# favourites logic


# add favourite
@router.post("/favourites/{hall_id}", status_code=status.HTTP_201_CREATED)
def add_favourite(
    hall_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Docstring
    """
    hall = db.query(models.Hall).filter(models.Hall.id == hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found!")

    # check if already favourited
    if hall in current_user.favourite_halls:
        raise HTTPException(status_code=400, detail="Hall is already in favourites!")

    current_user.favourite_halls.append(hall)
    db.commit()

    return {"detail": "Hall added to favourites!"}


# delete favourite
@router.delete("/favourites/{hall_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favourite(
    hall_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Docstring
    """
    hall = db.query(models.Hall).filter(models.Hall.id == hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found!")

    if hall not in current_user.favourite_halls:
        raise HTTPException(status_code=400, detail="Hall is not in favourites!")

    current_user.favourite_halls.remove(hall)
    db.commit()


# get favourites
@router.get("/favourites", response_model=List[schemas.HallResponse])
def get_favourites(current_user: models.User = Depends(get_current_user)):
    """
    Docstring
    """
    return current_user.favourite_halls


# admin management


# get all users
@router.get("/", response_model=List[schemas.UserResponse])
def get_all_users(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    """
    Docstring
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to view all users!")

    users = db.query(models.User).all()
    return users


# delete a user
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Docstring
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete users!")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")

    db.delete(user)
    db.commit()
