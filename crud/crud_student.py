from core import security
from models.class_lesson_relation import ClassLessonRelation
from models.class_ import Class
from schemas.student import StudentCreate, StudentUpdate
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from crud.base import CRUDBase
from models.student import Student


class CRUDStudent(CRUDBase[Student, StudentCreate, StudentUpdate]):
    async def authenticate(self, db: AsyncSession, id: str, password: str) -> Optional[Student]:
        student = await self.get(db, id=id)
        if not student:
            return None
        if not security.verifyPassword(password, student.hashed_password):
            return None
        return student

    async def getRandomStudentsByLessonId(self, db: AsyncSession, lesson_id: int, count: int = 1) -> List[Student]:
        query = select(
            Student
        ).join(
            Class, Class.id == Student.class_id
        ).join(
            ClassLessonRelation, ClassLessonRelation.class_id == Class.id
        ).where(
            ClassLessonRelation.lesson_id == lesson_id
        ).order_by(
            func.rand()
        ).limit(count)

        return (await db.execute(query)).scalars().all()

    async def getMultiByClassId(self, db: AsyncSession, class_id: int) -> List[Student]:
        query = select(
            Student
        ).where(
            Student.class_id == class_id
        )
        return (await db.execute(query)).scalars().all()

    async def getMultiByOptionalKeyword(
            self,
            db: AsyncSession,
            keyword: Optional[str] = None,
            offset: int = 0,
            limit: int = 10) -> list[Student]:
        if keyword == None or keyword == "":
            baseQuery = select(
                Student
            ).offset(offset).limit(limit)
        else:
            baseQuery = select(
                Student
            ).where(
                Student.name.like(f"%{keyword}%") |
                Student.id.like(f"%{keyword}%")
            ).offset(offset).limit(limit)

        totalQuery = select(func.count()).select_from(baseQuery)
        paginateQuery = baseQuery.offset(offset).limit(limit)

        return (await db.execute(paginateQuery)).scalars().all(), (await db.execute(totalQuery)).scalar()


student = CRUDStudent(Student)
