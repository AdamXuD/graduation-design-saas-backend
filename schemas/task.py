from pydantic import BaseModel


# Shared properties
class TaskBase(BaseModel):
    title: str
    description: str
    deadline: int


# Properties to receive on item creation
class TaskCreate(TaskBase):
    pass


# Properties to receive on item update
class TaskUpdate(TaskBase):
    pass


# Properties shared by models stored in DB
class TaskInDBBase(TaskBase):
    id: int
    lesson_id: int
    created_time: int

    class Config:
        orm_mode = True


# Properties to return to client
class Task(TaskInDBBase):
    pass


# Properties properties stored in DB
class TaskInDB(TaskInDBBase):
    pass
