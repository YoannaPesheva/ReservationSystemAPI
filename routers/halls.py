from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import database, models, schemas
from database import get_db
from typing import List
from routers.auth import get_current_user

router = APIRouter(prefix="/halls", tags=["Halls"])


# search
@router.get("/search", response_model=List[schemas.HallResponse])
def get_halls(
    search: str | None = None,
    category: str | None = None,
    min_capacity: int | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Hall)

    if search:
        query = query.filter(models.Hall.name.contains(search))

    if category:
        query = query.filter(models.Hall.category == category)
    
    if min_capacity:
        query = query.filter(models.Hall.capacity >= min_capacity)
    
    return query.all()

# get a hall by id
@router.get("/{hall_id}", response_model=schemas.HallResponse)
def get_hall(hall_id: int, db: Session = Depends(get_db)):
    hall = db.query(models.Hall).filter(models.Hall.id == hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found!")
    return hall

# create a hall
@router.post("/", response_model=schemas.HallResponse, status_code=status.HTTP_201_CREATED)
def create_hall(hall: schemas.HallCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role not in [models.UserRole.PROVIDER, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to create halls!")
    
    new_hall = models.Hall(**hall.model_dump(), provider_id=current_user.id)

    db.add(new_hall)
    db.commit()
    db.refresh(new_hall)

    return new_hall

# delete a hall
@router.delete("/{hall_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hall(hall_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    hall = db.query(models.Hall).filter(models.Hall.id == hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found!")
    
    if current_user.role != models.UserRole.ADMIN and hall.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this hall!")

    db.delete(hall)
    db.commit()

    return None

# make changes to a hall
@router.put("/{hall_id}", response_model=schemas.HallResponse)
def update_hall(hall_id: int, hall_update: schemas.HallCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_hall = db.query(models.Hall).filter(models.Hall.id == hall_id).first()

    if not db_hall:
        raise HTTPException(status_code=404, detail="Hall not found!")

    if current_user.role != models.UserRole.ADMIN and db_hall.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this hall!")

    db_hall.name = hall_update.name
    db_hall.description = hall_update.description
    db_hall.category = hall_update.category
    db_hall.capacity = hall_update.capacity
    db_hall.price_per_hour = hall_update.price_per_hour
    db_hall.location = hall_update.location

    db.commit()
    db.refresh(db_hall)

    return db_hall