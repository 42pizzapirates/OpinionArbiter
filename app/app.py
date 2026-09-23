from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import get_lifecycle_service
from app.routers.rest import config, host, report, research
from app.routers.sse import research_progress


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启停时注册与关闭生命周期协调器。"""
    lifecycle_service = get_lifecycle_service()
    try:
        lifecycle_service.register()
        yield    # 处理请求
    finally:
        lifecycle_service.shutdown()


app = FastAPI(description="舆情应用的FastAPI实例", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(config.router)

app.include_router(host.router)
app.include_router(research.router)
app.include_router(report.router)

app.include_router(research_progress.router)
