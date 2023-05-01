from pydantic import BaseModel


# Shared properties
class TeacherBase(BaseModel):
    id: str
    name: str
    phone: str
    email: str
    introduction: str
    avatar: str


# Properties to receive on item creation
class TeacherCreate(TeacherBase):
    pass


# Properties to receive on item update
class TeacherUpdate(TeacherBase):
    reset_password: bool


# Properties shared by models stored in DB
class TeacherInDBBase(TeacherBase):
    pass

    class Config:
        orm_mode = True


# Properties to return to client
class Teacher(TeacherInDBBase):
    pass


# Properties properties stored in DB
class TeacherInDB(TeacherInDBBase):
    hashed_password: str
