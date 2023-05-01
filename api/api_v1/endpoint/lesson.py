import json
import time
from redis.asyncio import Redis
from fastapi import APIRouter, Body, Depends, HTTPException

from api import deps
from core.classroom import ClassroomAlreadyOpenError, ClassroomNotOpenError, ClassroomQRCodeInvaildError, ClassroomRecordDecodeError, appendClassroomAttendance, appendClassroomEnd, getClassroomAttendanceQRCode, getClassroomRecord, createClassroom, deleteClassroom, appendClassroomRoll, verifyClassroomAttendanceQRCode
from core.dynamic import boardcastDynamicToLesson, sendDynamicToStudent, sendDynamicToTeacher
from crud.crud_lesson import lesson
from crud.crud_teacher import teacher
from crud.crud_task import task
from crud.crud_student import student
from crud.crud_lr import lessonRecord
from crud.crud_sts import studentTaskStatus
from crud.crud_class import theClass
from crud.crud_option import option
from schemas.lesson_record import LessonRecordCreate
from schemas.student_task_status import StudentTaskStatus, StudentTaskStatusUpdate
from schemas.task import Task, TaskCreate, TaskUpdate
from schemas.lesson import Lesson, LessonBrief
from schemas.teacher import Teacher


lesson_router = r = APIRouter()


@r.get("")
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
    return {"lessons": [LessonBrief.from_orm(l) for l in ls], "semester": semester}


@r.get("/{lesson_id}")
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
    return {"lesson": Lesson.from_orm(l), "teacher": Teacher.from_orm(t)}


@r.get("/{lesson_id}/task")
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
        return {"tasks": [Task.from_orm(t) for t in ts]}
    elif scope == "student":
        hasLesson = await lesson.isClassHasLesson(db, user.class_id, lesson_id)

        if not hasLesson:
            raise HTTPException(
                status_code=403, detail="You are not the student of this lesson")

        ts = await task.getMultiByLessonId(db, lesson_id)
        sts = await task.getMultiStatusByTaskIds(db, [t.id for t in ts], user.id)
        return {
            "tasks": [Task.from_orm(t) for t in ts],
            "status": [StudentTaskStatus.from_orm(st) for st in sts]
        }
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


@r.put("/{lesson_id}/task/{task_id}/status")
async def putTaskStatus(
    lesson_id: int,
    task_id: int,
    statusUpdate: StudentTaskStatusUpdate = Body(alias="status"),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "student" and not await lesson.isClassHasLesson(db, user.class_id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the student of this lesson")

    if await studentTaskStatus.isStudentHasTaskStatus(db, user.id, task_id):
        raise HTTPException(
            status_code=403, detail="You don't have this task")

    ts = await studentTaskStatus.getByStudentIdAndTaskId(db, user.id, task_id)
    t = await task.get(db, task_id)
    if ts.status == "uncompleted":
        l = await lesson.get(db, lesson_id)
        await sendDynamicToTeacher(db, l.teacher_id, f"{user.name} 完成了任务 {t.title}，请老师及时批改。")

    if ts.status == "checked":
        raise HTTPException(
            status_code=403, detail="You cannot modify a checked task")

    if t.deadline < time.time():
        await studentTaskStatus.update(
            db, db_obj=ts,
            obj_in={
                **statusUpdate.dict(),
                "status": "expired"
            }
        )
        raise HTTPException(
            status_code=403, detail="You cannot modify a task after deadline")

    await studentTaskStatus.update(
        db, db_obj=ts,
        obj_in={
            **statusUpdate.dict(),
            "status": "completed"
        }
    )

    return {"status": statusUpdate}


@r.put("/{lesson_id}/task/{task_id}")
async def putTask(
    lesson_id: int,
    task_id: int,
    taskUpdate: TaskUpdate = Body(alias="task"),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "teacher" and not await lesson.isTeacherHasLesson(db, user.id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You are not the teacher of this lesson")

    if await task.isTeacherHasTask(db, task_id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You don't have permission to edit this task")

    t = await task.get(db, task_id)
    await task.update(db, db_obj=t, obj_in=taskUpdate)
    await boardcastDynamicToLesson(db, lesson_id, f"任务 {t.title} 已更新，请及时完成。")


@r.post("/{lesson_id}/task")
async def postTask(
    lesson_id: int,
    taskCreate: TaskCreate = Body(alias="task"),
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
    class_ids = [theClass.id for theClass in await theClass.getMultiByLessonId(db, lesson_id)]
    student_ids = []
    for class_id in class_ids:
        student_ids += [student.id for student in await student.getMultiByClassId(db, class_id)]
    await studentTaskStatus.insertMultiByStudentIdsAndTaskId(db, student_ids, t.id)
    await boardcastDynamicToLesson(db, lesson_id, f"老师布置了新任务 {t.title}，请及时完成。")
    return {"task": t}


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

    if await task.isTeacherHasTask(db, task_id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You don't have permission to delete this task")

    t = await task.get(db, task_id)
    if not t:
        raise HTTPException(
            status_code=404, detail="Task not found")

    await task.remove(db, id=task_id)
    await studentTaskStatus.deleteMultiByTaskId(db, task_id)
    await boardcastDynamicToLesson(db, lesson_id, f"老师删除了任务 {t.title} ，请及时确认。")


@r.get("/{lesson_id}/task/{task_id}/status-checking")
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

    if await task.isTeacherHasTask(db, task_id, lesson_id):
        raise HTTPException(
            status_code=403, detail="You don't have permission to check this task")

    sts = await studentTaskStatus.getMultiByTaskId(db, task_id)
    return {"status": sts}


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
    await lessonRecord.create(db, obj_in=LessonRecordCreate(**{
        "lesson_id": lesson_id,
        "time": int(time.time()),
        "data": json.dumps(classroom)
    }))
    await deleteClassroom(redis, lesson_id)
    await boardcastDynamicToLesson(db, lesson_id, f"老师结束了上课。")
    return {"classroom": classroom}


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

    return


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
