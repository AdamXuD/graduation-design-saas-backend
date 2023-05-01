from pydantic import BaseModel


class StudentBase(BaseModel):
    id: str
    name: str
    class_id: str
    email: str
    phone: str
    introduction: str
    avatar: str


class StudentCreate(StudentBase):
    pass


class StudentUpdate(StudentBase):
    reset_password: bool


# Properties shared by models stored in DB
class StudentInDBBase(StudentBase):
    pass

    class Config:
        orm_mode = True


# Properties to return to client
class Student(StudentInDBBase):
    pass


# Properties properties stored in DB
class StudentInDB(StudentInDBBase):
    hashed_password: str
