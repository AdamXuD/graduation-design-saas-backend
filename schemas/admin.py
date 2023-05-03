from pydantic import BaseModel


# Shared properties
class AdminBase(BaseModel):
    id: str
    name: str
    phone: str
    email: str
    introduction: str
    avatar: str


# Properties to receive on item creation
class AdminCreate(AdminBase):
    pass


# Properties to receive on item update
class AdminUpdate(AdminBase):
    reset_password: bool


# Properties shared by models stored in DB
class AdminInDBBase(AdminBase):
    pass

    class Config:
        orm_mode = True


# Properties to return to client
class Admin(AdminInDBBase):
    pass


# Properties properties stored in DB
class AdminInDB(AdminInDBBase):
    hashed_password: str
