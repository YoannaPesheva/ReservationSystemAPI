"""
This is the main module - it initializes the FastAPI app and includes all routers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import engine, local_session
from routers import auth, halls, reservations, users, reviews
import models


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    This function is used to set up the database and
    hardcode an admin user at the start.
    """
    models.Base.metadata.create_all(bind=engine)
    db = local_session()

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


# here all the routers get included
app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(halls.router)
app.include_router(reservations.router)
app.include_router(users.router)
app.include_router(reviews.router)


@app.get("/")
def root():
    """
    The root endpoint - just to check if the API is running.
    """
    return {"Yay, the API is running successfully!"}
