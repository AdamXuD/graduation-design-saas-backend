from typing import List, Optional, Union
from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel

import schemas
from api import deps
from core.security import getPasswordHash, verifyPassword
from crud.crud_class import class_
from crud.crud_profession import profession
from crud.crud_student import student
from crud.crud_teacher import teacher
from crud.crud_admin import admin
from crud.crud_dynamic import dynamic
from crud.crud_lesson import lesson
from crud.crud_task import task


public_router = r = APIRouter()


class TaskWithLessonTitle(schemas.Task):
    lesson_title: str


class DynamicWithLessonTitle(schemas.Dynamic):
    lesson_title: str


class DashboardReturn(BaseModel):
    uncompleted_lessons: List[schemas.LessonBrief]
    uncompleted_tasks: List[TaskWithLessonTitle]
    dynamics: List[DynamicWithLessonTitle]


@r.get("/dashboard", response_model=DashboardReturn)
async def getDashboard(
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope == "teacher":
        uncompletedLessons = [
            l for l in await lesson.getMultiByTeacherId(db, user.id) if l.is_over == 0]
        uncheckedTasks = [{
            **t[0].to_dict(),
            "lesson_title": t[1].title
        } for t in await task.getMultiWithUncheckExpiredStatusByTeacherId(db, user.id)]
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
        uncompletedLessons = [
            l for l in await lesson.getMultiByClassId(db, user.class_id) if l.is_over == 0]
        uncompletedTasks = [{
            **t[0].to_dict(),
            "lesson_title": t[2].title
        } for t in await task.getMultiByStudentId(db, user.id) if t[1].status == "uncompleted"]
        dynamics = [{
            **item[0].to_dict(),
            "lesson_title": item[1].title,
        } for item in await dynamic.getMultiByUserIdAndScope(db, user.id, scope)]
        return {
            "uncompleted_tasks": uncompletedTasks,
            "uncompleted_lessons": uncompletedLessons,
            "dynamics": dynamics,
        }
    elif scope == "admin":
        return {
            "uncompleted_tasks": [],
            "uncompleted_lessons": [],
            "dynamics": [],
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request",
        )


class PersonalReturn(BaseModel):
    personal: Union[schemas.Student, schemas.Teacher, schemas.Admin]
    class_: Optional[schemas.Class]
    profession: Optional[schemas.Profession]


@r.get("/personal-info", response_model=PersonalReturn)
async def getPersonalInfo(
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser
    if scope == "student":
        classInfo = await class_.get(db, user.class_id)
        professionInfo = await profession.get(db, classInfo.profession_id)
        return {
            "personal": user,
            "class": classInfo,
            "profession": professionInfo
        }
    elif scope == "teacher":
        return {"personal": user}
    elif scope == "admin":
        return {"personal": user}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request",
        )


class UserInfoUpdate(BaseModel):
    email: str
    phone: str
    introduction: str
    avatar: str


@r.put("/personal-info")
async def updatePersonalInfo(
    info: UserInfoUpdate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser
    crudObj = None
    if scope == "student":
        crudObj = student
    elif scope == "teacher":
        crudObj = teacher
    elif scope == "admin":
        crudObj = admin
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request",
        )
    await crudObj.update(db, db_obj=user, obj_in={
        "email": info.email,
        "phone": info.phone,
        "introduction": info.introduction,
        "avatar": info.avatar,
    })


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str


@r.put("/password")
async def updatePassword(
    data: PasswordUpdate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if not verifyPassword(data.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wrong old password",
        )
    crudObj = None
    if scope == "student":
        crudObj = student
    elif scope == "teacher":
        crudObj = teacher
    elif scope == "admin":
        crudObj = admin
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request",
        )
    await crudObj.update(db, db_obj=user, obj_in={
        "hashed_password": getPasswordHash(data.new_password),
    })


@r.get("/dynamic/list", response_model=List[DynamicWithLessonTitle])
async def getDynamics(
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    dynamics = [{
        **item[0].to_dict(),
        "lesson_title": item[1].title,
    } for item in await dynamic.getMultiByUserIdAndScope(db, user.id, scope)]

    return dynamics
