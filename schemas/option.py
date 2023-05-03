from pydantic import BaseModel


# Shared properties
class OptionBase(BaseModel):
    value: str


# Properties to receive on item creation
class OptionCreate(OptionBase):
    pass


# Properties to receive on item update
class OptionUpdate(OptionBase):
    pass


# Properties shared by models stored in DB
class OptionInDBBase(OptionBase):
    key: str

    class Config:
        orm_mode = True


# Properties to return to client
class Option(OptionInDBBase):
    pass


# Properties properties stored in DB
class OptionInDB(OptionInDBBase):
    id: int
    key: str
