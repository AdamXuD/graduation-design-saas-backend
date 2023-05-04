from pydantic import BaseModel, conint, constr


class StudentBase(BaseModel):
    id: constr(min_length=10, max_length=10)
    name: constr(min_length=1, max_length=16)
    class_id: conint(ge=1)
    email: str
    phone:  str
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
