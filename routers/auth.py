# to do: registration and login
from fastapi import APIRouter, Depends, HTTPException, status
from bcrypt import hashpw, gensalt, checkpw
from sqlalchemy.orm import Session

import database, models, schemas
from database import get_db

# for the swagger ui
router = APIRouter(
    tags=["Authentication"]
)

# endpoints
@router.post("/register", response_model = schemas.UserResponse)
def register_user(user: schemas.UserCreate, db:Session = Depends(get_db)) -> models.User: # !!!!!
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered!")
    
    hashed_pass = get_hashed_pass(user.password)
    new_user = models.User(email = user.email, hashed_password = hashed_pass, role = user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model = schemas.UserResponse)
def login_user(user: schemas.LoginData, db:Session = Depends(get_db)) -> models.User:
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user with this email!")

    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password!")
    
    return db_user

def get_hashed_pass(password: str) -> str:
    salt = gensalt()
    hashed = hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

