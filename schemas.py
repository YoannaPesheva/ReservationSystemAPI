from datetime import datetime
from pydantic import BaseModel, EmailStr
from models import UserRole, ReservationStatus

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.USER

class UserResponse(UserBase):
    id: int
    role: UserRole

    # pydantic expects dict, sqlalchemy - returns an object, 
    # this fixes it
    class Config:
        from_attributes = True

class LoginData(BaseModel):
    email: EmailStr
    password: str

class HallBase(BaseModel):
    name: str
    description: str | None = None
    category: str
    capacity: int
    price_per_hour: float
    location: str

class HallCreate(HallBase):
    pass

class HallResponse(HallBase):
    id: int
    provider_id: int

    class Config:
        from_attributes = True

class ReservationBase(BaseModel):
    start_time: datetime
    end_time: datetime
    notes: str | None = None

class ReservationCreate(ReservationBase):
    hall_id: int

class ReservationResponse(ReservationBase):
    id: int
    status: ReservationStatus
    client_id: int
    hall_id: int
    total_price: float

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None
    role: str | None = None