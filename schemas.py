"""
Docstring
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from models import UserRole, ReservationStatus


class UserBase(BaseModel):
    """
    Docstring
    """

    email: EmailStr


class UserCreate(UserBase):
    """
    Docstring
    """

    password: str
    role: UserRole = UserRole.USER


class UserResponse(UserBase):
    """
    Docstring
    """

    id: int
    role: UserRole

    # pydantic expects dict, sqlalchemy - returns an object,
    # this fixes it
    class Config:
        """
        Docstring
        """

        from_attributes = True


class LoginData(BaseModel):
    """
    Docstring
    """

    email: EmailStr
    password: str


class HallBase(BaseModel):
    """
    Docstring
    """

    name: str
    description: str | None = None
    category: str
    capacity: int
    price_per_hour: float
    location: str


class HallCreate(HallBase):
    """
    Docstring
    """


class HallResponse(HallBase):
    """
    Docstring
    """

    id: int
    provider_id: int

    class Config:
        """
        Docstring
        """

        from_attributes = True


class ReservationBase(BaseModel):
    """
    Docstring
    """

    start_time: datetime
    end_time: datetime
    notes: str | None = None


class ReservationCreate(ReservationBase):
    """
    Docstring
    """

    hall_id: int


class ReservationResponse(ReservationBase):
    """
    Docstring
    """

    id: int
    status: ReservationStatus
    client_id: int
    hall_id: int
    total_price: float

    class Config:
        """
        Docstring
        """

        from_attributes = True


class Token(BaseModel):
    """
    Docstring
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Docstring
    """

    email: str | None = None
    role: str | None = None


class ReviewBase(BaseModel):
    """
    Docstring
    """

    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None
    hall_id: int


class ReviewCreate(ReviewBase):
    """
    Docstring
    """


class ReviewResponse(ReviewBase):
    """
    Docstring
    """

    id: int
    user_id: int

    class Config:
        """
        Docstring
        """

        from_attributes = True
