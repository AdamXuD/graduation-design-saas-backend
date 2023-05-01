

from pydantic import BaseModel


class LessonRecordBase(BaseModel):
    lesson_id: int
    time: int
    data: str


class LessonRecordUpdate(LessonRecordBase):
    id: int


class LessonRecordCreate(LessonRecordBase):
    pass


# Properties shared by models stored in DB
class LessonRecordInDBBase(LessonRecordBase):
    id: int

    class Config:
        orm_mode = True


# Properties to return to client
class LessonRecord(LessonRecordInDBBase):
    pass


# Properties properties stored in DB
class LessonInDB(LessonRecordInDBBase):
    pass
