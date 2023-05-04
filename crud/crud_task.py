import time
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from crud.base import CRUDBase
from models.lesson import Lesson
from models.task import Task
from models.student_task_status import StudentTaskStatus
from models.teacher import Teacher
from schemas.task import TaskCreate, TaskUpdate


class CRUDTask(CRUDBase[Task, TaskCreate, TaskUpdate]):
    async def getMultiByStudentId(self, db: AsyncSession, student_id: int) -> Optional[List[Task]]:
        query = select(
            Task, StudentTaskStatus, Lesson
        ).join(
            StudentTaskStatus
        ).join(
            Lesson
        ).where(
            StudentTaskStatus.student_id == student_id,
        )
        return (await db.execute(query)).all()

    async def getMultiByLessonId(self, db: AsyncSession, lesson_id: int) -> Optional[Task]:
        query = select(
            Task
        ).where(
            Task.lesson_id == lesson_id
        )
        return (await db.execute(query)).scalars().all()

    async def getMultiStatusByTaskIds(self, db: AsyncSession, task_ids: list[int], student_id: int) -> Optional[StudentTaskStatus]:
        query = select(
            StudentTaskStatus
        ).where(
            StudentTaskStatus.task_id.in_(task_ids),
            StudentTaskStatus.student_id == student_id
        )
        return (await db.execute(query)).scalars().all()

    async def isTeacherHasTask(self, db: AsyncSession, teacher_id: str, task_id: int) -> bool:
        query = select(
            Task
        ).join(
            Lesson
        ).where(
            Task.id == task_id,
            Lesson.teacher_id == teacher_id
        )
        return (await db.execute(query)).scalars().first() is not None

    async def getMultiWithUncheckExpiredStatusByTeacherId(self, db: AsyncSession, teacher_id: str) -> List[Task]:
        query = select(
            Task, Lesson
        ).join(
            StudentTaskStatus, Task.id == StudentTaskStatus.task_id
        ).join(
            Lesson, Lesson.id == Task.lesson_id
        ).join(
            Teacher, Teacher.id == Lesson.teacher_id
        ).where(
            StudentTaskStatus.status != 'checked',
            Task.deadline < int(time.time()),
            Teacher.id == teacher_id
        ).group_by(
            Task.id
        )
        return (await db.execute(query)).all()


task = CRUDTask(Task)
