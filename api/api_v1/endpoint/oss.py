import pathlib
import random
import re
import string
import time
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, File, HTTPException, Path, Query, UploadFile
from fastapi.responses import StreamingResponse

from api import deps
from core.config import MINIO_ENDPOINT
from core.oss import copyObjects, deleteObjects, getShareFilePathAndType, getObjectList, getObjectStream, moveObjects, putObjects, recvShareFile, renameObject
from crud.crud_task import task
from crud.crud_lesson import lesson
from crud.crud_sts import studentTaskStatus
from crud.crud_cs import cloudShare
from crud.crud_student import student
from crud.crud_teacher import teacher
from schemas.cloud_share import CloudShare


oss_router = r = APIRouter()


def randomString(length: int = 4):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


@r.put("/public/homework/{task_id}")
async def putHomeworkObject(
    task_id: str,
    files: List[UploadFile] = File(),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser
    if scope != "student" or not await studentTaskStatus.isStudentHasTaskStatus(db, task_id, user.id):
        raise HTTPException(
            status_code=403, detail="Only student can upload homework files.")

    ret = []
    for file in files:
        ext = file.filename.split(".")[-1]
        file.filename = f"{user.id}-{randomString()}.{ext}"
        ret.append({
            "filename": file.filename,
            "url": f"{MINIO_ENDPOINT}/public/homework/{task_id}/{file.filename}"
        })

    await putObjects(oss, files, "/", "public", "homework", task_id)
    return {"files": ret}


@r.delete("/public/homework/{task_id}")
async def deleteHomeworkObject(
    task_id: str,
    filenames: List[str] = Body(embed=True),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
    currentUser=Depends(deps.getCurrentUserAndScope)
):
    user, scope = currentUser

    if scope != "student" or not await studentTaskStatus.isStudentHasTaskStatus(db, task_id, user.id):
        raise HTTPException(
            status_code=403, detail="Only student can delete homework files.")

    for filename in filenames:
        filenameList = filename.split("-")
        if len(filenameList) and filenameList[0] != user.id:
            raise HTTPException(
                status_code=403, detail="You can only delete your homework files.")

    await deleteObjects(oss, filenames, "/", "public", "homework", task_id)


@ r.put("/public/courseware/{lesson_id}")
async def putCoursewareObject(
    lesson_id: str,
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
            "url": f"{MINIO_ENDPOINT}/public/courseware/{lesson_id}/{file.filename}"
        })
    await putObjects(oss, files, "/", "public", "courseware", lesson_id)
    return {"files": ret}


@ r.delete("/public/courseware/{lesson_id}")
async def deleteCoursewareObject(
    lesson_id: str,
    filenames: List[str] = Body(embed=True),
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

    await deleteObjects(oss, filenames, "/", "public", "courseware", lesson_id)


@ r.put("/cloud/{area}/{user_id}/file")
async def putCloudObjects(
    area: str,
    user_id: str,
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

    await putObjects(oss, files, path, "cloud", area, user_id)


@ r.delete("/cloud/{area}/{user_id}")
async def deleteCloudObjects(
    area: str,
    user_id: str,
    path: str = Query(),
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
            status_code=403, detail="You can only get from your own cloud")

    await deleteObjects(oss, names, path, "cloud", area, user_id)


@ r.get("/cloud/{area}/{user_id}/list")
async def getCloudObject(
    area: str,
    user_id: str,
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
    l = await getObjectList(oss, path, "cloud", area, user_id)
    return {"list": l}


@ r.get("/cloud/{area}/{user_id}/file")
async def downloadCloudObject(
    area: str,
    user_id: str,
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

    filename, body = await getObjectStream(oss, path, "cloud", area, user_id)

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
    user_id: str,
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

    await renameObject(oss, path, old_name, new_name, "cloud", area, user_id)


@ r.put("/cloud/{area}/{user_id}/move")
async def moveCloudObjects(
    area: str,
    user_id: str,
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
    await moveObjects(oss, names, src_path, dst_path, "cloud", area, user_id)


@ r.put("/cloud/{area}/{user_id}/copy")
async def copyCloudObjects(
    area: str,
    user_id: str,
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

    await copyObjects(oss, names, src_path, dst_path, "cloud", area, user_id)


@ r.get("/cloud/share")
async def getSharedCloudObjects(
    share_id: str = Query(),
    db=Depends(deps.getDB),
    oss=Depends(deps.getOSS),
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

    return {"share": share}


@ r.post("/cloud/{area}/{user_id}/share")
async def shareCloudObjects(
    area: str,
    user_id: str,
    path: str = Body(embed=True),
    expire: int = Body(embed=True),
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

    path, type = await getShareFilePathAndType(oss, path, "cloud", area, user_id)
    filename = path.split("/")[-1]

    share = await cloudShare.getByPath(db, path)
    if share and share.expire > int(time.time()):
        copy = CloudShare().from_orm(share)
        copy.expire = int(time.time()) + expire
        await cloudShare.update(db, db_obj=share, obj_in=copy)
        return {"share": copy}
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
                "expire": int(time.time()) + expire
            })
        return {"share": share}


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

    await recvShareFile(oss, share.path, share.name, path, "cloud", area, user_id)
