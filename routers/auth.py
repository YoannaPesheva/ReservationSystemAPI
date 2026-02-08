# to do: registration and login
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from sqlalchemy.orm import Session

import database, models, schemas
from database import get_db

# for the JWT token
SECRET_KEY = "mnogo-taen-klyuch-za-jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# for the swagger ui
router = APIRouter(tags=["Authentication"])

# endpoints
@router.post("/register", response_model = schemas.UserResponse)
def register_user(user: schemas.UserCreate, db:Session = Depends(get_db)) -> models.User: # !!!!!
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered!")
    
    if user.role == models.UserRole.ADMIN:
        raise HTTPException(
            status_code=403, 
            detail="Registration as Admin is not allowed! You can only register as a user or provider.")
    
    hashed_pass = get_hashed_pass(user.password)
    new_user = models.User(email = user.email, hashed_password = hashed_pass, role = user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/token", response_model = schemas.Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db:Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == form_data.username).first()

    if not db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user with this email!")

    if not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password!")
    
    access_token_expiration = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email, "role": db_user.role.value}, 
        expires_delta=access_token_expiration)
    
    return {"access_token": access_token, "token_type": "bearer"}

def get_hashed_pass(password: str) -> str:
    salt = gensalt()
    hashed_pass = hashpw(password.encode('utf-8'), salt)
    return hashed_pass.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta:  timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user