from typing import List, Optional, Generic, TypeVar
from pydantic.generics import GenericModel
from fastapi import APIRouter, Body, Depends, HTTPException, Query

import schemas
from api import deps
from core import security

from crud.crud_teacher import teacher
from crud.crud_student import student
from crud.crud_profession import profession
from crud.crud_class import class_
from crud.crud_option import option
from crud.crud_lesson import lesson
from crud.crud_clr import classLessonRelation


admin_router = r = APIRouter(dependencies=[Depends(deps.isAdmin)])


DataT = TypeVar("DataT")


class PaginatedData(GenericModel, Generic[DataT]):
    data: List[DataT]
    total: int


@r.get("/option/list", response_model=List[schemas.Option])
async def getOption(
    db=Depends(deps.getDB)
):
    return await option.getOptions(db)


@r.put("/option/{key}")
async def putOption(
    key: str,
    optionUpdate: schemas.OptionUpdate = Body(),
    db=Depends(deps.getDB),
):
    if o := await option.getByKey(db, key=key):
        await option.update(db, db_obj=o, obj_in={"value": optionUpdate.value})
    else:
        await option.create(db, obj_in={"key": key, "value": optionUpdate.value})


@r.get("/profession/list", response_model=PaginatedData[schemas.Profession])
async def getProfessionList(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=5, le=50),
    keyword: Optional[str] = Query(None, max_length=20),
    db=Depends(deps.getDB),
):
    ps, total = await profession.getPaginatedMultiByOptionalKeyword(db, keyword, (page - 1) * page_size, page_size)
    return {"data": ps, "total": total}


@r.post("/profession")
async def postProfession(
    professionCreate: schemas.ProfessionCreate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    await profession.create(db, obj_in=professionCreate)


@r.put("/profession/{id}")
async def putProfession(
    id: str,
    professionUpdate: schemas.ProfessionUpdate = Body(),
    db=Depends(deps.getDB),
):
    await profession.update(db, db_obj=await profession.get(db, id=id), obj_in=professionUpdate)


@r.delete("/profession/{id}")
async def deleteProfession(
    id: str,
    db=Depends(deps.getDB),
):
    await profession.remove(db, id=id)


@r.get("/teacher/list", response_model=PaginatedData[schemas.Teacher])
async def getTeacherList(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=5, le=50),
    keyword: Optional[str] = Query(None, max_length=20),
    db=Depends(deps.getDB),
):
    ts, total = await teacher.getMultiByOptionalKeyword(db, keyword, (page - 1) * page_size, page_size)
    return {"data": ts, "total": total}


@r.post("/teacher")
async def postTeacher(
    teacherCreate: schemas.TeacherCreate = Body(),
    db=Depends(deps.getDB),
):
    await teacher.create(db, obj_in={
        **teacherCreate.dict(),
        "hashed_password": security.getPasswordHash(teacherCreate.id),
    })


@r.put("/teacher/{id}")
async def putTeacher(
    id: str,
    teacherUpdate: schemas.TeacherUpdate = Body(),
    db=Depends(deps.getDB),
    currentUser=Depends(deps.getCurrentUserAndScope),
):
    await teacher.update(db, db_obj=await teacher.get(db, id=id), obj_in={
        **teacherUpdate.dict(exclude={"reset_password"}),
        "hashed_password": security.getPasswordHash(id),
    } if teacherUpdate.reset_password else teacherUpdate.dict(exclude={"reset_password"}))


@r.delete("/teacher/{id}")
async def deleteTeacher(
    id: str,
    db=Depends(deps.getDB),
):
    await teacher.remove(db, id=id)


@r.get("/student/list", response_model=PaginatedData[schemas.Student])
async def getStudentList(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=5, le=50),
    keyword: Optional[str] = Query(None, max_length=20),
    db=Depends(deps.getDB),
):
    ts, total = await student.getMultiByOptionalKeyword(db, keyword, (page - 1) * page_size, page_size)
    return {"data": ts, "total": total}


@r.post("/student")
async def postStudent(
    studentCreate: schemas.StudentCreate = Body(),
    db=Depends(deps.getDB),
):
    await student.create(db, obj_in={
        **studentCreate.dict(),
        "hashed_password": security.getPasswordHash(studentCreate.id),
    })


@r.put("/student/{id}")
async def putStudent(
    id: str,
    studentUpdate: schemas.StudentUpdate = Body(),
    db=Depends(deps.getDB),
):
    await student.update(db, db_obj=await student.get(db, id=id), obj_in={
        **studentUpdate.dict(exclude={"reset_password"}),
        "hashed_password": security.getPasswordHash(id),
    } if studentUpdate.reset_password else studentUpdate.dict(exclude={"reset_password"}))


@r.delete("/student/{id}")
async def deleteStudent(
    id: str,
    db=Depends(deps.getDB),
):
    await student.remove(db, id=id)


@r.get("/class/list", response_model=PaginatedData[schemas.Class])
async def getClassList(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=5, le=50),
    keyword: Optional[str] = Query(None, max_length=20),
    db=Depends(deps.getDB),
):
    cs, total = await class_.getMultiByOptionalKeyword(
        db, keyword, (page - 1) * page_size, page_size)

    return {"data": cs, "total": total}


@r.post("/class")
async def postClass(
    classCreate: schemas.ClassCreate = Body(),
    db=Depends(deps.getDB),
):
    await class_.create(db, obj_in=classCreate)


@r.put("/class/{id}")
async def putClass(
    id: str,
    classUpdate: schemas.ClassUpdate = Body(),
    db=Depends(deps.getDB),
):
    await class_.update(db, db_obj=await class_.get(db, id=id), obj_in=classUpdate)


@r.delete("/class/{id}")
async def deleteClass(
    id: str,
    db=Depends(deps.getDB),
):
    await class_.remove(db, id=id)


@r.get("/lesson/list", response_model=PaginatedData[schemas.Lesson])
async def getLessonList(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=5, le=50),
    keyword: Optional[str] = Query(None, max_length=20),
    db=Depends(deps.getDB),
):
    ls, total = await lesson.getMultiByOptionalKeyword(
        db, keyword, (page - 1) * page_size, page_size)

    return {"data": ls, "total": total}


@r.post("/lesson")
async def postLesson(
    lessonCreate: schemas.LessonCreate = Body(),
    db=Depends(deps.getDB),
):
    await lesson.create(db, obj_in=lessonCreate)


@r.put("/lesson/{id}")
async def putLesson(
    id: str,
    lessonUpdate: schemas.LessonUpdate = Body(),
    db=Depends(deps.getDB),
):
    await lesson.update(db, db_obj=await lesson.get(db, id=id), obj_in=lessonUpdate)


@r.delete("/lesson/{id}")
async def deleteLesson(
    id: str,
    db=Depends(deps.getDB),
):
    await lesson.remove(db, id=id)


@r.get("/lesson/{lesson_id}/class/list", response_model=List[schemas.Class])
async def getLessonClassList(
    lesson_id: str,
    db=Depends(deps.getDB),
):
    return await class_.getMultiByLessonId(db, lesson_id)


@r.put("/lesson/{lesson_id}/class")
async def putLessonClass(
    lesson_id: str,
    class_ids: List[int],
    db=Depends(deps.getDB),
):
    await classLessonRelation.updateLessonClasses(db, lesson_id, class_ids)
