"""
This is the authentication module. It handles the
registration and login, as well as hashing passwords and using tokens.
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from bcrypt import hashpw, gensalt, checkpw
from jose import JWTError, jwt
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

# for the JWT token
SECRET_KEY = "mnogo-taen-klyuch-za-jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(tags=["Authentication"])


# endpoints for registration and login
@router.post("/register", response_model=schemas.UserResponse)
def register_user(
    user: schemas.UserCreate, db: Session = Depends(get_db)
) -> models.User:
    """
    This function registers a new user.
    It checks if the email is already registered,
    hashes the password, and saves the user to the database.
    It also prevents registration as an admin (since there is only one).
    """
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered!"
        )

    if user.role == models.UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="You can only register as a user or provider - not admin!",
        )

    hashed_pass = get_hashed_pass(user.password)
    new_user = models.User(
        email=user.email, hashed_password=hashed_pass, role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/token", response_model=schemas.Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    This function logs in a user.
    It checks if the email is registered,
    verifies that the password is correct,
    and generates a token for the user.
    """
    db_user = (
        db.query(models.User).filter(models.User.email == form_data.username).first()
    )

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No user with this email!"
        )

    if not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password!"
        )

    access_token_expiration = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email, "role": db_user.role.value},
        expires_delta=access_token_expiration,
    )

    return {"access_token": access_token, "token_type": "bearer"}


def get_hashed_pass(password: str) -> str:
    """
    The function is used for hashing the password (using bcrypt).
    """
    salt = gensalt()
    hashed_pass = hashpw(password.encode("utf-8"), salt)
    return hashed_pass.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    The function is used for verifying the user's password.
    """
    return checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    The function is used for creating an access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    """
    This function returns the current user.
    It basically decodes the token and retrieves the user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        token_sub = payload.get("sub")
        if token_sub is None:
            raise credentials_exception

        email: str = token_sub

    except JWTError as exc:
        raise credentials_exception from exc

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception

    return user
