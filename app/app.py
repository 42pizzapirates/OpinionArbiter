from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.routers import config


# 定义lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # 初始化资源动作
        yield  # FASTAPI处理路由
    finally:
        # 应用关闭的时候，清理资源
        pass


app = FastAPI(description="舆情应用的FastAPI实例", lifespan=lifespan)

# app配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由

app.include_router(config.router)
