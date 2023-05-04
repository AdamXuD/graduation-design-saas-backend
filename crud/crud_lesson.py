from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from crud.base import CRUDBase
from models.class_lesson_relation import ClassLessonRelation
from models.lesson import Lesson
from models.student import Student
from schemas.lesson import LessonCreate, LessonUpdate


class CRUDLesson(CRUDBase[Lesson, LessonCreate, LessonUpdate]):
    async def getMultiByClassId(self, db: AsyncSession, class_id: int) -> Optional[List[Lesson]]:
        query = select(
            Lesson
        ).join(
            ClassLessonRelation
        ).filter(
            ClassLessonRelation.class_id == class_id
        )
        return (await db.execute(query)).scalars().all()

    async def getMultiByTeacherId(self, db: AsyncSession, teacher_id: int) -> Optional[List[Lesson]]:
        query = select(
            Lesson
        ).filter(
            Lesson.teacher_id == teacher_id
        )
        return (await db.execute(query)).scalars().all()

    async def isClassHasLesson(self, db: AsyncSession, class_id: int, lesson_id: int) -> bool:
        query = select(
            ClassLessonRelation
        ).filter(
            ClassLessonRelation.class_id == class_id,
            ClassLessonRelation.lesson_id == lesson_id
        )
        return (await db.execute(query)).scalars().first() is not None

    async def isTeacherHasLesson(self, db: AsyncSession, teacher_id: int, lesson_id: int) -> bool:
        query = select(
            Lesson
        ).filter(
            Lesson.teacher_id == teacher_id,
            Lesson.id == lesson_id
        )
        return (await db.execute(query)).scalars().first() is not None

    async def getMultiByOptionalKeyword(
            self,
            db: AsyncSession,
            keyword: Optional[str] = None,
            offset: int = 0,
            limit: int = 10) -> Optional[Tuple[List[Lesson], int]]:
        if keyword == None or keyword == "":
            baseQuery = select(
                Lesson
            )
        elif keyword.isdigit():
            baseQuery = select(
                Lesson
            ).where(
                Lesson.year == int(keyword)
            )
        else:
            baseQuery = select(
                Lesson
            ).where(
                Lesson.title.like(f"%{keyword}%") |
                Lesson.teacher_id.like(f"%{keyword}%")
            )

        totalQuery = select(func.count()).select_from(baseQuery)
        paginateQuery = baseQuery.offset(offset).limit(limit)

        return (await db.execute(paginateQuery)).scalars().all(), (await db.execute(totalQuery)).scalar()


lesson = CRUDLesson(Lesson)
