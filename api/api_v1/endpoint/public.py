from fastapi import APIRouter, Depends, HTTPException, status

from api import deps
from core.security import getPasswordHash, verifyPassword
from crud.crud_class import theClass
from crud.crud_profession import profession
from crud.crud_student import student
from crud.crud_teacher import teacher
from crud.crud_admin import admin
from crud.crud_dynamic import dynamic
from schemas.admin import Admin
from schemas.teacher import Teacher
from schemas.student import Student


public_router = r = APIRouter()


@r.get("/personal-info")
async def getPersonalInfo(
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser
    if scope == "student":
        classInfo = await theClass.get(db, user.class_id)
        professionInfo = await profession.get(db, classInfo.profession_id)
        return {
            "personal": Student.from_orm(user),
            "class": classInfo,
            "profession": professionInfo
        }
    elif scope == "teacher":
        return {"personal": Teacher.from_orm(user)}
    elif scope == "admin":
        return {"personal": Admin.from_orm(user)}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request",
        )


@r.put("/personal-info")
async def updatePersonalInfo(
    data: dict,
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser
    if scope == "student":
        await student.update(db, db_obj=user, obj_in={
            "email": data.get("email", user.email),
            "phone": data.get("phone", user.phone),
            "introduction": data.get("introduction", user.introduction),
            "avatar": data.get("avatar", user.avatar),
        })
    elif scope == "teacher":
        await teacher.update(db, db_obj=user, obj_in={
            "email": data.get("email", user.email),
            "phone": data.get("phone", user.phone),
            "introduction": data.get("introduction", user.introduction),
            "avatar": data.get("avatar", user.avatar),
        })
    elif scope == "admin":
        await admin.update(db, db_obj=user, obj_in={
            "email": data.get("email", user.email),
            "phone": data.get("phone", user.phone),
            "introduction": data.get("introduction", user.introduction),
            "avatar": data.get("avatar", user.avatar),
        })
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request",
        )


@r.put("/password")
async def updatePassword(
    data: dict,
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    oldPassword = data.get("old_password", None)
    newPassword = data.get("new_password", None)
    if oldPassword is None or newPassword is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request",
        )
    if not verifyPassword(oldPassword, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wrong old password",
        )
    if scope == "student":
        await student.update(db, db_obj=user, obj_in={
            "hashed_password": getPasswordHash(newPassword),
        })
    elif scope == "teacher":
        await teacher.update(db, db_obj=user, obj_in={
            "hashed_password": getPasswordHash(newPassword),
        })
    elif scope == "admin":
        await admin.update(db, db_obj=user, obj_in={
            "hashed_password": getPasswordHash(newPassword),
        })
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request",
        )


@r.get("/dynamic")
async def getDynamic(
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    dynamics = [{
        **item[0].to_dict(),
        "lesson_title": item[1].title,
    } for item in await dynamic.getMultiByUserIdAndScope(db, user.id, scope)]

    return {"dynamics": dynamics}
