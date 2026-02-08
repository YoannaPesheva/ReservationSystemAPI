from sqlalchemy import Column, Enum, Integer, String, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from database import Base
import enum

class UserRole(str, enum.Enum):
    USER = "user"
    PROVIDER = "provider"
    ADMIN = "admin"

class ReservationStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.USER)

    halls = relationship("Hall", back_populates="provider")
    reservations = relationship("Reservation", back_populates="client")
    reviews = relationship("Review", back_populates="user")

class Hall(Base):
    __tablename__ = "halls"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    category = Column(String)
    capacity = Column(Integer)
    price_per_hour = Column(Float)
    location = Column(String)

    # hall -> user (provider) (many to one)
    provider_id = Column(Integer, ForeignKey("users.id"))
    provider = relationship("User", back_populates="halls")

    # revervations for this hall (one to many)
    reservations = relationship("Reservation", back_populates="hall")

    reviews = relationship("Review", back_populates="hall")

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.PENDING)
    notes = Column(Text, nullable=True)
    total_price = Column(Float)

    # client who made the reservation
    client_id = Column(Integer, ForeignKey("users.id"))
    client = relationship("User", back_populates="reservations")

    # hall that is reserved
    hall_id = Column(Integer, ForeignKey("halls.id"))
    hall = relationship("Hall", back_populates="reservations")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer)
    comment = Column(Text, nullable=True)

    # client who made the review
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="reviews")

    # hall that is reviewed
    hall_id = Column(Integer, ForeignKey("halls.id"))
    hall = relationship("Hall", back_populates="reviews")