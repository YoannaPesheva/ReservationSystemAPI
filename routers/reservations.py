"""
Docstring
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/reservations", tags=["Reservations"])


# create a reservation
@router.post("/", response_model=schemas.ReservationResponse)
def create_reservation(
    reservation: schemas.ReservationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Docstring
    """
    hall = db.query(models.Hall).filter(models.Hall.id == reservation.hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found!")

    # do the overlap check for reservations
    overlapping_reservations = (
        db.query(models.Reservation)
        .filter(
            models.Reservation.hall_id == reservation.hall_id,
            models.Reservation.start_time < reservation.end_time,
            models.Reservation.end_time > reservation.start_time,
            models.Reservation.status != models.ReservationStatus.CANCELLED,
        )
        .all()
    )

    if overlapping_reservations:
        raise HTTPException(
            status_code=400, detail="The requested time slot is already reserved!"
        )

    # calculate the price
    duration_hours = (
        reservation.end_time - reservation.start_time
    ).total_seconds() / 3600
    calculated_price = duration_hours * hall.price_per_hour

    # put it in the database
    new_reservation = models.Reservation(
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        notes=reservation.notes,
        hall_id=reservation.hall_id,
        client_id=current_user.id,
        total_price=calculated_price,
        status=models.ReservationStatus.PENDING,
    )

    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)
    return new_reservation


# get reservations
@router.get("/", response_model=List[schemas.ReservationResponse])
def get_reservations(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    """
    Docstring
    """

    reservations = []

    if current_user.role == models.UserRole.USER:
        reservations = (
            db.query(models.Reservation)
            .filter(models.Reservation.client_id == current_user.id)
            .all()
        )
    elif current_user.role == models.UserRole.PROVIDER:
        reservations = (
            db.query(models.Reservation)
            .join(models.Hall)
            .filter(models.Hall.provider_id == current_user.id)
            .all()
        )
    elif current_user.role == models.UserRole.ADMIN:
        reservations = db.query(models.Reservation).all()

    return reservations


# update status
@router.patch("/{reservation_id}/status", response_model=schemas.ReservationResponse)
def update_reservation_status(
    reservation_id: int,
    new_status: models.ReservationStatus,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Docstring
    """
    reservation = (
        db.query(models.Reservation)
        .filter(models.Reservation.id == reservation_id)
        .first()
    )

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found!")

    hall = db.query(models.Hall).filter(models.Hall.id == reservation.hall_id).first()

    if not hall:
        raise HTTPException(status_code=404, detail="Associated hall not found!")

    is_admin = current_user.role == models.UserRole.ADMIN
    is_provider_owner = (
        current_user.role == models.UserRole.PROVIDER
        and hall.provider_id == current_user.id
    )
    is_reservation_owner = (
        current_user.role == models.UserRole.USER
        and reservation.client_id == current_user.id
    )

    if is_admin or is_provider_owner:
        pass
    elif is_reservation_owner:
        if new_status != models.ReservationStatus.CANCELLED:
            raise HTTPException(
                status_code=403, detail="Users can only cancel their reservations!"
            )

        if reservation.status == models.ReservationStatus.CANCELLED:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to change the status of this reservation!",
            )

    if reservation.status == models.ReservationStatus.CANCELLED:
        raise HTTPException(
            status_code=400, detail="Cannot update a cancelled reservation!"
        )

    if (
        reservation.status == models.ReservationStatus.CONFIRMED
        and new_status == models.ReservationStatus.PENDING
    ):
        raise HTTPException(
            status_code=400,
            detail="Cannot revert a confirmed reservation back to pending!",
        )

    if (
        reservation.status == models.ReservationStatus.COMPLETED
        and new_status != models.ReservationStatus.COMPLETED
    ):
        raise HTTPException(
            status_code=400,
            detail="Cannot change the status of a completed reservation!",
        )

    reservation.status = new_status
    db.commit()
    db.refresh(reservation)
    return reservation
