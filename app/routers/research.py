from fastapi import APIRouter, HTTPException
from app.schemas.research_schema import ResearchRequest, ResearchResponse, ResearchResultsResponse
from app.dependencies import ResearchServiceDep

router = APIRouter(prefix="/api/research", tags=["研究路由"])


@router.post("", response_model=ResearchResponse, description="开始研究接口")
async def start_research_endpoint(payload: ResearchRequest, service: ResearchServiceDep):
    try:
        return service.start_research(payload.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest", response_model=ResearchResultsResponse, description="获取研究结果接口")
def get_research_result_endpoint(service: ResearchServiceDep):
    try:
        research_result = service.get_research_result()
        return ResearchResultsResponse(results=research_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
