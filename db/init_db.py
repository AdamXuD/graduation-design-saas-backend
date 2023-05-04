from db.oss import SessionOSS
from db.redis import SessionRedis
from models.admin import Admin
from models.class_ import Class
from models.class_lesson_relation import ClassLessonRelation
from models.cloud_share import CloudShare
from models.dynamic import Dynamic
from models.lesson_record import LessonRecord
from models.lesson import Lesson
from models.option import Option
from models.profession import Profession
from models.student_task_status import StudentTaskStatus
from models.student import Student
from models.task import Task
from models.teacher import Teacher

import ujson
from sqlalchemy.ext.asyncio import AsyncSession
from botocore.client import ClientError

import schemas
from models.base_class import Base
from db.database import SessionDatabase, engine
from crud.crud_admin import admin
from core.config import settings
from core import security


async def initDatabase(db: AsyncSession) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if not await admin.get(db, id=settings.FIRST_ADMIN_ID):
        obj = schemas.AdminCreate(
            id=settings.FIRST_ADMIN_ID,
            name="admin",
            phone="",
            email="",
            introduction="",
            avatar="",
        )
        await admin.create(db, obj_in={
            **obj.dict(),
            "hashed_password": security.getPasswordHash(settings.FIRST_ADMIN_PASSWORD),
        })


async def initOSS(oss: any):
    try:  # 若不存在则创建
        await oss.head_bucket(Bucket="public")
    except ClientError:
        await oss.create_bucket(Bucket="public")
        policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Sid": "AddPerm",
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": "arn:aws:s3:::public/*"
            }]
        }
        await oss.put_bucket_policy(Bucket="public", Policy=ujson.dumps(policy))

    try:  # 若不存在则创建
        await oss.head_bucket(Bucket="cloud")
    except ClientError:
        await oss.create_bucket(Bucket="cloud")


async def initDB():
    async with SessionDatabase() as db:
        await initDatabase(db)

    async with SessionOSS() as oss:
        await initOSS(oss)

    async with SessionRedis() as r:
        await r.ping()
