from crud.crud_teacher import teacher
from crud.crud_student import student
from crud.crud_admin import admin
from core.security import ALGORITHM, SECRET_KEY
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from db.redis import SessionRedis
from db.session import SessionLocal
from db.oss import SessionOSS
# from models.student import

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"/auth/login"
)


async def getDB():
    try:
        db = SessionLocal()
        yield db
    finally:
        await db.close()


async def getRedis():
    try:
        r = SessionRedis()
        yield r
    finally:
        await r.close()


async def getOSS():
    return SessionOSS()


class TokenPayload(BaseModel):
    username: str = None
    scope: str = None


async def getCurrentUserAndScope(
    db: AsyncSession = Depends(getDB),
    token: str = Depends(reusable_oauth2)
):
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        tokenData = TokenPayload(**payload)
    except (ValidationError, jwt.PyJWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    if tokenData.scope == "student":
        user = await student.get(db, id=tokenData.username)
    elif tokenData.scope == "teacher":
        user = await teacher.get(db, id=tokenData.username)
    elif tokenData.scope == "admin":
        user = await admin.get(db, id=tokenData.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return [user, tokenData.scope]
