from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession


from models.class_lesson_relation import ClassLessonRelation
from crud.base import CRUDBase


class CRUDClassLessonRelation(CRUDBase[ClassLessonRelation, None, None]):
    async def updateLessonClasses(self, db: AsyncSession, lesson_id: int, class_ids: list[int]):
        query = delete(ClassLessonRelation).where(
            ClassLessonRelation.lesson_id == lesson_id,
            ClassLessonRelation.class_id.notin_(class_ids)
        )
        await db.execute(query)
        query = insert(ClassLessonRelation).prefix_with(
            'IGNORE'
        ).values([{
            "lesson_id": lesson_id,
            "class_id": class_id
        } for class_id in class_ids])
        await db.execute(query)
        await db.commit()


classLessonRelation = CRUDClassLessonRelation(ClassLessonRelation)
