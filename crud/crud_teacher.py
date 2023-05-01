from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from crud.base import CRUDBase
from models.teacher import Teacher
from schemas.teacher import TeacherCreate, TeacherUpdate
from core import security


class CRUDTeacher(CRUDBase[Teacher, TeacherCreate, TeacherUpdate]):
    async def authenticate(self, db: AsyncSession, id: str, password: str) -> Optional[Teacher]:
        teacher = await self.get(db, id=id)
        if not teacher:
            return None
        if not security.verifyPassword(password, teacher.hashed_password):
            return None
        return teacher

    async def getMultiByOptionalKeyword(
            self,
            db: AsyncSession,
            keyword: Optional[str] = None,
            offset: int = 0,
            limit: int = 10) -> list[Teacher]:
        if keyword == None or keyword == "":
            baseQuery = select(
                Teacher
            )
        else:
            baseQuery = select(
                Teacher
            ).where(
                Teacher.name.like(f"%{keyword}%") |
                Teacher.id.like(f"%{keyword}%")
            )

        totalQuery = select(func.count()).select_from(baseQuery)
        paginateQuery = baseQuery.offset(offset).limit(limit)

        return (await db.execute(paginateQuery)).scalars().all(), (await db.execute(totalQuery)).scalar()


teacher = CRUDTeacher(Teacher)
