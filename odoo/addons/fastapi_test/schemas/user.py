from pydantic import BaseModel

class UserCreate(BaseModel):
    login: str
    name: str

class UserResponse(BaseModel):
    id: int
    login: str
    name: str



