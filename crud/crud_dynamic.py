from typing import Optional, Tuple, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.dynamic import Dynamic
from models.lesson import Lesson
from schemas.dynamic import DynamicCreate, DynamicUpdate


class CRUDDynamic(CRUDBase[Dynamic, DynamicCreate, DynamicUpdate]):
    async def insertMultiByStudentIds(
        self,
            db: AsyncSession,
            student_ids: list[int],
            lesson_id: int,
            content: str,
            created_time: int,
            scope: str,
    ) -> None:
        data = [Dynamic(**{
            "lesson_id": lesson_id,
            "content": content,
            "created_time": created_time,
            "scope": scope,
            "user_id": student_id,
        }) for student_id in student_ids]
        db.add_all(data)
        await db.commit()

    async def getMultiByUserIdAndScope(self, db: AsyncSession, user_id: str, scope: str) -> Optional[Tuple[Dynamic, Lesson]]:
        query = select(
            Dynamic, Lesson
        ).join(
            Lesson, Lesson.id == Dynamic.lesson_id
        ).where(
            Dynamic.scope == scope,
            Dynamic.user_id == user_id
        ).order_by(
            Dynamic.created_time.desc()
        ).limit(50)
        return (await db.execute(query)).all()


dynamic = CRUDDynamic(Dynamic)
