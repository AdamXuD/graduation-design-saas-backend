import ujson
import time
from typing import List, Optional
from pydantic import BaseModel
from redis.asyncio import Redis
from fastapi import APIRouter, Body, Depends, HTTPException

import schemas
from api import deps
from core.classroom import (
    ClassroomAlreadyOpenError,
    ClassroomNotOpenError,
    ClassroomQRCodeInvaildError,
    ClassroomRecordDecodeError,
    appendClassroomAttendance,
    appendClassroomEnd,
    getClassroomAttendanceQRCode,
    getClassroomRecord,
    createClassroom,
    deleteClassroom,
    appendClassroomRoll,
    verifyClassroomAttendanceQRCode
)
from core.dynamic import (
    boardcastDynamicToLesson,
    sendDynamicToStudent,
    sendDynamicToTeacher
)
from crud.crud_lesson import lesson
from crud.crud_teacher import teacher
from crud.crud_task import task
from crud.crud_student import student
from crud.crud_lr import lessonRecord
from crud.crud_sts import studentTaskStatus
from crud.crud_class import class_
from crud.crud_option import option


lesson_router = r = APIRouter()


class LessonsReturn(BaseModel):
    lessons: List[schemas.LessonBrief]
    semester: dict


class LessonDetailReturn(BaseModel):
    lesson: schemas.Lesson
    teacher: schemas.Teacher


class LessonTaskReturn(BaseModel):
    tasks: List[schemas.Task]
    statuses: Optional[List[schemas.StudentTaskStatus]]


