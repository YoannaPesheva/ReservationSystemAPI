"""
This module is used for managing users. It has endpoints for
getting and updating info of the current user, having favourites,
and some admin specifics.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db
from routers.auth import get_current_user, get_hashed_pass

router = APIRouter(prefix="/users", tags=["Users"])

# Users


@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """
    This function returns the information of the current user.
    """
    return current_user


@router.patch("/me", response_model=schemas.UserResponse)
def update_current_user_info(
    updated_info: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    This function is used for updating the current user's information.
    It allows updating the email and password, but checks if the new
    email is not already in the system.
    """
    update_data = updated_info.model_dump(exclude_unset=True)

    if "password" in update_data:
        password = update_data.pop("password")
        current_user.hashed_password = get_hashed_pass(password)
        

    if "email" in update_data:
        new_email = update_data["email"]
        user_exists = (db.query(models.User).filer(models.User.email == new_email).first())

        if user_exists and user_exists.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered by another user!",
            )

    for key, value in update_data.items():
        setattr(current_user, key, value)

    db.commit()
    db.refresh(current_user)
    return current_user


# Favourites


@router.post("/favourites/{hall_id}", status_code=status.HTTP_201_CREATED)
def add_favourite(
    hall_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    This function is used to add a hall to the current user's favourite
    halls. It checks if the hall is not already there.
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


@router.delete("/favourites/{hall_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favourite(
    hall_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    This function is used to remove a specific hall from the user's list of
    favourites. Chceks if the hall is actually in the favourites, or if it
    even exists.
    """
    hall = db.query(models.Hall).filter(models.Hall.id == hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found!")

    if hall not in current_user.favourite_halls:
        raise HTTPException(status_code=400, detail="Hall is not in favourites!")

    current_user.favourite_halls.remove(hall)
    db.commit()


@router.get("/favourites", response_model=List[schemas.HallResponse])
def get_favourites(current_user: models.User = Depends(get_current_user)):
    """
    This function returns the list of favourites for the current user.
    """
    return current_user.favourite_halls


# Admins


@router.get("/", response_model=List[schemas.UserResponse])
def get_all_users(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    """
    This function returns all the users in the system.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to view all users!")

    users = db.query(models.User).all()
    return users


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    This function deletes a specific user. It checks if the user exists.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete users!")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")

    db.delete(user)
    db.commit()
