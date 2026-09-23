from typing import Any

from fastapi import APIRouter, HTTPException

from app.dependencies import ConfigServiceDep
from app.schemas.config_schema import ConfigResponse, ConfigUpdateRequest

router = APIRouter(prefix="/api/config", tags=["应用配置路由"])


@router.get("", response_model=ConfigResponse)
def get_config_endpoint(service: ConfigServiceDep):
    """GET /api/config 返回当前应用配置。"""
    try:
        config: dict[str, Any] = service.read_config_info()
        return ConfigResponse(config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=ConfigResponse)
def get_config_endpoint(request: ConfigUpdateRequest, service: ConfigServiceDep):
    """POST /api/config 更新并返回最新配置。"""
    new_config_infos = service.update_config_info(request.root)
    return ConfigResponse(config=new_config_infos.model_dump(mode="json"))
