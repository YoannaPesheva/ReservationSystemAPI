from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user") # guest?, user, renter?, admin

    # to do: add more relations after adding the reservations
    # idea: since reservations have the name of the renter, then it will be easy to give access

# class Reservations(Base):
   # __tablename__="reservations"

    # to do: add name, description, category, working hours/availability
    # also pictures, renter, reviews (separately?)


