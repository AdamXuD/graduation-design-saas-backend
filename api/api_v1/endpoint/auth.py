from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from api import deps
from core import security
from core.config import settings
from crud.crud_admin import admin
from crud.crud_student import student
from crud.crud_teacher import teacher


auth_router = r = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str


@r.post("/login", response_model=Token)
async def login(db=Depends(deps.getDB), formData: OAuth2PasswordRequestForm = Depends()):
    role = formData.scopes.pop()
    username = formData.username
    if role == "student":
        user = await student.authenticate(db, formData.username, formData.password)
    elif role == "teacher":
        user = await teacher.authenticate(db, formData.username, formData.password)
    elif role == "admin":
        user = await admin.authenticate(db, formData.username, formData.password)
    else:
        user = None
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    accessTokenExpires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    accessToken = security.createAccessToken(
        data={"username": username, "scope": role},
        expiresDelta=accessTokenExpires,
    )
    return {"access_token": accessToken, "token_type": "bearer"}
