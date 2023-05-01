import time
from sqlalchemy.ext.asyncio import AsyncSession

from crud.crud_dynamic import dynamic
from crud.crud_class import theClass
from crud.crud_student import student


async def sendDynamicToStudent(
    db: AsyncSession,
    student_id: str,
    lesson_id: int,
    content: str,
):
    await dynamic.create(db, obj_in={
        "lesson_id": lesson_id,
        "content": content,
        "created_time": int(time.time()),
        "scope": "student",
        "user_id": student_id
    })


async def sendDynamicToTeacher(
    db: AsyncSession,
    teacher_id: str,
    lesson_id: int,
    content: str,
):
    await dynamic.create(db, obj_in={
        "lesson_id": lesson_id,
        "content": content,
        "created_time": int(time.time()),
        "scope": "teacher",
        "user_id": teacher_id
    })


async def boardcastDynamicToLesson(
    db: AsyncSession,
    lesson_id: int,
    content: str,
):
    class_ids = [theClass.id for theClass in await theClass.getMultiByLessonId(db, lesson_id)]
    student_ids = []
    for class_id in class_ids:
        student_ids += [student.id for student in await student.getMultiByClassId(db, class_id)]
    await dynamic.insertMultiByStudentIds(
        db, student_ids, lesson_id, content,
        int(time.time()), "student"
    )
