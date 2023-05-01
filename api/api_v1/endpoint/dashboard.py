from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api import deps
from crud.crud_task import task
from crud.crud_lesson import lesson
from crud.crud_dynamic import dynamic
from schemas.lesson import LessonBrief
from schemas.task import Task

dashboard_router = r = APIRouter()


@r.get("")
async def getDashboard(
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope == "teacher":
        lessons = await lesson.getMultiByTeacherId(db, user.id)
        uncompletedLessons = [
            LessonBrief.from_orm(l) for l in lessons if l.is_over == 0
        ]
        tasks = await task.getMultiWithUncheckExpiredStatusByTeacherId(db, user.id)
        uncheckedTasks = [{
            **t[0].to_dict(),
            "lesson_title": t[1].title
        } for t in tasks]
        dynamics = [{
            **item[0].to_dict(),
            "lesson_title": item[1].title,
        } for item in await dynamic.getMultiByUserIdAndScope(db, user.id, scope)]
        return {
            "uncompleted_tasks": uncheckedTasks,
            "uncompleted_lessons": uncompletedLessons,
            "dynamics": dynamics,
        }
    elif scope == "student":
        tasks = await task.getMultiByStudentId(db, user.id)
        uncompletedTasks = [{
            **t[0].to_dict(),
            "lesson_title": t[2].title
        } for t in tasks if t[1].status == "uncompleted"]
        lessons = await lesson.getMultiByClassId(db, user.class_id)
        uncompletedLessons = [
            LessonBrief.from_orm(l) for l in lessons if l.is_over == 0
        ]
        dynamics = [{
            **item[0].to_dict(),
            "lesson_title": item[1].title,
        } for item in await dynamic.getMultiByUserIdAndScope(db, user.id, scope)]
        return {
            "uncompleted_tasks": uncompletedTasks,
            "uncompleted_lessons": uncompletedLessons,
            "dynamics": dynamics,
        }
    else:
        raise HTTPException(status_code=403, detail="Forbidden")
