

from pydantic import BaseModel


# Shared properties
class DynamicBase(BaseModel):
    lesson_id: int
    content: str
    created_time: int
    scope: str
    user_id: str


# Properties to receive on item creation
class DynamicUpdate(DynamicBase):
    pass


# Properties to receive on item update
class DynamicCreate(DynamicBase):
    pass


# Properties shared by models stored in DB
class DynamicInDBBase(DynamicBase):
    id: int

    class Config:
        orm_mode = True


# Properties to return to client
class Dynamic(DynamicInDBBase):
    pass


# Properties properties stored in DB
class DynamicInDB(DynamicInDBBase):
    pass
