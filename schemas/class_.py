from pydantic import BaseModel, conint, constr


# Shared properties
class ClassBase(BaseModel):
    grade: conint(ge=1900, le=2100)
    profession_id: conint(ge=1)
    name: constr(min_length=1, max_length=32)


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
