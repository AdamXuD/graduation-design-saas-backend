import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

from core.config import settings

pwdContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def getPasswordHash(password: str) -> str:
    return pwdContext.hash(password)


def verifyPassword(plainPassword: str, hashedPassword: str) -> bool:
    return pwdContext.verify(plainPassword, hashedPassword)


def createAccessToken(*, data: dict, expiresDelta: timedelta = None):
    toEncode = data.copy()
    if expiresDelta:
        expire = datetime.utcnow() + expiresDelta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    toEncode.update({"exp": expire})
    encodedJwt = jwt.encode(toEncode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encodedJwt
