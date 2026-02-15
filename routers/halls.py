"""
This module is used for managing the halls. It includes endpoints for:
- searching halls, getting a specific hall, creating/updating/deleting halls.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/halls", tags=["Halls"])


@router.get("/search", response_model=List[schemas.HallResponse])
def get_halls(
    search: str | None = None,
    category: str | None = None,
    min_capacity: int | None = None,
    db: Session = Depends(get_db),
):
    """
    This function returns the list of halls based on the search of a user.
    It allows to search by name, category, or minimum capacity.
    """
    query = db.query(models.Hall)

    if search:
        query = query.filter(models.Hall.name.contains(search))

    if category:
        query = query.filter(models.Hall.category == category)

    if min_capacity:
        query = query.filter(models.Hall.capacity >= min_capacity)

    return query.all()

@router.get("/", response_model=List[schemas.HallResponse])
def get_all_halls(db: Session = Depends(get_db)):
    halls = db.query(models.Hall).all() 
    return halls

@router.get("/{hall_id}", response_model=schemas.HallResponse)
def get_hall(hall_id: int, db: Session = Depends(get_db)):
    """
    This function returns a specific hall by its ID.
    """
    hall = db.query(models.Hall).filter(models.Hall.id == hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found!")
    return hall


@router.post(
    "/", response_model=schemas.HallResponse, status_code=status.HTTP_201_CREATED
)
def create_hall(
    hall: schemas.HallCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    This function is used to create a new hall.
    It takes into account the fact that only providers
    and admins can do this.
    """
    if current_user.role not in [models.UserRole.PROVIDER, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to create halls!")

    new_hall = models.Hall(**hall.model_dump(), provider_id=current_user.id)

    db.add(new_hall)
    db.commit()
    db.refresh(new_hall)

    return new_hall


@router.delete("/{hall_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hall(
    hall_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    The function is used to delete a hall.
    It takes into account the fact that only admins and
    the provider who created the hall can delete it.
    """
    hall = db.query(models.Hall).filter(models.Hall.id == hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found!")

    if (
        current_user.role != models.UserRole.ADMIN
        and hall.provider_id != current_user.id
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this hall!"
        )

    db.delete(hall)
    db.commit()


@router.put("/{hall_id}", response_model=schemas.HallResponse)
def update_hall(
    hall_id: int,
    hall_update: schemas.HallUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    This function is used to update a hall's information.
    It takes into account the fact that only admins and
    the provider who created the hall can update it.
    """
    db_hall = db.query(models.Hall).filter(models.Hall.id == hall_id).first()

    if not db_hall:
        raise HTTPException(status_code=404, detail="Hall not found!")

    if (
        current_user.role != models.UserRole.ADMIN
        and db_hall.provider_id != current_user.id
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to update this hall!"
        )

    update_data = hall_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_hall, key, value) 

    db.commit()
    db.refresh(db_hall)

    return db_hall
