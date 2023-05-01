from pydantic import BaseModel


# Shared properties
class LessonBase(BaseModel):
    thumbnail: str
    title: str
    teacher_id: str
    year: int
    term: int
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
