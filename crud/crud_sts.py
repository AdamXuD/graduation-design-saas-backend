from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional


from models.student_task_status import StudentTaskStatus
from crud.base import CRUDBase
from models.student import Student
from schemas.student_task_status import StudentTaskStatusCreate, StudentTaskStatusUpdate


class CRUDStudentTaskStatus(CRUDBase[StudentTaskStatus, StudentTaskStatusCreate, StudentTaskStatusUpdate]):
    async def getByStudentIdAndTaskId(self, db: AsyncSession, student_id: str, task_id: int) -> Optional[StudentTaskStatus]:
        query = select(
            StudentTaskStatus
        ).where(
            StudentTaskStatus.student_id == student_id,
            StudentTaskStatus.task_id == task_id
        )
        return (await db.execute(query)).scalars().first()

    async def insertMultiByStudentIdsAndTaskId(self, db: AsyncSession, student_ids: list[int], task_id: int):
        data = [StudentTaskStatus(**{
            "student_id": student_id,
            "task_id": task_id,
            "status": "uncompleted",
            "text": "",
            "files": "[]",
            "score": -1,
        }) for student_id in student_ids]
        db.add_all(data)
        await db.commit()

    async def updateMultiToExpiredByTaskId(self, db: AsyncSession, task_id: int):
        query = update(StudentTaskStatus).where(
            StudentTaskStatus.task_id == task_id,
            StudentTaskStatus.status != "checked"
        ).values(status="expired")
        await db.execute(query)
        await db.commit()

    async def updateMultiExpiredToOtherByTaskId(self, db: AsyncSession, task_id: int):
        query = update(StudentTaskStatus).where(
            StudentTaskStatus.task_id == task_id,
            StudentTaskStatus.status == "expired",
            StudentTaskStatus.score == -1,
            ((StudentTaskStatus.text != "") | (StudentTaskStatus.files != "[]"))
        ).values(status="completed")
        await db.execute(query)
        query = update(StudentTaskStatus).where(
            StudentTaskStatus.task_id == task_id,
            StudentTaskStatus.status == "expired",
            StudentTaskStatus.score == -1,
            ((StudentTaskStatus.text == "") | (StudentTaskStatus.files == "[]"))
        ).values(status="uncompleted")
        await db.execute(query)
        query = update(StudentTaskStatus).where(
            StudentTaskStatus.task_id == task_id,
            StudentTaskStatus.status == "expired",
            StudentTaskStatus.score != -1
        ).values(status="checked")
        await db.execute(query)
        await db.commit()

    async def getMultiByTaskId(self, db: AsyncSession, task_id: int) -> List[StudentTaskStatus]:
        query = select(
            StudentTaskStatus
        ).where(
            StudentTaskStatus.task_id == task_id
        )
        return (await db.execute(query)).scalars().all()

    async def deleteMultiByTaskId(self, db: AsyncSession, task_id: int):
        query = delete(StudentTaskStatus).where(
            StudentTaskStatus.task_id == task_id
        )
        await db.execute(query)

    async def isStudentHasTaskStatus(self, db: AsyncSession, student_id: int, task_id: int) -> bool:
        query = select(
            StudentTaskStatus
        ).where(
            StudentTaskStatus.student_id == student_id,
            StudentTaskStatus.task_id == task_id
        )
        return (await db.execute(query)).scalars().first() is not None


studentTaskStatus = CRUDStudentTaskStatus(StudentTaskStatus)
