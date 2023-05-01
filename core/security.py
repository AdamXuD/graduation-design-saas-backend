import jwt
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta

oauth2Scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

pwdContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

# TODO
SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 240


def getPasswordHash(password: str) -> str:
    return pwdContext.hash(password)


def verifyPassword(plainPassword: str, hashedPassword: str) -> bool:
    return pwdContext.verify(plainPassword, hashedPassword)


def createAccessToken(*, data: dict, expiresDelta: timedelta = None):
    toEncode = data.copy()
    if expiresDelta:
        expire = datetime.utcnow() + expiresDelta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    toEncode.update({"exp": expire})
    encodedJwt = jwt.encode(toEncode, SECRET_KEY, algorithm=ALGORITHM)
    return encodedJwt
