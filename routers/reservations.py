from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import database, models, schemas
from database import get_db
from typing import List
from routers.auth import get_current_user

router = APIRouter(prefix="/reservations", tags=["Reservations"])

# create a reservation
@router.post("/", response_model=schemas.ReservationResponse)
def create_reservation(reservation: schemas.ReservationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):

    hall = db.query(models.Hall).filter(models.Hall.id == reservation.hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found!")
    
    # do the overlap check for reservations

    # calculate the price
    calculated_price = 0

    # put it in the database
    new_reservation = models.Reservation(
        start_time = reservation.start_time,
        end_time = reservation.end_time,
        notes = reservation.notes,
        hall_id = reservation.hall_id,
        client_id = current_user.id,
        total_price = calculated_price,
        status = models.ReservationStatus.PENDING
    )

    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)
    return new_reservation

# get reservations

# update status


