"""
This module is used to for pydantic models.
The data coming in and out is validated and formatted.
DocStrings are added to each class as to satisfy pylint.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from models import UserRole, ReservationStatus


class UserBase(BaseModel):
    """
    The UserBase class - email
    is used everywhere.
    """

    email: EmailStr


class UserCreate(UserBase):
    """
    the UserCreate class.
    """

    password: str
    role: UserRole = UserRole.USER


class UserResponse(UserBase):
    """
    The UserResponse class
    """

    id: int
    role: UserRole

    class Config:
        """
        Add a setting here.
        """

        from_attributes = True


class LoginData(BaseModel):
    """
    The login data class.
    """

    email: EmailStr
    password: str


class HallBase(BaseModel):
    """
    The hall class.
    """

    name: str
    description: str | None = None
    category: str
    capacity: int
    price_per_hour: float
    location: str


class HallCreate(HallBase):
    """
    The HallCreate class.
    """


class HallResponse(HallBase):
    """
    The HallResponse class.
    """

    id: int
    provider_id: int

    class Config:
        """
        Add a setting.
        """

        from_attributes = True


class ReservationBase(BaseModel):
    """
    The ReservationBase class.
    """

    start_time: datetime
    end_time: datetime
    notes: str | None = None


class ReservationCreate(ReservationBase):
    """
    The ReservationCreate class.
    """

    hall_id: int


class ReservationResponse(ReservationBase):
    """
    The ReservationResponse class.
    """

    id: int
    status: ReservationStatus
    client_id: int
    hall_id: int
    total_price: float

    class Config:
        """
        Add a setting here as well.
        """

        from_attributes = True


class Token(BaseModel):
    """
    The token class.
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    The TokenData class.
    """

    email: str | None = None
    role: str | None = None


class ReviewBase(BaseModel):
    """
    The ReviewBase class.
    """

    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None
    hall_id: int


class ReviewCreate(ReviewBase):
    """
    The ReviewCreate class.
    """


class ReviewResponse(ReviewBase):
    """
    The ReviewResponse class.
    """

    id: int
    user_id: int

    class Config:
        """
        Add a setting.
        """

        from_attributes = True
