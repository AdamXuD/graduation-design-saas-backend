from datetime import datetime, timedelta
import time
import random
import string
import jwt
from pydantic import ValidationError

from redis.asyncio import Redis
import ujson


class ClassroomRecordDecodeError(Exception):
    pass


class ClassroomAlreadyOpenError(Exception):
    pass


class ClassroomNotOpenError(Exception):
    pass


class ClassroomQRCodeInvaildError(Exception):
    pass


def _getRandomString(length: int = 4):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


async def createClassroom(redis: Redis, lesson_id: int, title: str, attendance_expiration: int):
    classroomStr = await redis.get(f"lesson:{lesson_id}:classroom:record")
    if classroomStr is not None:
        raise ClassroomAlreadyOpenError

    classroom = [{
        "type": "classbegin",
        "time": int(time.time()),
        "data": {
            "title": title,
            "attendance_expiration": int(time.time()) + attendance_expiration
        }
    }]
    await redis.set(
        f"lesson:{lesson_id}:classroom:record",
        ujson.dumps(classroom)
    )
    await redis.set(
        f"lesson:{lesson_id}:classroom:attendance_secret",
        _getRandomString(4)
    )
    await redis.set(
        f"lesson:{lesson_id}:classroom:attendance_expiration",
        int(time.time()) + attendance_expiration
    )
    return


async def deleteClassroom(redis: Redis, lesson_id: int):
    await redis.delete(f"lesson:{lesson_id}:classroom:record")
    await redis.delete(f"lesson:{lesson_id}:classroom:attendance_secret")
    await redis.delete(f"lesson:{lesson_id}:classroom:attendance_expiration")
    return


async def getClassroomRecord(redis: Redis, lesson_id: int) -> list:
    classroomStr = await redis.get(f"lesson:{lesson_id}:classroom:record")
    if classroomStr is None:
        return None

    try:
        classroom = ujson.loads(classroomStr)
    except ujson.JSONDecodeError:
        raise ClassroomRecordDecodeError

    return classroom


async def appendClassroomEnd(redis: Redis, lesson_id: int):
    classroom = await getClassroomRecord(redis, lesson_id)
    if classroom is None:
        raise ClassroomNotOpenError

    classroom.append({
        "type": "classend",
        "time": int(time.time()),
        "data": None
    })
    await redis.set(
        f"lesson:{lesson_id}:classroom:record",
        ujson.dumps(classroom)
    )
    return


async def appendClassroomAttendance(redis: Redis, lesson_id: int, student_id: int, student_name: str):
    classroom = await getClassroomRecord(redis, lesson_id)
    if classroom is None:
        raise ClassroomNotOpenError

    order = 1
    for item in classroom:
        if item["type"] != "attendance":
            continue
        if item["data"]["student"]["student_id"] == student_id:
            return
        order += 1

    classroom.append({
        "type": "attendance",
        "time": int(time.time()),
        "data": {
            "student": {
                "student_id": student_id,
                "name": student_name,
            },
            "order": order,
        }
    })
    await redis.set(
        f"lesson:{lesson_id}:classroom:record",
        ujson.dumps(classroom)
    )
    return


async def appendClassroomRoll(redis: Redis, lesson_id: int, idAndNames: list, question: str):
    classroom = await getClassroomRecord(redis, lesson_id)
    if classroom is None:
        raise ClassroomNotOpenError

    classroom.append({
        "type": "taketheroll",
        "time": int(time.time()),
        "data": {
            "students": idAndNames,
            "question": question
        }
    })
    await redis.set(
        f"lesson:{lesson_id}:classroom:record",
        ujson.dumps(classroom)
    )
    return


async def getClassroomAttendanceQRCode(redis: Redis, lesson_id: int, expiresDelta: int = 20):
    secret = await redis.get(f"lesson:{lesson_id}:classroom:attendance_secret")
    expiration = await redis.get(f"lesson:{lesson_id}:classroom:attendance_expiration")
    if secret is None or expiration is None:
        raise ClassroomNotOpenError

    if int(expiration) < int(time.time()):
        return None

    data = {"exp": datetime.utcnow() + timedelta(seconds=expiresDelta)}
    return jwt.encode(data, secret, algorithm="HS256")


async def verifyClassroomAttendanceQRCode(redis: Redis, lesson_id: int, qrcode: str):
    secret = await redis.get(f"lesson:{lesson_id}:classroom:attendance_secret")
    if secret is None:
        raise ClassroomNotOpenError

    try:
        jwt.decode(qrcode, secret, algorithms=["HS256"])
    except (ValidationError, jwt.PyJWTError):
        raise ClassroomQRCodeInvaildError
