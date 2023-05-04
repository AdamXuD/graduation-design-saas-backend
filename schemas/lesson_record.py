

from pydantic import BaseModel


class LessonRecordBase(BaseModel):
    lesson_id: int
    time: int


class LessonRecordUpdate(LessonRecordBase):
    data: str


class LessonRecordCreate(LessonRecordBase):
    data: str


# Properties shared by models stored in DB
class LessonRecordInDBBase(LessonRecordBase):
    id: int

    class Config:
        orm_mode = True


# Properties to return to client
class LessonRecord(LessonRecordInDBBase):
    data: str


class LessonRecordBrief(LessonRecordInDBBase):
    pass


# Properties properties stored in DB
class LessonInDB(LessonRecordInDBBase):
    pass
