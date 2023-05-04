
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


# TODO 待实现
# 1. 初始化部分中，需要将public桶中的权限开放给所有人
# 2. 需要写docker-compose文件，并尝试部署到洛杉矶服务器，测试延迟
# 3. 前端部署到cloudflare pages，并测试加载速度
