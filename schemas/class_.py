from pydantic import BaseModel


# Shared properties
class ClassBase(BaseModel):
    grade: int
    profession_id: int
    name: str


# Properties to receive on item creation
class ClassCreate(ClassBase):
    pass


# Properties to receive on item update
class ClassUpdate(ClassBase):
    pass


# Properties shared by models stored in DB
class ClassInDBBase(ClassBase):
    id: int

    class Config:
        orm_mode = True


# Properties to return to client
class Class(ClassInDBBase):
    pass


# Properties properties stored in DB
class ClassInDB(ClassInDBBase):
    pass
