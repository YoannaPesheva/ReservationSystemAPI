# to do: registration and login
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import database, models, schemas
from database import get_db

# for the swagger ui
router = APIRouter(
    tags=["Authentication"]
)

# endpoints
@router.post("/register", response_model = schemas.UserResponse)
def register_user(user: schemas.UserCreate, db:Session = Depends(get_db)): # !!!!!
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        # raise some exception
        pass
    
    hashed_pass = get_hashed_pass(user.password)
    new_user = models.User(email = user.email, hashed_password = hashed_pass, role = user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
# to do


def get_hashed_pass(password):
    # there was a simple algorithm for hashing
    pass

