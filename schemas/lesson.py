from pydantic import BaseModel, conint, constr


# Shared properties
class LessonBase(BaseModel):
    thumbnail: str
    title: constr(min_length=1, max_length=32)
    teacher_id: constr(min_length=10, max_length=10)
    year: conint(ge=1900, le=2100)
    term: conint(ge=1, le=2)
    is_over: bool


# Properties to receive on item creation
class LessonCreate(LessonBase):
    notice: str
    courseware: str


# Properties to receive on item update
class LessonUpdate(LessonBase):
    notice: str
    courseware: str


# Properties shared by models stored in DB
class LessonInDBBase(LessonBase):
    id: int

    class Config:
        orm_mode = True


# Properties to return to client briefly
class LessonBrief(LessonInDBBase):
    pass


# Properties to return to client
class Lesson(LessonInDBBase):
    notice: str
    courseware: str


# Properties properties stored in DB
class LessonInDB(LessonInDBBase):
    notice: str
    courseware: str