@r.get("", response_model=LessonsReturn)
async def getLessons(
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope == "teacher":
        ls = await lesson.getMultiByTeacherId(db, user.id)
    elif scope == "student":
        ls = await lesson.getMultiByClassId(db, user.class_id)
    else:
        raise HTTPException(status_code=403, detail="Forbidden")

    semester = await option.getSemester(db)
    return {"lessons": ls, "semester": semester}


@r.get("/{lesson_id}", response_model=LessonDetailReturn)
async def getLessonDetail(
    lesson_id: int,
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope == "teacher":
        hasLesson = await lesson.isTeacherHasLesson(db, user.id, lesson_id)
        if not hasLesson:
            raise HTTPException(
                status_code=403, detail="You are not the teacher of this lesson")
    elif scope == "student":
        hasLesson = await lesson.isClassHasLesson(db, user.class_id, lesson_id)
        if not hasLesson:
            raise HTTPException(
                status_code=403, detail="You are not the student of this lesson")
    else:
        raise HTTPException(status_code=403, detail="Forbidden")

    l = await lesson.get(db, lesson_id)
    t = await teacher.get(db, l.teacher_id)
    return {"lesson": l, "teacher": t}


@r.get("/{lesson_id}/task", response_model=LessonTaskReturn)
async def getLessonTask(
    lesson_id: int,
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope == "teacher":
        hasLesson = await lesson.isTeacherHasLesson(db, user.id, lesson_id)

        if not hasLesson:
            raise HTTPException(
                status_code=403, detail="You are not the teacher of this lesson")

        ts = await task.getMultiByLessonId(db, lesson_id)
        return {"tasks": ts}
    elif scope == "student":
        hasLesson = await lesson.isClassHasLesson(db, user.class_id, lesson_id)

        if not hasLesson:
            raise HTTPException(
                status_code=403, detail="You are not the student of this lesson")

        ts = await task.getMultiByLessonId(db, lesson_id)
        sts = await task.getMultiStatusByTaskIds(db, [t.id for t in ts], user.id)
        return {"tasks": ts, "statuses": sts}
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


@r.put("/{lesson_id}/task/{task_id}/status")
async def putTaskStatus(
    lesson_id: int,
    task_id: int,
    statusUpdate: schemas.StudentTaskStatusUpdate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "student" and not await lesson.isClassHasLesson(db, user.class_id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the student of this lesson")

    if not await studentTaskStatus.isStudentHasTaskStatus(db, user.id, task_id):
        raise HTTPException(
            status_code=403, detail="You don't have this task")

    ts = await studentTaskStatus.getByStudentIdAndTaskId(db, user.id, task_id)
    t = await task.get(db, task_id)
    if ts.status == "uncompleted":
        l = await lesson.get(db, lesson_id)
        await sendDynamicToTeacher(db, l.teacher_id, lesson_id, f"{user.name} 完成了任务 {t.title}，请老师及时批改。")

    if ts.status == "checked":
        raise HTTPException(
            status_code=403, detail="You cannot modify a checked task")

    if ts.status == "expired":
        raise HTTPException(
            status_code=403, detail="You cannot modify a checked task")

    await studentTaskStatus.update(
        db, db_obj=ts,
        obj_in={
            **statusUpdate.dict(),
            "status": "completed"
        }
    )


@r.put("/{lesson_id}/task/{task_id}")
async def putTask(
    lesson_id: int,
    task_id: int,
    taskUpdate: schemas.TaskUpdate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "teacher" and not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the teacher of this lesson")

    if not await task.isTeacherHasTask(db, user.id, task_id):
        raise HTTPException(
            status_code=403, detail="You don't have permission to edit this task")

    t = await task.update(db, db_obj=await task.get(db, task_id), obj_in=taskUpdate)
    if taskUpdate.deadline > int(time.time()):
        await studentTaskStatus.updateMultiExpiredToOtherByTaskId(db, task_id)
    await boardcastDynamicToLesson(db, lesson_id, f"任务 {t.title} 已更新，请及时完成。")


@r.put("/{lesson_id}/task/{task_id}/end")
async def putTaskStatusEnd(
    lesson_id: int,
    task_id: int,
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "teacher" and not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the teacher of this lesson")

    if not await task.isTeacherHasTask(db, user.id, task_id):
        raise HTTPException(
            status_code=403, detail="You don't have permission to edit this task")

    t = await task.get(db, task_id)
    await studentTaskStatus.updateMultiToExpiredByTaskId(db, task_id)
    await boardcastDynamicToLesson(db, lesson_id, f"任务 {t.title} 已被老师截止提交。")


@r.post("/{lesson_id}/task")
async def postTask(
    lesson_id: int,
    taskCreate: schemas.TaskCreate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "teacher" and not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the teacher of this lesson")

    t = await task.create(db, obj_in={
        **taskCreate.dict(),
        "lesson_id": lesson_id,
        "created_time": int(time.time())
    })
    class_ids = [theClass.id for theClass in await class_.getMultiByLessonId(db, lesson_id)]
    student_ids = []
    for class_id in class_ids:
        student_ids += [student.id for student in await student.getMultiByClassId(db, class_id)]
    await studentTaskStatus.insertMultiByStudentIdsAndTaskId(db, student_ids, t.id)
    await boardcastDynamicToLesson(db, lesson_id, f"老师布置了新任务 {t.title}，请及时完成。")


@r.delete("/{lesson_id}/task/{task_id}")
async def deleteTask(
    lesson_id: int,
    task_id: int,
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "teacher" and not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the teacher of this lesson")

    if not await task.isTeacherHasTask(db, user.id, task_id):
        raise HTTPException(
            status_code=403, detail="You don't have permission to delete this task")

    t = await task.get(db, task_id)
    if not t:
        raise HTTPException(
            status_code=404, detail="Task not found")

    await task.remove(db, id=task_id)
    await studentTaskStatus.deleteMultiByTaskId(db, task_id)
    await boardcastDynamicToLesson(db, lesson_id, f"老师删除了任务 {t.title} ，请及时确认。")


@r.get("/{lesson_id}/task/{task_id}/status-checking", response_model=List[schemas.StudentTaskStatus])
async def getTaskStatusChecking(
    lesson_id: int,
    task_id: int,
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "teacher" and not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the teacher of this lesson")

    if not await task.isTeacherHasTask(db, user.id, task_id):
        raise HTTPException(
            status_code=403, detail="You don't have permission to check this task")

    return await studentTaskStatus.getMultiByTaskId(db, task_id)


@r.put("/{lesson_id}/task/{task_id}/status-checking")
async def putTaskStatusChecking(
    lesson_id: int,
    task_id: int,
    student_id: str = Body(embed=True),
    score: int = Body(embed=True),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "teacher" and not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the teacher of this lesson")

    if not await task.isTeacherHasTask(db, user.id, task_id):
        raise HTTPException(
            status_code=403, detail="You don't have permission to check this task")

    t = await task.get(db, task_id)
    await studentTaskStatus.update(
        db, db_obj=await studentTaskStatus.getByStudentIdAndTaskId(db, student_id, task_id),
        obj_in={
            "score": score,
            "status": "checked"
        })
    await sendDynamicToStudent(
        db, student_id, lesson_id,
        f"{user.name} 完成了任务 {t.title} 的批改，你的成绩是 {score} ，请及时查看。"
    )


@r.put("/{lesson_id}/notice")
async def putNotice(
    lesson_id: int,
    notice: str = Body(embed=True),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "teacher" and not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the teacher of this lesson")

    await lesson.update(db, db_obj=await lesson.get(db, lesson_id), obj_in={"notice": notice})
    await boardcastDynamicToLesson(db, lesson_id, f"老师更新了课程公告。")


@r.put("/{lesson_id}/courseware")
async def putCourseware(
    lesson_id: int,
    courseware: str = Body(embed=True),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "teacher" and not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the teacher of this lesson")

    await lesson.update(db, db_obj=await lesson.get(db, lesson_id), obj_in={"courseware": courseware})
    await boardcastDynamicToLesson(db, lesson_id, f"老师更新了课程课件。")


@r.get("/{lesson_id}/classroom")
async def getClassroom(
    lesson_id: int,
    db=Depends(deps.getDB),
    redis: Redis = Depends(deps.getRedis),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope == "teacher" and not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the teacher of this lesson")
    elif scope == "student" and not await lesson.isClassHasLesson(db, user.class_id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the student of this lesson")

    try:
        classroom = await getClassroomRecord(redis, lesson_id)
    except ClassroomRecordDecodeError:
        await deleteClassroom(redis, lesson_id)
        raise HTTPException(
            status_code=400, detail="Classroom record is broken")

    if scope == "student":
        return {"classroom": classroom}
    elif scope == "teacher":
        try:
            qrcode = await getClassroomAttendanceQRCode(redis, lesson_id)
        except ClassroomNotOpenError:
            qrcode = None
        return {"classroom": classroom, "qrcode": qrcode}


@r.get("/{lesson_id}/classroom/pre-data")
async def getClassroomPreData(
    lesson_id: int,
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope == "teacher" and not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the teacher of this lesson")
    elif scope == "student" and not await lesson.isClassHasLesson(db, user.class_id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the student of this lesson")

    classes = await class_.getMultiByLessonId(db, lesson_id)
    students = []
    for c in classes:
        students += [
            schemas.Student.from_orm(student) for student in await student.getMultiByClassId(db, c.id)
        ]
    historys = await lessonRecord.getMultiByLessonId(db, lesson_id)
    return {"classes": classes, "students": students, "histories": historys}


@r.get("/{lesson_id}/classroom/history/{history_id}")
async def getClassroomHistory(
    lesson_id: int,
    history_id: int,
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope == "teacher" and not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the teacher of this lesson")
    elif scope == "student" and not await lesson.isClassHasLesson(db, user.class_id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the student of this lesson")

    h = await lessonRecord.get(db, id=history_id)
    if h.lesson_id != lesson_id:
        raise HTTPException(
            status_code=403, detail="This history is not belong to this lesson")

    return {"history": h}


@r.put("/{lesson_id}/classroom/classbegin")
async def putClassroomBegin(
    lesson_id: int,
    title: str = Body(embed=True),
    expiration: int = Body(embed=True),
    db=Depends(deps.getDB),
    redis: Redis = Depends(deps.getRedis),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "teacher" and not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the teacher of this lesson")

    try:
        await createClassroom(redis, lesson_id, title, expiration)
    except ClassroomAlreadyOpenError:
        raise HTTPException(
            status_code=400, detail="Classroom is already opened")
    await boardcastDynamicToLesson(db, lesson_id, f"老师开启了上课 {title} 。")


@r.put("/{lesson_id}/classroom/classend")
async def putClassroomEnd(
    lesson_id: int,
    db=Depends(deps.getDB),
    redis: Redis = Depends(deps.getRedis),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "teacher" and not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the teacher of this lesson")

    try:
        await appendClassroomEnd(redis, lesson_id)
        classroom = await getClassroomRecord(redis, lesson_id)
    except ClassroomNotOpenError:
        raise HTTPException(
            status_code=400, detail="Classroom is not opened")
    except ClassroomRecordDecodeError:
        await deleteClassroom(redis, lesson_id)
        raise HTTPException(
            status_code=400, detail="Classroom record is broken")
    await lessonRecord.create(db, obj_in={
        "lesson_id": lesson_id,
        "time": int(time.time()),
        "data": ujson.dumps(classroom)
    })
    await deleteClassroom(redis, lesson_id)
    await boardcastDynamicToLesson(db, lesson_id, f"老师结束了上课。")


@r.put("/{lesson_id}/classroom/attendance")
async def putClassroomAttendance(
    lesson_id: int,
    qrcode: str = Body(embed=True),
    db=Depends(deps.getDB),
    redis: Redis = Depends(deps.getRedis),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "student" and not await lesson.isClassHasLesson(db, user.class_id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the student of this lesson")

    try:
        await verifyClassroomAttendanceQRCode(redis, lesson_id, qrcode)
        await appendClassroomAttendance(redis, lesson_id, user.id, user.name)
    except ClassroomNotOpenError:
        raise HTTPException(
            status_code=400, detail="Classroom is not opened")
    except ClassroomQRCodeInvaildError:
        raise HTTPException(
            status_code=400, detail="Invalid QRCode")
    except ClassroomRecordDecodeError:
        await deleteClassroom(redis, lesson_id)
        raise HTTPException(
            status_code=400, detail="Classroom record is broken")


@r.get("/{lesson_id}/classroom/roll")
async def getClassroomRoll(
    lesson_id: int,
    count: int = 5,
    question: str = "",
    db=Depends(deps.getDB),
    redis: Redis = Depends(deps.getRedis),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "teacher" and not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the teacher of this lesson")

    students = await student.getRandomStudentsByLessonId(db, lesson_id, count)
    idAndNames = [{
        "student_id": student.id,
        "name": student.name,
    } for student in students]

    try:
        await appendClassroomRoll(redis, lesson_id, idAndNames, question)
    except ClassroomNotOpenError:
        raise HTTPException(
            status_code=400, detail="Classroom is not opened")
    except ClassroomRecordDecodeError:
        await deleteClassroom(redis, lesson_id)
        raise HTTPException(
            status_code=400, detail="Classroom record is broken")

    return {"students": idAndNames}
