from fastapi import APIRouter, HTTPException

from app.dependencies import HostServiceDep
from app.schemas.host_schema import HostDiscussionRecordsResponse, HostStateResponse

router = APIRouter(prefix="/api/host", tags=["主持人 Agent"])


@router.get("/start", response_model=HostStateResponse, description="开始主持人讨论接口")
async def start_host_endpoint(service: HostServiceDep):
    """GET /api/host/start 启动主持人讨论。"""
    try:
        service.start_host()
        return HostStateResponse(host_running=True)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/stop", response_model=HostStateResponse, description="停止主持人讨论接口")
async def stop_host_endpoint(service: HostServiceDep):
    """GET /api/host/stop 停止主持人讨论。"""
    try:
        service.stop_host()
        return HostStateResponse(host_running=False)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/discussion",
    response_model=HostDiscussionRecordsResponse,
    description=" 获取讨论区里收集到的发言记录",
)
def get_host_discussion_records_endpoint(service: HostServiceDep):
    """返回讨论区发言记录。"""
    try:
        discussion_records = service.get_discussion_records()
        return HostDiscussionRecordsResponse(**discussion_records)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
