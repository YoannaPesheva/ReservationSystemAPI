"""
Docstring
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import engine, local_session
from routers import auth, halls, reservations, users, reviews
import models


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Docstring
    """
    models.Base.metadata.create_all(bind=engine)
    db = local_session()

    # put the admin in the database
    try:
        if not db.query(models.User).filter_by(role="admin").first():
            hashed_pass = auth.get_hashed_pass("admin123")

            admin = models.User(
                email="admin@gmail.com", hashed_password=hashed_pass, role="admin"
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()

    yield
    print("Shutting down!")


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(halls.router)
app.include_router(reservations.router)
app.include_router(users.router)
app.include_router(reviews.router)


@app.get("/")
def root():
    """
    Docstring
    """
    return {"Yay, the API is running successfully!"}
