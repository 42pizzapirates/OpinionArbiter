from typing import Any

from pydantic import BaseModel, Field, RootModel, field_validator


class ConfigUpdateRequest(RootModel[dict[str, Any]]):
    """应用配置更新请求体。"""

    @field_validator("root")
    @classmethod
    def not_empty(cls, v: dict[str, Any]) -> dict[str, Any]:
        """校验配置更新请求体非空。"""
        if not v:
            raise ValueError("请求体不能为空")
        return v


class ConfigResponse(BaseModel):
    """应用配置查询响应体。"""

    config: dict[str, Any] = Field(default_factory=dict, description="当前配置")
