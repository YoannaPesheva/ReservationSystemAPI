"""
This module is used for setting up the database.
"""

from typing import Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

RESERVATIONS_DATABASE_URL = "sqlite:///./reservations.db"
engine = create_engine(
    RESERVATIONS_DATABASE_URL, connect_args={"check_same_thread": False}
)

local_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base: Any = declarative_base()


def get_db():
    """
    The function is used to start a database session and close it after
    use.
    """
    db = local_session()
    try:
        yield db

    finally:
        db.close()
