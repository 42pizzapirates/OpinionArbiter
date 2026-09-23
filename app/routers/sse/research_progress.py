"""SSE 实时事件流路由。"""

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from app.dependencies import get_sse_broadcaster

router = APIRouter(tags=["events"])


@router.get("/api/events/stream")
async def stream_research_progress(request: Request):
    """推送研究进度 SSE 事件流。"""
    return EventSourceResponse(
        get_sse_broadcaster().stream_research_progress(request),
        ping=15,
        headers={"X-Accel-Buffering": "no"},
    )
