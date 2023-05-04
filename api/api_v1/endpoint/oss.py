import random
import string
import time
from typing import List, Union
from fastapi import APIRouter, Body, Depends, File, HTTPException, Path, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import schemas
from api import deps
from core.config import settings
from core.oss import (
    copyObjects,
    deleteObjects,
    getShareFilePathAndType,
    getObjectList,
    getObjectStream,
    moveObjects,
    putObjects,
    recvShareFile,
    renameObject,
    ObjectConflictError,
    ObjectNotFoundError
)
from crud.crud_lesson import lesson
from crud.crud_sts import studentTaskStatus
from crud.crud_cs import cloudShare
from crud.crud_student import student
from crud.crud_teacher import teacher


oss_router = r = APIRouter()


def randomString(length: int = 4):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


class PublicFileUploadReturn(BaseModel):
    filename: str
    url: str


@r.put("/public/homework/{task_id}", response_model=List[PublicFileUploadReturn])
async def putHomeworkObject(
    task_id: int = Path(ge=1),
    files: List[UploadFile] = File(),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser
    if scope != "student" or not await studentTaskStatus.isStudentHasTaskStatus(db, user.id, task_id):
        raise HTTPException(
            status_code=403, detail="Only student can upload homework files.")

    ret = []
    for file in files:
        ext = file.filename.split(".")[-1]
        file.filename = f"{user.id}-{randomString()}.{ext}"
        ret.append({
            "filename": file.filename,
            "url": f"{settings.S3_API_ENDPOINT}/public/homework/{task_id}/{file.filename}"
        })

    try:
        await putObjects(oss, files, "/", "public", "homework", task_id)
    except ObjectConflictError as e:
        raise HTTPException(
            status_code=409, detail=f"Filename conflict: {e.object}")

    return ret


@r.delete("/public/homework/{task_id}")
async def deleteHomeworkObject(
    task_id: int = Path(ge=1),
    filenames: List[str] = Body(),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser

    if scope != "student" or not await studentTaskStatus.isStudentHasTaskStatus(db, user.id, task_id):
        raise HTTPException(
            status_code=403, detail="Only student can delete homework files.")

    for filename in filenames:
        filenameList = filename.split("-")
        if len(filenameList) and filenameList[0] != user.id:
            raise HTTPException(
                status_code=403, detail="You can only delete your homework files.")
    try:
        await deleteObjects(oss, filenames, "/", "public", "homework", task_id)
    except ObjectNotFoundError as e:
        raise HTTPException(
            status_code=404, detail=f"Object not found: {e.object}")


@ r.put("/public/courseware/{lesson_id}", response_model=List[PublicFileUploadReturn])
async def putCoursewareObject(
    lesson_id: int = Path(ge=1),
    files: List[UploadFile] = File(),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser
    if scope != "teacher" or not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You can only upload courseware to your own lesson")

    ret = []
    for file in files:
        ext = file.filename.split(".")[-1]
        file.filename = f"{user.id}-{randomString()}.{ext}"
        ret.append({
            "filename": file.filename,
            "url": f"{settings.S3_API_ENDPOINT}/public/courseware/{lesson_id}/{file.filename}"
        })

    try:
        await putObjects(oss, files, "/", "public", "courseware", lesson_id)
    except ObjectConflictError as e:
        raise HTTPException(
            status_code=409, detail=f"Filename conflict: {e.object}")

    return ret


@ r.delete("/public/courseware/{lesson_id}")
async def deleteCoursewareObject(
    lesson_id: int = Path(ge=1),
    filenames: List[str] = Body(),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser

    if scope != "teacher" or not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You can only delete courseware from your own lesson")

    for filename in filenames:
        filenameList = filename.split("-")
        if len(filenameList) or filenameList[0] != user.id:
            raise HTTPException(
                status_code=403, detail="You can only delete your own courseware")
    try:
        await deleteObjects(oss, filenames, "/", "public", "courseware", lesson_id)
    except ObjectNotFoundError as e:
        raise HTTPException(
            status_code=404, detail=f"Object not found: {e.object}")


@ r.put("/cloud/{area}/{user_id}/file")
async def putCloudObjects(
    area: str,
    user_id: Union[str, int],
    path: str = Query(),
    files: List[UploadFile] = File(),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser

    if not (scope == area and user_id == user.id) and \
        not (area == "lesson" and scope == "teacher" and
             await lesson.isTeacherHasLesson(db, user.id, user_id)):
        raise HTTPException(
            status_code=403, detail="You can only put from your own cloud")
    try:
        await putObjects(oss, files, path, "cloud", area, user_id)
    except ObjectConflictError as e:
        raise HTTPException(
            status_code=409, detail=f"Filename conflict: {e.object}")


@ r.delete("/cloud/{area}/{user_id}")
async def deleteCloudObjects(
    area: str,
    user_id: Union[str, int],
    path: str = Query(),
    names: List[str] = Body(),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser

    if not (scope == area and user_id == user.id) and \
        not (area == "lesson" and scope == "teacher" and
             await lesson.isTeacherHasLesson(db, user.id, user_id)):
        raise HTTPException(
            status_code=403, detail="You can only get from your own cloud")

    try:
        await deleteObjects(oss, names, path, "cloud", area, user_id)
    except ObjectNotFoundError as e:
        raise HTTPException(
            status_code=404, detail=f"Object not found: {e.object}")


@ r.get("/cloud/{area}/{user_id}/list")
async def getCloudObject(
    area: str,
    user_id: Union[str, int],
    path: str = Query(),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser

    if not (scope == area and user_id == user.id) and \
        not (area == "lesson" and scope == "student" and
             await lesson.isClassHasLesson(db, user.class_id, user.class_id)) and \
            not (area == "lesson" and scope == "teacher" and
                 await lesson.isTeacherHasLesson(db, user.id, user_id)):
        raise HTTPException(
            status_code=403, detail="You can only get from your own cloud")

    return await getObjectList(oss, path, "cloud", area, user_id)


@ r.get("/cloud/{area}/{user_id}/file")
async def downloadCloudObject(
    area: str,
    user_id: Union[str, int],
    path: str = Query(),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser

    if not (scope == area and user_id == user.id) and \
        not (area == "lesson" and scope == "student" and
             await lesson.isClassHasLesson(db, user.class_id, user.class_id)) and \
            not (area == "lesson" and scope == "teacher" and
                 await lesson.isTeacherHasLesson(db, user.id, user_id)):
        raise HTTPException(
            status_code=403, detail="You can only get from your own cloud")

    try:
        filename, body = await getObjectStream(oss, path, "cloud", area, user_id)
    except ObjectNotFoundError as e:
        raise HTTPException(
            status_code=404, detail=f"Object not found: {e.object}")

    return StreamingResponse(
        content=body,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={filename}".encode("utf-8").decode("latin-1")
        }
    )


@ r.put("/cloud/{area}/{user_id}/name")
async def renameCloudObject(
    area: str,
    user_id: Union[str, int],
    path: str = Query(),
    old_name: str = Body(embed=True),
    new_name: str = Body(embed=True),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser

    if not (scope == area and user_id == user.id) and \
        not (area == "lesson" and scope == "teacher" and
             await lesson.isTeacherHasLesson(db, user.id, user_id)):
        raise HTTPException(
            status_code=403, detail="You can only put from your own cloud")

    if old_name == new_name:
        return
    try:
        await renameObject(oss, path, old_name, new_name, "cloud", area, user_id)
    except ObjectNotFoundError as e:
        raise HTTPException(
            status_code=404, detail=f"Object not found: {e.object}")
    except ObjectConflictError as e:
        raise HTTPException(
            status_code=409, detail=f"Filename conflict: {e.object}")


@ r.put("/cloud/{area}/{user_id}/move")
async def moveCloudObjects(
    area: str,
    user_id: Union[str, int],
    src_path: str = Body(embed=True),
    dst_path: str = Body(embed=True),
    names: List[str] = Body(embed=True),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser

    if not (scope == area and user_id == user.id) and \
            not (area == "lesson" and scope == "teacher" and
                 await lesson.isTeacherHasLesson(db, user.id, user_id)):
        raise HTTPException(
            status_code=403, detail="You can only put from your own cloud")

    if src_path == dst_path:
        return

    try:
        await moveObjects(oss, names, src_path, dst_path, "cloud", area, user_id)
    except ObjectNotFoundError as e:
        raise HTTPException(
            status_code=404, detail=f"Object not found: {e.object}")
    except ObjectConflictError as e:
        raise HTTPException(
            status_code=409, detail=f"Filename conflict: {e.object}")


@ r.put("/cloud/{area}/{user_id}/copy")
async def copyCloudObjects(
    area: str,
    user_id: Union[str, int],
    src_path: str = Body(embed=True),
    dst_path: str = Body(embed=True),
    names: List[str] = Body(embed=True),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser

    if not (scope == area and user_id == user.id) and \
            not (area == "lesson" and scope == "teacher" and
                 await lesson.isTeacherHasLesson(db, user.id, user_id)):
        raise HTTPException(
            status_code=403, detail="You can only put from your own cloud")

    if src_path == dst_path:
        return

    try:
        await copyObjects(oss, names, src_path, dst_path, "cloud", area, user_id)
    except ObjectNotFoundError as e:
        raise HTTPException(
            status_code=404, detail=f"Object not found: {e.object}")
    except ObjectConflictError as e:
        raise HTTPException(
            status_code=409, detail=f"Filename conflict: {e.object}")


@ r.get("/cloud/share", response_model=schemas.CloudShare)
async def getSharedCloudObjects(
    share_id: str = Query(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser

    if not (scope == "student" and await student.get(db, user.id)) and\
            not (scope == "teacher" and await teacher.get(db, user.id)):
        raise HTTPException(status_code=403, detail="User not found")

    share = await cloudShare.getByKey(db, share_id)
    if not share:
        raise HTTPException(status_code=404, detail="Share object not found")

    if share.expire < int(time.time()):
        raise HTTPException(status_code=410, detail="Share object expired")

    return share


@ r.post("/cloud/{area}/{user_id}/share", response_model=schemas.CloudShare)
async def shareCloudObjects(
    area: str,
    user_id: str,
    cloudShareCreate: schemas.CloudShareCreate = Body(),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser

    if not (scope == area and user_id == user.id) and \
            not (area == "lesson" and scope == "teacher" and
                 await lesson.isTeacherHasLesson(db, user.id, user_id)):
        raise HTTPException(
            status_code=403, detail="You can only put from your own cloud")

    try:
        path, type = await getShareFilePathAndType(oss, cloudShareCreate.path, "cloud", area, user_id)
    except ObjectNotFoundError as e:
        raise HTTPException(
            status_code=404, detail=f"Object not found: {e.object}")

    filename = path.split("/")[-1]

    share = await cloudShare.getByPath(db, path)
    if share and share.expire > int(time.time()):
        copy = schemas.CloudShare().from_orm(share)
        copy.expire = int(time.time()) + cloudShareCreate.expire
        await cloudShare.update(db, db_obj=share, obj_in=copy)
        return copy
    else:
        key = "".join(random.choices(
            string.ascii_letters + string.digits, k=6
        ))
        share = await cloudShare.create(
            db, obj_in={
                "key": key,
                "path": path,
                "name": filename if filename else "file",
                "type": type,
                "expire": int(time.time()) + cloudShareCreate.expire
            })
        return share


@ r.put("/cloud/{area}/{user_id}/share/recv")
async def recvSharedCloudObjects(
    area: str,
    user_id: str,
    share_id: str = Body(embed=True),
    path: str = Body(embed=True),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser

    if not (scope == area and user_id == user.id) and \
            not (area == "lesson" and scope == "teacher" and
                 await lesson.isTeacherHasLesson(db, user.id, user_id)):
        raise HTTPException(
            status_code=403, detail="You can only put from your own cloud")

    share = await cloudShare.getByKey(db, share_id)
    if not share:
        raise HTTPException(status_code=404, detail="Share object not found")

    if share.expire < int(time.time()):
        raise HTTPException(status_code=410, detail="Share object expired")

    try:
        await recvShareFile(oss, share.path, share.name, path, "cloud", area, user_id)
    except ObjectNotFoundError as e:
        raise HTTPException(
            status_code=404, detail=f"Object not found: {e.object}")
    except ObjectConflictError as e:
        raise HTTPException(
            status_code=409, detail=f"Filename conflict: {e.object}")
