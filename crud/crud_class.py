from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from crud.base import CRUDBase
from models.class_lesson_relation import ClassLessonRelation
from models.class_ import Class
from schemas.class_ import ClassCreate, ClassUpdate


class CRUDClass(CRUDBase[Class, ClassCreate, ClassUpdate]):
    async def getMultiByLessonId(self, db: AsyncSession, lesson_id: int) -> List[Class]:
        query = select(
            Class
        ).join(
            ClassLessonRelation
        ).filter(
            ClassLessonRelation.lesson_id == lesson_id
        )
        return (await db.execute(query)).scalars().all()

    async def getMultiByOptionalKeyword(
            self,
            db: AsyncSession,
            keyword: Optional[str] = None,
            offset: int = 0,
            limit: int = 10) -> list[Class]:
        if keyword == None or keyword == "":
            baseQuery = select(
                Class
            )
        else:
            baseQuery = select(
                Class
            ).where(
                Class.name.like(f"%{keyword}%")
            )

        totalQuery = select(func.count()).select_from(baseQuery)
        paginateQuery = baseQuery.offset(offset).limit(limit)

        return (await db.execute(paginateQuery)).scalars().all(), (await db.execute(totalQuery)).scalar()


class_ = CRUDClass(Class)
