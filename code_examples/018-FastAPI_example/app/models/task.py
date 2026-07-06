# Task model definition
from pydantic import BaseModel, Field

# the "perfect" task
class TaskOut(BaseModel):
    name: str
    description: str
    status: bool
    id: int

# DTO - Data Transfer Object
# a type that has a predictable shape for use with the API

# the "new" task
class TaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, description="Short task name")
    description: str = Field(default="", max_length=1000)
    status: bool = Field(default=False, description="Is the task completed?")

# the "udated" task
class TaskUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    status: bool = False
