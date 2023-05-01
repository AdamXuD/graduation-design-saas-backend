from typing import Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query

from api import deps
from core import security
from crud.crud_teacher import teacher
from crud.crud_student import student
from crud.crud_profession import profession
from crud.crud_class import theClass
from crud.crud_option import option
from crud.crud_lesson import lesson
from schemas.option import OptionUpdate
from schemas.the_class import ClassCreate, ClassUpdate
from schemas.lesson import LessonCreate, LessonUpdate
from schemas.profession import ProfessionCreate, ProfessionUpdate
from schemas.student import StudentCreate, StudentUpdate
from schemas.teacher import Teacher, TeacherCreate,  TeacherUpdate

admin_router = r = APIRouter()


@r.get("/option")
async def getOption(
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    options = await option.getOptions(db)

    return {option.key: option.value for option in options}


@r.put("/option/{key}")
async def putOption(
    key: str,
    optionUpdate: OptionUpdate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    o = await option.getByKey(db, key=key)
    if o:
        await option.update(db, db_obj=o, obj_in={"value": optionUpdate.value})
    else:
        await option.create(db, obj_in={"key": key, "value": optionUpdate.value})


@r.get("/profession/list")
async def getProfessionList(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=5, le=50),
    keyword: Optional[str] = Query(None, max_length=20),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    ps, total = await profession.getPaginatedMultiByOptionalKeyword(db, keyword, (page - 1) * page_size, page_size)

    return {"professions": ps, "total": total}


@r.post("/profession")
async def postProfession(
    professionCreate: ProfessionCreate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    await profession.create(db, obj_in=professionCreate)


@r.put("/profession/{id}")
async def putProfession(
    id: str,
    professionUpdate: ProfessionUpdate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    p = await profession.update(db, db_obj=await profession.get(db, id=id), obj_in=professionUpdate)


@r.delete("/profession/{id}")
async def deleteProfession(
    id: str,
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    await profession.remove(db, id=id)


@r.get("/teacher/list")
async def getTeacherList(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=5, le=50),
    keyword: Optional[str] = Query(None, max_length=20),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    ts, total = await teacher.getMultiByOptionalKeyword(db, keyword, (page - 1) * page_size, page_size)

    return {"teachers": [Teacher.from_orm(t) for t in ts], "total": total}


@r.post("/teacher")
async def postTeacher(
    teacherCreate: TeacherCreate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    await teacher.create(db, obj_in={
        **teacherCreate.dict(),
        "hashed_password": security.getPasswordHash(teacherCreate.id),
    })


@r.put("/teacher/{id}")
async def putTeacher(
    id: str,
    teacherUpdate: TeacherUpdate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    await teacher.update(db, db_obj=await teacher.get(db, id=id), obj_in={
        **teacherUpdate.dict(exclude={"reset_password"}),
        "hashed_password": security.getPasswordHash(id),
    } if teacherUpdate.reset_password else teacherUpdate.dict(exclude={"reset_password"}))


@r.delete("/teacher/{id}")
async def deleteTeacher(
    id: str,
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser
    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    await teacher.remove(db, id=id)


@r.get("/student/list")
async def getStudentList(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=5, le=50),
    keyword: Optional[str] = Query(None, max_length=20),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    ts, total = await student.getMultiByOptionalKeyword(db, keyword, (page - 1) * page_size, page_size)

    return {"students": ts, "total": total}


@r.post("/student")
async def postStudent(
    studentCreate: StudentCreate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    await student.create(db, obj_in={
        **studentCreate.dict(),
        "hashed_password": security.getPasswordHash(studentCreate.id),
    })


@r.put("/student/{id}")
async def putStudent(
    id: str,
    studentUpdate: StudentUpdate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    await student.update(db, db_obj=await student.get(db, id=id), obj_in={
        **studentUpdate.dict(exclude={"reset_password"}),
        "hashed_password": security.getPasswordHash(id),
    } if studentUpdate.reset_password else studentUpdate.dict(exclude={"reset_password"}))


@r.delete("/student/{id}")
async def deleteStudent(
    id: str,
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser
    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    await student.remove(db, id=id)


@r.get("/class/list")
async def getClassList(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=5, le=50),
    keyword: Optional[str] = Query(None, max_length=20),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    cs, total = await theClass.getMultiByOptionalKeyword(
        db, keyword, (page - 1) * page_size, page_size)

    return {"classes": cs, "total": total}


@r.post("/class")
async def postClass(
    classCreate: ClassCreate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    await theClass.create(db, obj_in=classCreate)


@r.put("/class/{id}")
async def putClass(
    id: str,
    classUpdate: ClassUpdate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    p = await theClass.update(db, db_obj=await theClass.get(db, id=id), obj_in=classUpdate)


@r.delete("/class/{id}")
async def deleteClass(
    id: str,
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    await theClass.remove(db, id=id)


@r.get("/lesson/list")
async def getLessonList(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=5, le=50),
    keyword: Optional[str] = Query(None, max_length=20),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    ls, total = await lesson.getMultiByOptionalKeyword(
        db, keyword, (page - 1) * page_size, page_size)

    return {"lessons": ls, "total": total}


@r.post("/lesson")
async def postLesson(
    lessonCreate: LessonCreate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    await lesson.create(db, obj_in=lessonCreate)


@r.put("/lesson/{id}")
async def putLesson(
    id: str,
    lessonUpdate: LessonUpdate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    p = await lesson.update(db, db_obj=await lesson.get(db, id=id), obj_in=lessonUpdate)


@r.delete("/lesson/{id}")
async def deleteLesson(
    id: str,
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    user, scope = currentUser

    if scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    await lesson.remove(db, id=id)
