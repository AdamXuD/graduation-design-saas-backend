from pydantic import BaseModel, constr


# Shared properties
class ProfessionBase(BaseModel):
    name: constr(min_length=1, max_length=24)


# Properties to receive on item creation
class ProfessionCreate(ProfessionBase):
    pass


# Properties to receive on item update
class ProfessionUpdate(ProfessionBase):
    pass


# Properties shared by models stored in DB
class ProfessionInDBBase(ProfessionBase):
    id: int

    class Config:
        orm_mode = True


# Properties to return to client
class Profession(ProfessionInDBBase):
    pass


# Properties properties stored in DB
class ProfessionInDB(ProfessionInDBBase):
    pass
