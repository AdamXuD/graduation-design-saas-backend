from api import router
from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)


# TODO 待测试
# 1. 重构后的oss模块(已完成)
# 2. 动态模块(已完成)
# 3. 已完成的管理模块(已完成)

# TODO 待完成
# 1. 一切增删改查的异常处理（涉及外键）

# FIXME 待修复
# 1. 前端管理端各个表格在搜索栏变化是，页数不会复位为1(已完成)
# 2. Task界面刷新403(已完成)
