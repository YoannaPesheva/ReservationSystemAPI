from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# create the database
RESERVATIONS_DATABASE_URL = "sqlite:///./reservations.db"
engine = create_engine(RESERVATIONS_DATABASE_URL, connect_args={"check_same_thread": False})

# local session
local_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = local_session()
    try:
        yield db
    
    finally:
        db.close()