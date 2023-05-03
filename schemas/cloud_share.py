

from pydantic import BaseModel


class CloudShareBase(BaseModel):
    path: str
    expire: int


class CloudShareUpdate(CloudShareBase):
    pass


class CloudShareCreate(CloudShareBase):
    pass


# Properties shared by models stored in DB
class CloudShareInDBBase(CloudShareBase):
    id: int
    key: str
    type: str
    name: str

    class Config:
        orm_mode = True


# Properties to return to client
class CloudShare(CloudShareInDBBase):
    pass


# Properties properties stored in DB
class LessonInDB(CloudShareInDBBase):
    pass
