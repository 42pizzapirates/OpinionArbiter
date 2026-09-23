from fastapi import APIRouter, HTTPException

from app.dependencies import ResearchServiceDep
from app.schemas.research_schema import (
    ResearchRequest,
    ResearchResponse,
    ResearchResultsResponse,
)

router = APIRouter(prefix="/api/research", tags=["研究路由"])


@router.post("", response_model=ResearchResponse, description="开始研究接口")
async def start_research_endpoint(payload: ResearchRequest, service: ResearchServiceDep):
    """POST /api/research 启动研究工作流。"""
    try:
        return service.start_research(payload.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest", response_model=ResearchResultsResponse, description="获取研究结果接口")
def get_research_result_endpoint(service: ResearchServiceDep):
    """获取最新研究结果。"""
    try:
        research_result = service.get_research_result()
        return ResearchResultsResponse(results=research_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
