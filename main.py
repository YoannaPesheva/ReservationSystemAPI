from database import engine, local_session
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from routers import auth, halls, reservations
from fastapi import FastAPI
import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    db = local_session()
    
    # put the admin in the database
    try:
        if not db.query(models.User).filter_by(role="admin").first():
            hashed_pass = auth.get_hashed_pass("admin123")

            admin = models.User(
                email="admin@gmail.com",
                hashed_password=hashed_pass,
                role="admin"
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

@app.get("/")
def root():
    return {"Yay, the API is running successfully!"}   


