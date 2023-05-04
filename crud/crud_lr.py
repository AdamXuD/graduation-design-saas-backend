from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from crud.base import CRUDBase
from models.lesson_record import LessonRecord
from schemas.lesson_record import LessonRecordCreate, LessonRecordUpdate


class CRUDLessonRecord(CRUDBase[LessonRecord, LessonRecordCreate, LessonRecordUpdate]):
    async def getMultiByLessonId(self, db: AsyncSession, lesson_id: int) -> Optional[List[LessonRecord]]:
        query = select(
            LessonRecord
        ).filter(
            LessonRecord.lesson_id == lesson_id
        )
        return (await db.execute(query)).scalars().all()


lessonRecord = CRUDLessonRecord(LessonRecord)
