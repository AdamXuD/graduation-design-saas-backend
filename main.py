
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from api import router
from fastapi import FastAPI
from core.config import settings
from db.init_db import initDB


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    on_startup=[initDB]
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin) for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)


# TODO 待测试
# 1. lesson公告系统的增删存在bug 是前端的问题
# 2. lesson课件全屏存在bug
# 3. 可发布
