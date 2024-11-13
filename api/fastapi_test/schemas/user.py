from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    login: str
    name: str

from typing import Optional

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    login: Optional[str]




