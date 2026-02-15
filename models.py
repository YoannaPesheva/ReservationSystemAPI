"""
This is a module that is used to define the structure of the
database tables.
"""

import datetime
import enum
from sqlalchemy import (
    Column,
    Enum,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text,
    Float,
    Table,
)
from sqlalchemy.orm import relationship
from database import Base


class UserRole(str, enum.Enum):
    """
    There are only three roles available.
    """

    USER = "user"
    PROVIDER = "provider"
    ADMIN = "admin"


class ReservationStatus(str, enum.Enum):
    """
    There are only four types of status for reservations.
    """

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


# table for favourites
user_favourites = Table(
    "user_favourites",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("hall_id", Integer, ForeignKey("halls.id"), primary_key=True),
)


class User(Base):
    """
    This is the User's class and all its relationships.
    """

    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    email: str = Column(String, unique=True, index=True)
    hashed_password: str = Column(String)
    role: UserRole = Column(Enum(UserRole), default=UserRole.USER)

    halls = relationship("Hall", back_populates="provider")
    reservations = relationship("Reservation", back_populates="client")
    reviews = relationship("Review", back_populates="user")
    favourite_halls = relationship(
        "Hall", secondary=user_favourites, back_populates="favourited_by"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    def __str__(self):
        return f"User(id={self.id}, email={self.email}, role={self.role})>"


class Hall(Base):
    """
    This is the Hall's class and all its relationships.

    """

    __tablename__ = "halls"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, index=True)
    description: str = Column(Text)
    category: str = Column(String)
    capacity: int = Column(Integer)
    price_per_hour: float = Column(Float)
    location: str = Column(String)

    # hall -> user (provider) (many to one)
    provider_id = Column(Integer, ForeignKey("users.id"))
    provider = relationship("User", back_populates="halls")

    # revervations for this hall (one to many)
    reservations = relationship("Reservation", back_populates="hall")

    reviews = relationship("Review", back_populates="hall")

    favourited_by = relationship(
        "User", secondary=user_favourites, back_populates="favourite_halls"
    )

    def __repr__(self):
        return f"<Hall(id={self.id}, name={self.name}, provider_id={self.provider_id})>"

    def __str__(self):
        return f"Hall(id={self.id}, name={self.name}, provider_id={self.provider_id})>"
    

class HallUpdate(Base):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    capacity: int | None = None
    price_per_hour: float | None = None
    location: str | None = None


class Reservation(Base):
    """
    This is the Reservation's class and all its relationships.
    """

    __tablename__ = "reservations"

    id: int = Column(Integer, primary_key=True, index=True)
    start_time: datetime = Column(DateTime)
    end_time: datetime = Column(DateTime)
    status: ReservationStatus = Column(
        Enum(ReservationStatus), default=ReservationStatus.PENDING
    )
    notes: str | None = Column(Text, nullable=True)
    total_price: float = Column(Float)

    # client who made the reservation
    client_id = Column(Integer, ForeignKey("users.id"))
    client = relationship("User", back_populates="reservations")

    # hall that is reserved
    hall_id = Column(Integer, ForeignKey("halls.id"))
    hall = relationship("Hall", back_populates="reservations")

    def __repr__(self):
        return f"<Reservation(id={self.id}, hall_id={self.hall_id}, client_id={self.client_id},\
                        status={self.status})>"

    def __str__(self):
        return f"Reservation(id={self.id}, hall_id={self.hall_id}, client_id={self.client_id},\
                        status={self.status})>"


class Review(Base):
    """
    This is the Reviewsl's class and all its relationships.
    """

    __tablename__ = "reviews"

    id: int = Column(Integer, primary_key=True, index=True)
    rating: int = Column(Integer)
    comment: str | None = Column(Text, nullable=True)

    # client who made the review
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="reviews")

    # hall that is reviewed
    hall_id = Column(Integer, ForeignKey("halls.id"))
    hall = relationship("Hall", back_populates="reviews")

    def __repr__(self):
        return f"<Review(id={self.id}, rating={self.rating}, hall_id={self.hall_id}, \
                            user_id={self.user_id})>"

    def __str__(self):
        return f"Review(id={self.id}, rating={self.rating}, hall_id={self.hall_id}, \
                            user_id={self.user_id})>"
