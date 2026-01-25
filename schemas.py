from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user" # default = user

class UserResponse(BaseModel):
    id: int
    email: str
    role: str

    # pydantic expects dict, sqlalchemy - returns an object, 
    # this fixes it
    class Config:
        from_attributes = True

class LoginData(BaseModel):
    email: EmailStr
    password: str