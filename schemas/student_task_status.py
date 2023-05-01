from pydantic import BaseModel
from typing import List


# Shared properties
class StudentTaskStatusBase(BaseModel):
    text: str
    files: str


# Properties to receive on item creation
class StudentTaskStatusCreate(StudentTaskStatusBase):
    pass


# Properties to receive on item update
class StudentTaskStatusUpdate(StudentTaskStatusBase):
    pass


# Properties shared by models stored in DB
class StudentTaskStatusInDBBase(StudentTaskStatusBase):
    id: int
    student_id: int
    task_id: int
    status: str
    score: int

    class Config:
        orm_mode = True


# Properties to return to client
class StudentTaskStatus(StudentTaskStatusInDBBase):
    pass


# Properties properties stored in DB
class StudentTaskStatusInDB(StudentTaskStatusInDBBase):
    pass
