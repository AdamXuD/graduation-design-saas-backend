from core.config import settings
from crud.crud_teacher import teacher
from crud.crud_student import student
from crud.crud_admin import admin
from core.security import ALGORITHM
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from db.redis import SessionRedis
from db.database import SessionDatabase
from db.oss import SessionOSS

reusableOauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def getDB():
    try:
        db = SessionDatabase()
        yield db
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        )
    finally:
        await db.close()


async def getRedis():
    try:
        r = SessionRedis()
        yield r
    finally:
        await r.close()


async def getOSS():
    async with SessionOSS() as oss:
        yield oss


class TokenPayload(BaseModel):
    username: str = None
    scope: str = None


def parseToken(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        tokenData = TokenPayload(**payload)
    except (ValidationError, jwt.PyJWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return tokenData


async def getCurrentUserAndScope(
    db: AsyncSession = Depends(getDB),
    token: str = Depends(reusableOauth2)
):
    tokenData = parseToken(token)
    if tokenData.scope == "student":
        user = await student.get(db, id=tokenData.username)
    elif tokenData.scope == "teacher":
        user = await teacher.get(db, id=tokenData.username)
    elif tokenData.scope == "admin":
        user = await admin.get(db, id=tokenData.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return [user, tokenData.scope]


async def isAdmin(token: str = Depends(reusableOauth2)):
    if parseToken(token).scope != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    return True
