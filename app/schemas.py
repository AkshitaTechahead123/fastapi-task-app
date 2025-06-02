from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime

class UserSignup(BaseModel):
    first_name: str = Field(..., example="John")
    last_name: str = Field(..., example="Doe")
    username: str = Field(..., example="johndoe")
    password: str = Field(..., example="strongpassword")

class UserLogin(BaseModel):
    username: str = Field(..., example="johndoe")
    password: str = Field(..., example="strongpassword")

class TaskBase(BaseModel):
    title: str = Field(..., example="My Task")
    description: Optional[str] = Field(None, example="Task description")
    due_date: Optional[date] = Field(None, example="2025-06-01")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    status: Optional[str] = Field(None, example="completed")

class TaskOut(TaskBase):
    id: int
    status: str
    time_of_generation: datetime

    model_config = ConfigDict(from_attributes=True)

class TokenData(BaseModel):
    username: Optional[str] = None
